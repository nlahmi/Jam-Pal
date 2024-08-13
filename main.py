import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from pprint import pp
from urllib.parse import parse_qs, urlparse

import demucs.separate
import inquirer
import librosa
import reapy
from reapy import reascript_api as RPR
from unidecode import unidecode
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic
from basic_pitch.inference import predict_and_save

logger = logging.getLogger(__name__)

DEBUG = sys.gettrace() is not None

template_file = Path("project_template.RPP")
recordings_base_path = Path("/home/noam/projects/Recordings/")


def download_song(url: str, save_path: Path) -> Path:
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "highest",
            }
        ],
        "outtmpl": {
            "default": str(
                (save_path / "%(uploader)s - %(title)s [%(id)s].%(ext)s").absolute()
            )
        },
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            url,
            download=True,
        )
        file_path = ydl.prepare_filename(info)

        return Path(file_path).with_suffix(".mp3")


def start_reaper(project_file: str | None = None):
    args = ["reaper"]
    if project_file:
        args.append(project_file)

    subprocess.Popen(args, start_new_session=True)


# Create new project
def create_project(project_name: str, launch: bool = True) -> Path:
    project_base_path = recordings_base_path / project_name
    project_file = project_base_path / f"{project_name}.RPP"

    # If dir already exists,also don't copy the template file
    try:
        os.mkdir(project_base_path)
        shutil.copyfile(template_file, project_file)
    except FileExistsError:
        print("Dir already exists")

    # Open reaper with out project in a detached process
    if launch:
        start_reaper(project_file)
    # sleep(10)

    return project_base_path


# Separate tracks
def separate_tracks(song_path: Path, model="htdemucs_6s") -> Path:
    # model = "mkx_extra"
    # temp_base_path = "separated"
    base_path = song_path.parent
    stems_path = base_path / model / song_path.stem

    demucs.separate.main(
        [
            "--mp3",
            "-n",
            model,
            "-o",
            str(base_path.absolute()),
            str(song_path.absolute()),
        ]
    )

    return stems_path


def yt_vid_to_url(vid: str) -> str:
    return f"https://youtube.com/watch?v={vid}"


def yt_url_to_vid(url: str) -> str:
    return parse_qs(urlparse(url).query).get("v")[0]


def search_song(query: str = None, url_given: bool = False) -> dict:
    # If not supplied, ask interactively
    query = query or inquirer.text("Search for a song")

    # Search for a song
    yt = YTMusic()
    # NOTE: For some reason, limit doesn't really work, instead returning 20 items as the default (which is fine by me honestly)
    results = yt.search(query, filter="songs", limit=10)

    # Multiple results, ask!
    if len(results) > 1:
        # Ask the user for the correct song
        choices = [
            f"{i} | {r['artists'][0]['name']} - {r['title']} | {r['album']['name']} | {r['duration']}"
            for i, r in enumerate(results)
        ]
        question = inquirer.List(
            "song", message="Choose the correct song", choices=choices
        )
        answers = inquirer.prompt([question])

        # Parse the result and return full data about it
        chosen_result_index = int(answers["song"].split(" | ")[0])
        result = results[chosen_result_index]

    # A single result, choose it
    elif len(results) == 1:
        result = results[0]

        # TODO: Make this a logging print
        print(
            f"Only a single option, choosing it: {result['artists'][0]['name']} - {result['title']} | {result['album']['name']} | {result['duration']}"
        )

    # No results but URL given, supply values manually
    elif url_given:
        print("No search results found, please input song details manualy.")

        questions = [
            inquirer.Text(name="title", message="Song Name"),
            inquirer.Text(name="artist", message="Artist Name"),
        ]
        result = inquirer.prompt(questions)

        # Query is probably the video_id
        result["video_id"] = query
        result["video_url"] = yt_vid_to_url(query)

        # We return here bc the last return statement expects the 'result' object to be structured differently
        return result

    # No results at all and no Video URL
    else:
        print("Error, no search results found and no URL was provided.")
        return

    return {
        # "album": result["album"]["name"],
        "artist": result["artists"][0]["name"],
        "title": result["title"],
        "video_id": result["videoId"],
        "video_url": yt_vid_to_url(result["videoId"]),
    }


def handle_input() -> dict:
    query = " ".join(sys.argv[1:])
    is_url = False

    # Handle Youtube URLs
    if query.startswith("https"):
        query = yt_url_to_vid(query)
        is_url = True

    result = search_song(query=query, url_given=is_url)
    pp(result)
    return result


def slugify(original: str) -> str:
    return unidecode(original).lower().replace(" ", "_")


def generate_project_name(song_details: dict, ask: bool = True) -> str:
    # Calculate the name from the song title and artist
    project_name = f"{slugify(song_details['artist'])}-{slugify(song_details['title'])}"

    # Confirm with the user and allow changes
    if ask:
        question = inquirer.Text(
            name="project_name", message="Confirm Project Name", default=project_name
        )
        project_name = inquirer.prompt([question])["project_name"]

    # Return the final project name as string
    return project_name


def detect_bpm(song_path: Path) -> int:
    # Load the audio file
    y, sr = librosa.load(str(song_path.absolute()))

    # Use librosa's tempo detection function to estimate the BPM
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    return int(tempo[0].round())


