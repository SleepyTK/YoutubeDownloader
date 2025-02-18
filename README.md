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
  - GUI development (CustomTkinter)

### Key Features
| User Experience | Technical Merit |
|-----------------|-----------------|
| 🔍 In-app YouTube search | ⚡ GPU-accelerated encoding (NVENC/AMF/QSV) |
| 🎨 Dark Themed UI | 🧵 ThreadPoolExecutor for background tasks |
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

## Table of Contents
- 📥 [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [Technical Deep Dive](#-technical-deep-dive)
- [Development Setup](#-development-setup)
- 🗺️ [Roadmap](#-roadmap)
- [License](#-license)

---

## 📥 Installation

### For End Users
🚀 **Quick Start**  
1. Download the latest `YouTube_Downloader.exe` from my [Releases page](https://github.com/SleepyTK/YoutubeDownloader/releases)
2. Double-click the executable to launch  
   *No additional dependencies required*

> **Note**: Windows may show a security warning - this is normal for unsigned executables. Click "More info" then "Run anyway".

---

### For Developers
**System Requirements**  
- Python 3.10+ (64-bit)
- Windows 10/11 (Linux support planned)

**Setup Process**:

```bash
# 1. Clone repository
git clone https://github.com/SleepyTK/YoutubeDownloader.git
cd YoutubeDownloader

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux (when support is available)

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure FFmpeg
# Download from: https://www.gyan.dev/ffmpeg/builds/
# Place these files in project:
#   - src/ffmpeg/ffmpeg.exe
#   - src/ffmpeg/ffprobe.exe

# 5. Verify installation
python src/main.py
```


## 🖥️ Usage Guide

### Basic Workflow
1. **Select Save Location**  
   - Click <img src="images/select_dir_button.png" width="200" alt="Directory selection button">
   - Select folder in dialog  
   - Confirmation appears in left panel

2. **Add Content**    
   - **Method 1**: Paste URL in input field → Click <img src="images/add_link_button.png" width="200" alt="URL input section"> or press Enter  
   - **Method 2**: Use built-in search:  
     1. Type query in right-side search bar  
     2. Press Enter  
     3. Click "ADD" on desired results  

3. **Configure Settings**  
   <img src="images/settings_dropdowns.png" width="200" alt="Configuration options">  
   - **Resolution**: Dropdown (1080p, 720p, 480p, 360p)  
   - **Bitrate**: Dropdown (10Mbps to 2Mbps)  
   - **Encoder**: Auto-populated based on detected GPU  

4. **Start Download**  
   <img src="images/download_buttons.png" width="200" alt="Download buttons">  
   - **Video**: Click "DOWNLOAD VIDEO" for MP4  
   - **Audio**: Click "DOWNLOAD AUDIO" for MP3  

### Interface Breakdown
| UI Element | Purpose | Code Reference |
|------------|---------|----------------|
| <img src="images/progress_bar.png" width="200"> | Shows current file progress | `CTkProgressBar` |
| <img src="images/search_results.png" width="200"> | Displays YouTube search results with thumbnails | `CTkScrollableFrame` |
| <img src="images/queue_panel.png" width="200"> | Lists queued URLs with remove buttons | `CTkScrollableFrame` |

### Settings Explained
**Resolution Options**  
```python
# From __init__():
self.resolution_menu = CTkOptionMenu(
    values=["1080p", "720p", "480p", "360p"]
)
```

## 🗺️ Roadmap

- Playlist support
- video player
- music player
- improved UI

## License
This software bundles FFmpeg binaries licensed under [LGPL v2.1](src/ffmpeg/LICENSE.txt).



## Support
For issues, [open a GitHub ticket](https://github.com/SleepyTK/YoutubeDownloader/issues).