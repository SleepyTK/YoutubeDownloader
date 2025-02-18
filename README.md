# YouTube Downloader

<img src="images/YoutubeDownloaderv1.0.3.png" width="885" alt="Youtube Downloader v1.0.3">

## Features
- Download videos/audio from YouTube
- Built-in search functionality
- Auto-updates
- No FFmpeg setup required (bundled with the app)
- supports 2Mbps, 3Mbps, 4Mbps, 5Mbps, 6Mbps, 10Mbps bitrates
- Supports 360p, 480p, 720p, 1080p video resolutions

## Installation
1. Download latest release from [Releases page](https://github.com/SleepyTK/YoutubeDownloader/releases)
2. Double-click `YouTube_Downloader.exe`

## Requirements
- Windows 10/11

## Legal
This software bundles FFmpeg binaries licensed under [LGPL v2.1](src/ffmpeg/LICENSE.txt).

## Support
For issues, [open a GitHub ticket](https://github.com/SleepyTK/YoutubeDownloader/issues).

## Notes
- This program is constantly in development and may contain bugs.
- The EXE might get flagged by antivirus software (e.g., McAfee) due to the nature of video downloads. If this happens, you may need to adjust your antivirus settings temporarily while the program is being certified.

## Currently Working on
- Adding video thumbnails and duration to video cards in the application interface on both the search frame and link frame

## Running the Python Code (Requires Python 3.10 or Higher)

If you'd like to run the Python version of the application instead of downloading the EXE, follow these steps:

1. **Clone the repository**  
   Clone this repository to your local machine using the following command:
   `git clone https://github.com/SleepyTK/YoutubeDownloader.git`

2. **Download FFmpeg**  
    Download FFmpeg from [this link](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z).  
    After downloading, extract the files and move `ffmpeg.exe` and `ffprobe.exe` into the `src/ffmpeg` folder of your project.

3. **Create a Virtual Environment**  
    In the root folder of the project, create a virtual environment by running:
    `python -m venv venv`

4. **Activate the Virtual Environment**  
    Activate the virtual environment by running:
    `venv\Scripts\Activate`

5. **Install Dependencies**  
    Install the required dependencies by running:
    `pip install -r src/requirements.txt`

6. **Run the Program**  
    Finally, run the program using:
    `python src/main.py`


# YouTube Downloader 🎥

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
![FFmpeg Required](https://img.shields.io/badge/FFmpeg-Required-orange.svg)

**A production-grade YouTube downloader blending intuitive design with robust technical implementation**

<img src="images/YoutubeDownloaderv1.0.3.png" width="885" alt="Youtube Downloader Interface Preview">

## Project Overview

### Purpose & Value Proposition
A dual-purpose application that:
- **For End Users**: Provides a simple yet powerful tool to download YouTube content in multiple formats
- **For Developers**: Demonstrates modern Python architecture with:
  - Hardware-accelerated video encoding
  - Auto-update system
  - Production-ready packaging
- **For Recruiters**: Showcases skills in:
  - GUI development (CustomTkinter)
  - Concurrent programming
  - CI/CD pipeline implementation

### Key Features
| User Experience | Technical Merit |
|-----------------|-----------------|
| 🔍 In-app YouTube search | ⚡ GPU-accelerated encoding (NVENC/AMF/QSV) |
| 🎨 Dark mode UI with thumbnails | 🧵 ThreadPoolExecutor for background tasks |
| 📥 Batch download queue | 🔄 GitHub API integration for auto-updates |
| 🛠️ One-click EXE installer | 🔒 Sanitized filename handling |

### Technology Stack
**Core Components**:
- `yt-dlp`: YouTube content extraction
- `FFmpeg`: Media processing/encoding
- `CustomTkinter`: Modern GUI framework
- `requests`: Update system/thumbnail fetching

**Key Implementations**:
- Version comparison (`packaging.version`)
- Subprocess management (`subprocess`)
- Image processing (`PIL`)
- Cross-thread communication (`queue`)

### Target Audience
| User Type | Value Received |
|-----------|----------------|
| Casual Users | Simple content downloading |
| Developers | Reference implementation of:<br>- Hardware acceleration<br>- Auto-updating apps<br>- Production packaging |
| Recruiters | Evidence of:<br>- Full project lifecycle management<br>- Technical decision making<br>- Production debugging skills |
## Table of Contents
- 🚀 [Features](#-features)
- 📥 [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [Technical Deep Dive](#-technical-deep-dive)
- [Development Setup](#-development-setup)
- 🗺️ [Roadmap](#-roadmap)
- [License](#-license)

---

## 🚀 Features

### User-Facing
🔍 **Smart Search** - Find videos directly in-app  
🔄 **Auto-Update** - Get latest features automatically  
🎨 **Modern GUI** - Dark theme with thumbnail previews  
📥 **Batch Downloads** - Queue multiple videos at once

### Technical Highlights
⚡ **Hardware Acceleration** - NVIDIA/AMD/Intel GPU support  
🧵 **Multi-Threading** - Background processing for smooth UI  
🔒 **Safe Filenames** - Automatic path sanitization  
📦 **EXE Packaging** - Single-file distribution

---

## 📥 Installation

### For End Users
1. Download latest `YouTube_Downloader.exe` from [Releases](https://github.com/SleepyTK/YoutubeDownloader/releases)
2. Double-click to run (no admin rights needed)

### For Developers
```bash
# 1. Clone repository
git clone https://github.com/SleepyTK/YoutubeDownloader.git
cd YoutubeDownloader

# 2. Set up Python environment
python -m venv venv  # Create virtual environment

# Activate environment
venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# If pip install fails:
python -m pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# 4. Set up FFmpeg
# Download ffmpeg.exe and ffprobe.exe from:
# https://www.gyan.dev/ffmpeg/builds/
# Place both files in: src/ffmpeg/

# 5. Verify setup
python src/main.py  # Should launch the application
```

## 🗺️ Roadmap

- Playlist support
- video player
- music player
- improved UI

## License
