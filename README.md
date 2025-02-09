# YouTube Downloader

<img src="images/YoutubeDownloaderv1.0.2.png" width="885" alt="Youtube Downloader v1.0.2">

## Features
- Download videos/audio from YouTube
- Built-in search functionality
- Auto-updates
- No FFmpeg setup required
- 2Mbps, 3Mbps, 4Mbps, 5Mbps, 6Mbps, 10Mbps
- 360p, 480p, 720p, 1080p

## Installation
1. Download latest release from [Releases page]
2. Double-click `YouTube_Downloader.exe`

## Updating
The app will automatically prompt you when updates are available.

## Requirements
- Windows 10/11
- No FFmpeg installation needed

## Legal
This software bundles FFmpeg binaries licensed under [LGPL v2.1](src/ffmpeg/LICENSE.txt).

## Support
For issues, [open a GitHub ticket](https://github.com/SleepyTK/YoutubeDownloader/issues).

## Notes
- This program is constantly in development and will have bugs.
- the exe might get blocked by antivirus scanners like McAfee, so you will have to tinker a bit until I get the program certified

## Currently Working on
- adding video thumbnail and length added to the video cards


## If you want to run the python code instead of downloading the exe (python installation 3.10 or higher required)
1. Clone the repository
2. Download ffmpeg from [ffmpeg](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z) and move ffmpeg.exe & ffprobe.exe into the 'src/ffmpeg' folder
3. make a virtual environment in the root folder by running this command in your root: "python -m venv venv"
4. Start the virtual environment by running this command in your root: "venv/Scripts/Activate"
5. install all the dependencies by running this command in your root: "pip install -r scr/requirements.txt"
6. try running the program by running this command in your root: "python src/main.py"