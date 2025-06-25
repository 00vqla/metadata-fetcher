#!/usr/bin/env python3
"""
Genius Lyrics Fetcher
A batch processor for fetching lyrics and metadata from Genius.com

Based on the MP3Tag script by Bugzero
"""

import os
import re
import json
import requests
import argparse
from pathlib import Path
from urllib.parse import quote
import time
from mutagen import File
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCOM, TPE2, USLT, TXXX
from mutagen.mp3 import MP3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeniusLyricsFetcher:
    def __init__(self, delay=1.0, user_agent=None, keep_sections=True):
        self.delay = delay
        self.keep_sections = keep_sections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def clean_text_for_url(self, text):
        """Clean text for URL generation (similar to the MP3Tag script)"""
        # Remove special characters and replace spaces with hyphens
        cleaned = re.sub(r'[^\w\s-]', '', text.lower())
        cleaned = re.sub(r'[-\s]+', '-', cleaned)
        return cleaned.strip('-')
    
    def generate_genius_url(self, artist, title):
        """Generate Genius.com URL from artist and title"""
        artist_clean = self.clean_text_for_url(artist)
        title_clean = self.clean_text_for_url(title)
        return f"https://genius.com/{artist_clean}-{title_clean}-lyrics"
    
    def extract_json_from_html(self, html_content):
        """Extract JSON data from Genius.com HTML page"""
        try:
            # Look for the specific pattern that contains the JSON
            start_marker = 'window.__PRELOADED_STATE__ = JSON.parse(\''
            end_marker = '\');'
            
            start_pos = html_content.find(start_marker)
            if start_pos == -1:
                logger.warning("Could not find __PRELOADED_STATE__ in HTML")
                return None
            
            # Extract the JSON string
            json_start = start_pos + len(start_marker)
            json_end = html_content.find(end_marker, json_start)
            if json_end == -1:
                logger.warning("Could not find end of __PRELOADED_STATE__")
                return None
            
            json_str = html_content[json_start:json_end]
            
            if not json_str:
                logger.warning("Could not extract JSON content")
                return None
            
            # Clean the JSON string - this is the key step that makes it work!
            def clean_json_string(s):
                # Replace common escape sequences
                s = s.replace('\\"', '"')
                s = s.replace("\\'", "'")
                s = s.replace('\\$', '$')
                s = s.replace('\\\\n', '\\n')
                s = s.replace('\\\\t', '\\t')
                s = s.replace('\\\\r', '\\r')
                s = s.replace('\\\\/', '/')  # Fix forward slashes
                s = s.replace('\\\\', '\\')  # Fix double backslashes
                return s
            
            cleaned_json = clean_json_string(json_str)
            
            # Parse the cleaned JSON
            return json.loads(cleaned_json)
            
        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            return None
    
    def fix_json_string(self, json_str):
        """Attempt to fix common JSON string issues"""
        try:
            # Remove any HTML comments that might be embedded
            json_str = re.sub(r'<!--.*?-->', '', json_str, flags=re.DOTALL)
            
            # Fix unescaped quotes in the middle of strings
            # This is a simplified fix - in practice, this is complex
            json_str = re.sub(r'(?<!\\)"(?=.*":)', '\\"', json_str)
            
            # Remove any trailing commas before closing braces/brackets
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            return json_str
        except Exception:
            return json_str
    
    def extract_metadata_from_json(self, json_data):
        """Extract metadata from the JSON data"""
        try:
            song_page = json_data.get('songPage', {})
            entities = json_data.get('entities', {})
            
            # Extract basic song info
            song_id = song_page.get('song')
            
            # Extract lyrics - new format has lyricsData.body.html
            lyrics_data = song_page.get('lyricsData', {})
            lyrics_html = lyrics_data.get('body', {}).get('html', '')
            
            # Clean lyrics HTML
            lyrics_text = self.clean_lyrics_html(lyrics_html, self.keep_sections)
            
            # Extract tracking data
            tracking_data = song_page.get('trackingData', [])
            metadata = {}
            
            for item in tracking_data:
                key = item.get('key')
                value = item.get('value')
                if key and value:
                    metadata[key] = value
            
            # Extract additional info from entities
            if song_id and 'songs' in entities:
                song_info = entities['songs'].get(str(song_id), {})
                metadata.update({
                    'primaryArtistNames': song_info.get('primaryArtistNames', ''),
                    'artistNames': song_info.get('artistNames', ''),
                    'producerArtists': song_info.get('writerArtists', []),  # Changed from producerArtists
                    'featuredArtists': song_info.get('featuredArtists', [])
                })
            
            return {
                'lyrics': lyrics_text,
                'title': metadata.get('Title', ''),
                'artist': metadata.get('Primary Artist', ''),
                'album': metadata.get('Primary Album', ''),
                'release_date': metadata.get('Release Date', ''),  # Full date like "2022-07-02"
                'primary_artist': metadata.get('primaryArtistNames', ''),
                'all_artists': metadata.get('artistNames', ''),
                'producers': metadata.get('producerArtists', []),
                'featured': metadata.get('featuredArtists', [])
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return None
    
    def clean_lyrics_html(self, html_content, keep_sections=True):
        """Clean HTML from lyrics content and preserve section formatting as specified. Optionally remove section headers."""
        if not html_content:
            return ""
        # 1. Convert 2+ <br> to double newline (section break)
        text = re.sub(r'(<br\s*/?>\s*){2,}', '\n\n', html_content, flags=re.IGNORECASE)
        # 2. Remove single <br> (do NOT make a new line)
        text = re.sub(r'<br\s*/?>', '', text, flags=re.IGNORECASE)
        # 3. Convert <p> to double newlines (paragraphs)
        text = re.sub(r'</?p>', '\n\n', text, flags=re.IGNORECASE)
        # 4. Remove all other HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # 5. Decode HTML entities
        text = text.replace('&quot;', '"')
        text = text.replace('&#x27;', "'")
        text = text.replace('&#39;', "'")
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        # 6. Remove trailing spaces on each line
        text = '\n'.join(line.rstrip() for line in text.splitlines())
        # 7. Collapse 3+ newlines to just 2 (single blank line between sections)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 8. Remove leading/trailing blank lines
        text = text.strip('\n')
        # 9. Optionally remove section headers like [Chorus], [Verse], etc.
        if not keep_sections:
            text = re.sub(r'^\s*\[[^\]]+\]\s*$', '', text, flags=re.MULTILINE)
            # Remove extra blank lines left by section header removal
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.strip('\n')
        return text
    
    def fetch_lyrics_and_metadata(self, artist, title):
        """Fetch lyrics and metadata from Genius.com"""
        try:
            url = self.generate_genius_url(artist, title)
            logger.info(f"Fetching: {url}")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            # Debug: Save HTML for inspection if needed
            if logger.isEnabledFor(logging.DEBUG):
                with open(f"debug_{artist}_{title}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                logger.debug(f"Saved HTML to debug_{artist}_{title}.html")
            
            # Extract JSON from HTML
            json_data = self.extract_json_from_html(response.text)
            if not json_data:
                logger.warning(f"Could not extract JSON data from {url}")
                return None
            
            # Extract metadata
            metadata = self.extract_metadata_from_json(json_data)
            if not metadata:
                logger.warning(f"Could not extract metadata from JSON for {artist} - {title}")
                return None
            
            # Add delay to be respectful to Genius.com
            time.sleep(self.delay)
            
            return metadata
            
        except requests.RequestException as e:
            logger.error(f"Request error for {artist} - {title}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching data for {artist} - {title}: {e}")
            return None
    
    def get_mp3_metadata(self, file_path):
        """Get existing metadata from MP3 file"""
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            
            tags = audio.tags
            
            return {
                'title': str(tags.get('TIT2', [''])[0]) if 'TIT2' in tags else '',
                'artist': str(tags.get('TPE1', [''])[0]) if 'TPE1' in tags else '',
                'album': str(tags.get('TALB', [''])[0]) if 'TALB' in tags else '',
                'year': str(tags.get('TDRC', [''])[0]) if 'TDRC' in tags else '',
            }
        except Exception as e:
            logger.error(f"Error reading MP3 metadata from {file_path}: {e}")
            return None
    
    def update_mp3_metadata(self, file_path, metadata):
        """Update MP3 file with new metadata (only lyrics and year)"""
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            
            tags = audio.tags
            
            # Only update year (release date)
            if metadata.get('release_date'):
                tags['TDRC'] = TDRC(encoding=3, text=metadata['release_date'])
            
            # Only update lyrics
            if metadata.get('lyrics'):
                tags['USLT::eng'] = USLT(encoding=3, lang='eng', desc='', text=metadata['lyrics'])
            
            # Do NOT update title, artist, album, composers, or featured artists
            
            # Save the file
            audio.save()
            return True
            
        except Exception as e:
            logger.error(f"Error updating MP3 metadata for {file_path}: {e}")
            return False
    
    def process_file(self, file_path, force_update=False):
        """Process a single MP3 file"""
        try:
            # Get existing metadata
            existing_metadata = self.get_mp3_metadata(file_path)
            if not existing_metadata:
                logger.warning(f"Could not read metadata from {file_path}")
                return False
            artist = existing_metadata.get('artist', '')
            title = existing_metadata.get('title', '')
            if not artist or not title:
                logger.warning(f"Missing artist or title in {file_path}")
                return False
            # Remove apostrophes
            search_title = title.replace("'", "")
            # Remove trailing version like V1, V2, v1, v2 (with or without space)
            search_title = re.sub(r'\s*[Vv][0-9]+$', '', search_title).strip()
            # Remove "(LQ)" and "(Snippet)" (case insensitive)
            search_title = re.sub(r'\s*\([Ll][Qq]\)\s*', '', search_title)
            search_title = re.sub(r'\s*\([Ss]nippet\)\s*', '', search_title, flags=re.IGNORECASE)
            # Remove (OG) (case insensitive)
            search_title = re.sub(r'\s*\([Oo][Gg]\)\s*', '', search_title, flags=re.IGNORECASE)
            # Remove (feat. ...) and (with ...) (case-insensitive)
            search_title = re.sub(r'\s*\((feat\.|with)[^)]*\)', '', search_title, flags=re.IGNORECASE)
            # Split by "/" and use only the first part
            search_title = search_title.split('/')[0].strip()
            if search_title != title:
                logger.info(f"Title '{title}' -> Using '{search_title}' for search")
            # Check if lyrics already exist and we're not forcing update
            if not force_update:
                audio = MP3(file_path, ID3=ID3)
                if audio.tags and 'USLT::eng' in audio.tags:
                    logger.info(f"Lyrics already exist in {file_path}, skipping")
                    return True
            # Fetch new metadata using the search title
            genius_metadata = self.fetch_lyrics_and_metadata(artist, search_title)
            if not genius_metadata:
                logger.warning(f"Could not fetch metadata for {artist} - {search_title}")
                return False
            # Always use the original file's title for tagging
            genius_metadata['title'] = title
            # Update the file (only lyrics and year)
            success = self.update_mp3_metadata(file_path, genius_metadata)
            if success:
                logger.info(f"Successfully updated {file_path}")
            return success
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return False
    
    def process_directory(self, directory_path, force_update=False):
        """Process all MP3 files in a directory"""
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return
        
        mp3_files = list(directory.rglob("*.mp3"))
        if not mp3_files:
            logger.info(f"No MP3 files found in {directory_path}")
            return
        
        logger.info(f"Found {len(mp3_files)} MP3 files to process")
        
        successful = 0
        failed = 0
        
        for file_path in mp3_files:
            if self.process_file(str(file_path), force_update):
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Processing complete: {successful} successful, {failed} failed")

def main():
    parser = argparse.ArgumentParser(description='Genius Lyrics Fetcher - Batch MP3 metadata updater')
    parser.add_argument('path', help='Path to MP3 file or directory')
    parser.add_argument('--force', '-f', action='store_true', help='Force update even if lyrics already exist')
    parser.add_argument('--delay', '-d', type=float, default=1.0, help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--user-agent', '-u', help='Custom User-Agent string')
    
    args = parser.parse_args()
    
    fetcher = GeniusLyricsFetcher(delay=args.delay, user_agent=args.user_agent)
    
    path = Path(args.path)
    if path.is_file():
        if path.suffix.lower() == '.mp3':
            fetcher.process_file(str(path), args.force)
        else:
            logger.error("File is not an MP3 file")
    elif path.is_dir():
        fetcher.process_directory(str(path), args.force)
    else:
        logger.error(f"Path does not exist: {args.path}")

if __name__ == "__main__":
    main() 