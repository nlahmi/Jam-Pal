from pathlib import Path
import os
import shutil
import subprocess
from time import sleep

import demucs.separate
import reapy

# import shlex

# snake_case - author-song_name
project_name = "author-test"
template_file = Path("project_template.RPP")


# Create new project
def create_project():
    recordings_base_path = Path("/home/noam/projects/Recordings/")
    project_base_path = recordings_base_path / project_name
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


def main():
    pass


if __name__ == "__main__":
    init()
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