def insert_media(
    project: reapy.Project,
    media_path: Path,
    track_index: int = 0,
    insertion_point: float = 0.0,
    new_track: bool = True,
):
    # Create a new track with the name being the filename (without suffix)
    if new_track:
        track = project.add_track(index=track_index, name=media_path.stem)

    # Selecting an existing track
    else:
        track = project.tracks()[track_index]

    # Setting the focus on the track
    # BUG: doesn't really work for the purposes of adding a media item
    track.select()

    # NOTE: We could save the position, insert there then restore it,
    # then the parent function would set to 0 if needed, but whatever - this works

    # Make sure we insert at the 0 position (or the point specified)
    project.cursor_position = insertion_point

    # Insert the media into the 0-index track (512 does that, apparantly - though 0 would just be the selected track)
    RPR.InsertMedia(str(media_path.absolute()), 0)


def insert_stems_as_tracks(project: reapy.Project, stems_path: Path):
    for file in stems_path.iterdir():
        insert_media(project=project, media_path=file)


def transcribe_stem(stems_path: Path, instrument: str = "bass"):
    from basic_pitch import ICASSP_2022_MODEL_PATH

    # Pretty self-explanatory..
    instrument_filepath = str((stems_path / instrument).with_suffix(".mp3").absolute())
    predict_and_save(
        audio_path_list=[instrument_filepath],
        output_directory=str(stems_path.absolute()),
        save_midi=True,
        sonify_midi=False,
        save_model_outputs=False,
        save_notes=False,
        model_or_model_path=ICASSP_2022_MODEL_PATH,
    )

    # Return the final path of the MIDI file
    return stems_path / f"{instrument}_basic_pitch.mid"


def midi_to_tab(midi_path: Path, instrument: str = "bass"):
    import pretty_midi
    from tuttut.logic.tab import Tab
    from tuttut.logic.theory import Tuning

    weights = {"b": 1, "height": 1, "length": 1, "n_changed_strings": 1}
    f = pretty_midi.PrettyMIDI(midi_path.as_posix())

    # TODO: Handle different instruments (guitar)
    tuning = Tuning(["G2", "D2", "A1", "E1"])

    tab = Tab(
        midi_path.stem,
        tuning,
        f,
        weights=weights,
        output_dir=str(midi_path.parent.absolute()),
    )
    tab.to_ascii()

    # TODO: Return the final path of the txt file and open it (in the main fucntion)
    return 


def init():
    # Setup logging
    level = logging.DEBUG if DEBUG else logging.INFO
    format = (
        "[%(levelname)s] - %(name)s - %(message)s - %(pathname)s:%(lineno)d"
        if DEBUG
        else "[%(levelname)s] %(message)s"
    )

    logging.basicConfig(level=logging.INFO, format=format)
    logger.setLevel(level)

    # Init reaper
    try:
        reapy.configure_reaper()
    except RuntimeError:
        logger.error(
            "Reaper was not running. Please run this script again once it starts properly (launching in the background)"
        )
        start_reaper()
        exit(1)


def main():
    # Init Reaper with reapy (only needs to be done once, then restart reaper)
    init()

    # Handle user input (argv or interactively) and generate a name for the project
    song_details = handle_input()
    project_name = generate_project_name(song_details)

    # Create the project from template and launch it with Reaper
    project_path = create_project(project_name)

    # Download the song
    song_path = download_song(song_details["video_url"], project_path)

    # Detect BPM
    song_bpm = detect_bpm(song_path)

    # Seperate stems
    stems_path = separate_tracks(song_path)

    # Set the project's BPM
    project = reapy.Project()
    project.bpm = song_bpm

    # Insert Stems to session
    insert_stems_as_tracks(project=project, stems_path=stems_path)

    # Transcribe
    midi_path = transcribe_stem(stems_path=stems_path, instrument="bass")

    # Convert MIDI to Tabs
    midi_to_tab(midi_path)


def main_test():
    init()

    song_details = search_song("aLGQTKtbkbg")
    project_name = generate_project_name(song_details, ask=False)

    project_path = create_project(project_name)

    song_path = Path(
        "/home/noam/projects/Recordings/twenty_one_pilots-paladin_strait/twenty one pilots - Paladin Strait [aLGQTKtbkbg].mp3"
    )

    stems_path = Path(
        "/home/noam/projects/Recordings/twenty_one_pilots-paladin_strait/htdemucs_6s/twenty one pilots - Paladin Strait [aLGQTKtbkbg]/"
    )

    song_bpm = detect_bpm(song_path)

    # Set the project's BPM
    project = reapy.Project()
    project.bpm = song_bpm

    # Insert Stems to session
    # insert_stems_as_tracks(project=project, stems_path=stems_path)

    # Transcribe
    midi_path = transcribe_stem(stems_path=stems_path, instrument="bass")

    # Convert MIDI to Tabs
    midi_to_tab(midi_path)

    print("")


if __name__ == "__main__":
    if DEBUG:
        main_test()
    else:
        main()

print("Done!")

## Get a song name, spotify link, or youtube link
## Create a Reaper project with reathon
## Download the song via yt-dlp
## Get the BPM of the song - either locally or via some online database
## Separate instruments using demucs
## Start it and.. profit(?)
## Not yet, still need to add tracks to reaper (setting BPM first)

# Extra1: Do a bass2midi detection
# Extra2: Do a midi2tabs conversion
# Extra3: Chords Overlay (markers?)
# Extra4: Lyrics - https://github.com/johnwmillr/LyricsGenius/tree/master
