import demucs.separate
from reathon.nodes import Project, Node, Path, Track, Item
# import shlex

model = "mkx_extra"
temp_base_path = "separated"
file_path = "test.mp3"

# Separate tracks
# demucs.separate.main(["--mp3", "-n", model, file_path])

project = Project(Track(), Track(), Track())
project.write("test.rpp")


print("done!")

# Get a song name, spotify link, or youtube link
# Download the song via yt-dlp
# Get the BPM of the song - either locally or via some online database
# Separate instruments using demucs
# Create a Reaper project with reathon and include the files and tempo
# Start it and.. profit(?)

# Extra: Do a bass2midi detection
# Extra2: Do a midi2tabs conversion
