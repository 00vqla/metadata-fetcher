# py-genius-tag

A python tool to fetch and embed metadata from Genius.com to mp3 files

## Quick Start

```bash
pip install -r requirements.txt

# for drag n drop
pip install tkinterdnd2

# gui usage
python genius_lyrics_gui.py
```

Or, for CLI usage:

```bash
python metadata_fetcher.py <path-to-mp3-or-folder>
```

## Requirements

- Python 3.7+
- `requests`
- `mutagen`
- `tkinterdnd2` (for drag-and-drop)

## Usage

### GUI

```
python genius_lyrics_gui_tkinter.py
```

### CLI

```bash
python metadata_fetcher.py "/path/to/song.mp3"
python metadata_fetcher.py "/path/to/music/folder"
python metadata_fetcher.py "/path/to/folder" --force
python metadata_fetcher.py "/path/to/folder" --delay 2.0
```

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

## Screenshots

<p align="center">
  <table>
    <tr>
      <td align="center">
        <img src="screenshots/image.png" alt="Metadata Fetcher UI" width="250"/><br>
        <em>App UI</em>
      </td>
      <td align="center">
        <img src="screenshots/image 2.png" alt="Lyrics in Music Player" width="250"/><br>
        <em>Lyrics in Music Player</em>
      </td>
    </tr>
  </table>
</p>
