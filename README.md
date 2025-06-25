# Metadata Fetcher

**Metadata Fetcher™** by **vq vault** is a powerful, user-friendly batch tool for fetching and embedding lyrics and metadata into your MP3 files. It features a modern drag-and-drop GUI for macOS, multi-threaded processing, and robust Genius.com integration.

## Features

- 🎵 **Batch Processing:** Process entire folders of MP3 files at once.
- 🔍 **Lyrics Extraction:** Fetch lyrics from Genius.com and embed them in MP3 tags.
- 🏷️ **Metadata Enhancement:** Update year, lyrics, and more—while preserving your original title.
- ⚡ **Multi-threaded:** Speed up processing with parallel threads.
- 🖱️ **Drag-and-Drop:** Easily select files or folders.
- 🖥️ **Modern GUI:** Clean, resizable interface with progress and logs.
- 🛡️ **Respectful Crawling:** Built-in delays to avoid rate-limiting.
- 📝 **Section Formatting:** Option to keep or remove [Chorus], [Verse], etc.

## Installation

1. **Install Python 3.7+** (macOS comes with Python, but you may want to update it).
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   - For drag-and-drop support:
     ```bash
     pip install tkinterdnd2
     ```

3. **(Optional) Build as a macOS .app:**
   - See instructions below.

## Usage

### Run the GUI

```bash
python genius_lyrics_gui_tkinter.py
```

- Select a file or folder, set your options, and click **Start**!

### Build a macOS .app

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build the app:
   ```bash
   pyinstaller --windowed --onefile --name "Metadata Fetcher" genius_lyrics_gui_tkinter.py
   ```
3. The `.app` will be in the `dist/` folder.

## Configuration

- **Thread Count:** Set how many files to process in parallel.
- **Delay:** Set a delay between requests to avoid being blocked by Genius.com.
- **Section Headers:** Choose whether to keep or remove [Chorus], [Verse], etc.

## Requirements

- Python 3.7+
- `requests`
- `mutagen`
- `tkinterdnd2` (for drag-and-drop)

## License

© 2024 vq vault. All rights reserved.™

## Contributing

Pull requests and issues are welcome! 