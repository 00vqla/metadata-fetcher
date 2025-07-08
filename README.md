# Metadata Fetcher

A python tool to fetch and embed metadata from Genius.com to mp3 files

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# (Optional) For drag-and-drop support
pip install tkinterdnd2

# Run the GUI
python3 genius_lyrics_gui_tkinter.py
```

Or, for CLI usage:

```bash
python3 metadata_fetcher.py <path-to-mp3-or-folder>
```

---

## Requirements

- Python 3.7+
- `requests`
- `mutagen`
- `tkinterdnd2` (for drag-and-drop)

---

## Usage

### Method 1: GUI (Recommended)

- Select a file or folder, set your options, and click **Start**!

### Method 2: Command-Line

```bash
python3 metadata_fetcher.py "/path/to/song.mp3"
python3 metadata_fetcher.py "/path/to/music/folder"
python3 metadata_fetcher.py "/path/to/folder" --force
python3 metadata_fetcher.py "/path/to/folder" --delay 2.0
```

---

## How It Works

1. **Batch Processing:** Process entire folders of MP3 files at once.
2. **Lyrics Extraction:** Fetch lyrics from Genius.com and embed them in MP3 tags.
3. **Metadata Update:** Only lyrics and year are updated; other tags are preserved.
4. **Multi-threaded:** Speed up processing with parallel threads.
5. **Section Formatting:** Option to keep or remove [Chorus], [Verse], etc.

---

## Output Format

Lyrics are embedded in the MP3 file's ID3 tags. You can view them in most music players that support lyrics display.

---

## Configuration

- **Thread Count:** Set how many files to process in parallel (GUI only).
- **Delay:** Set a delay between requests to avoid being blocked by Genius.com.
- **Section Headers:** Choose whether to keep or remove [Chorus], [Verse], etc.

---

## Example Output

```
Found 3 MP3 file(s):
1. song1.mp3
2. song2.mp3
3. song3.mp3

==================================================
Processing: song1.mp3
==================================================

1. Fetching lyrics from Genius.com...
2. Embedding lyrics and year...
✅ Success! Updated: song1.mp3
```

---

## Troubleshooting

- If lyrics are not found, try cleaning up the song title or artist metadata.
- For drag-and-drop, ensure `tkinterdnd2` is installed.
- If you see a security warning on macOS, right-click the app and choose **Open** the first time.

---

## License

This project is open source and available under the MIT License.

---

## Screenshots

<p align="center">
  <table>
    <tr>
      <td align="center">
        <img src="image.png" alt="Metadata Fetcher UI" width="250"/><br>
        <em>App UI</em>
      </td>
      <td align="center">
        <img src="image 2.png" alt="Lyrics in Music Player" width="250"/><br>
        <em>Lyrics in Music Player</em>
      </td>
    </tr>
  </table>
</p>