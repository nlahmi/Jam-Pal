from pprint import pp
import sys
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs
# from time import sleep

import inquirer
import demucs.separate
import reapy
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

# import shlex

# snake_case - author-song_name
project_name = "author-test"
template_file = Path("project_template.RPP")
recordings_base_path = Path("/home/noam/projects/Recordings/")
project_base_path = recordings_base_path / project_name


def download_song(url: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "highest",
            }
        ],
        "outtmpl": {"default": "ST_%(upload_date)s_%(title).50s.mp3"},
    }
    with YoutubeDL(ydl_opts) as ydl:
        out = ydl.download([url])
        print(out)


# Create new project
def create_project():
    project_file = project_base_path / f"{project_name}.RPP"

    # If dir already exists, also don't copy the template file
    try:
        os.mkdir(project_base_path)
        shutil.copyfile(template_file, project_file)
    except FileExistsError:
        print("Dir already exists")

    # Open reaper with out project in a detached process
    subprocess.Popen(["reaper", project_file], start_new_session=True)
    # sleep(10)


# Separate tracks
def separate_tracks():
    model = "mkx_extra"
    temp_base_path = "separated"
    file_path = "test.mp3"
    demucs.separate.main(["--mp3", "-n", model, file_path])


def reapy_test():
    project = reapy.Project()
    # reapy.print("yay")


def init():
    reapy.configure_reaper()


def yt_vid_to_url(vid: str) -> str:
    return f"https://youtube.com/watch?v={vid}"


def yt_url_to_vid(url: str) -> str:
    return parse_qs(urlparse(url).query).get("v")[0]


def search_song(query: str = None) -> dict:
    # If not supplied, ask interactively
    query = query or inquirer.text("Search for a song")

    # Search for a song
    yt = YTMusic()
    results = yt.search(query, filter="songs", limit=10)

    # Ask the user for the correct song
    choices = [
        f"{i} | {r['artists'][0]['name']} - {r['title']} | {r['album']['name']} | {r['duration']}"
        for i, r in enumerate(results)
    ]
    question = inquirer.List(
        "song", message="Choose the correct song:", choices=choices
    )
    answers = inquirer.prompt([question])

    # Parse the result and return full data about it
    chosen_result_index = int(answers["song"].split(" | ")[0])
    chosen_result = results[chosen_result_index]

    # print(chosen_result)
    return chosen_result


# def get_info_from_vid(vid: str) -> dict:
#     return YTMusic().get_song(vid)


def handle_input(arg: str = "") -> dict:
    # Handle Youtube URLs
    if arg.startswith("https"):
        vid = yt_url_to_vid(arg)
        # url = arg

        # result = get_info_from_vid(vid)

    # If it can't be parsed as a URL, treat it as a query (even if empty)
    else:
        query = arg
        result = search_song(query)

    pp(result)
    # TODO: Normalize the two options - URL, Song name and Artist


def main():
    # init()
    # handle_input("https://www.youtube.com/watch?v=FVdjZYfDuLE")
    # handle_input(sys.argv[-1])

    # search_song()

    print("")
    # ytmdl.


if __name__ == "__main__":
    main()

print("done!")

# Get a song name, spotify link, or youtube link
# Download the song via yt-dlp
# Get the BPM of the song - either locally or via some online database
# Separate instruments using demucs
# Create a Reaper project with reathon and include the files and tempo
# Start it and.. profit(?)

# Extra1: Do a bass2midi detection
# Extra2: Do a midi2tabs conversion
# Extra3: Chords Overlay (markers?)
# Extra4: Lyrics
