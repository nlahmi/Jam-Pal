import os
import shutil
import subprocess
import sys
from pathlib import Path
from pprint import pp
from urllib.parse import parse_qs, urlparse

import demucs.separate

from unidecode import unidecode
import inquirer
import reapy
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

# snake_case - author-song_name
# project_name = "author-test"
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

        return Path(file_path)
        # out = ydl.download([url])
        # print(out)


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
        subprocess.Popen(["reaper", project_file], start_new_session=True)
    # sleep(10)

    return project_base_path


# Separate tracks
def separate_tracks(song_path: Path, model = "htdemucs_6s") -> Path:
    # model = "mkx_extra"
    # temp_base_path = "separated"
    base_path = song_path.parent
    stems_path = base_path / model / song_path.stem

    demucs.separate.main(["--mp3", "-n", model, "-o", str(base_path.absolute()), str(song_path.absolute())])

    return stems_path


def init():
    reapy.configure_reaper()


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


def main():
    init()
    # pp(search_song("FVdjZYfDuLE"))

    song_details = search_song("aLGQTKtbkbg")
    project_name = generate_project_name(song_details, ask=False)

    # song_details = handle_input()
    # project_name = generate_project_name(song_details)

    project_path = create_project(project_name)

    # song_path = download_song(song_details["video_url"], project_path)
    song_path = Path("/home/noam/projects/Recordings/twenty_one_pilots-paladin_strait/twenty one pilots - Paladin Strait [aLGQTKtbkbg].mp3")

    # not urgent: detect BPM

    stems_path = separate_tracks(song_path)

    # insert tracks to session

    print("")


if __name__ == "__main__":
    main()

print("Done!")

## Get a song name, spotify link, or youtube link
## Create a Reaper project with reathon
## Download the song via yt-dlp
# Get the BPM of the song - either locally or via some online database
## Separate instruments using demucs
## Start it and.. profit(?)
# Not yet, still need to add tracks to reaper (setting BPM first)

# Extra1: Do a bass2midi detection
# Extra2: Do a midi2tabs conversion
# Extra3: Chords Overlay (markers?)
# Extra4: Lyrics - https://github.com/johnwmillr/LyricsGenius/tree/master
