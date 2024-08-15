# Jam Pal

## What?
This project is meant to help ~you~ me get learning to play a new song (I play bass BTW) as quickly and smoothly as possible.
It integrates with Reaper, my DAW of choice, and allows you to:
1. Search for a song.
2. Download it from YouTube (using yt-dlp).
3. Create a new project based on a given template.
4. Set the BPM of the project to match the song.
5. Break it into stems (instruments) using Spotify's awesome `basic-pitch` project.
6. Import the stems into the project.

As an extra, it will also:
1. Detect the notes played and save them as MIDI file. (WIP)
2. Convert the MIDI file to a text file, representing the notes as ASCII tablature.

## Why?
Why not?
Seriously though, it saves me some time while learning to play a new song, which makes it much easier to just start playing. Of course, I'm not trying to rely on it, instead using it for songs that are difficult to transcribe by hearing (for example if the drums are too loud in the mix).


## Installation
```sh 
pip install -r requirements.txt
```

## Usage
```sh 
# To interactively search for a song
python main.py 

# You can also supply a youtube video URL 
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```
