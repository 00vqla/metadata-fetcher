#!/usr/bin/env python3
"""
Genius Lyrics Fetcher - Tkinter GUI
A GUI application for batch processing MP3 files with lyrics from Genius.com
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import queue
import os
from pathlib import Path
from genius_lyrics_fetcher import GeniusLyricsFetcher
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

DND_AVAILABLE = False

class GeniusLyricsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Genius Lyrics Fetcher")
        self.root.geometry("450x600")
        
        # Configure logging to use our GUI
        self.log_queue = queue.Queue()
        self.setup_logging()
        
        # Processing state
        self.processing = False
        self.current_song = ""
        self.failed_files = []  # For error summary
        
        # Initialize tk.Variable attributes before creating widgets
        self.force_var = tk.BooleanVar()
        self.delay_var = tk.DoubleVar(value=1.0)
        self.thread_var = tk.IntVar(value=1)
        self.section_format_var = tk.BooleanVar(value=True)
        
        self.create_widgets()
        self.update_log()
        
        if DND_AVAILABLE:
            self.setup_drag_and_drop()
    
    def setup_logging(self):
        """Setup logging to send messages to our GUI"""
        class QueueHandler(logging.Handler):
            def __init__(self, queue):
                super().__init__()
                self.queue = queue
            
            def emit(self, record):
                self.queue.put(self.format(record))
        
        # Configure logging
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add our queue handler
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(queue_handler)
    
    def create_widgets(self):
        """Create the GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)

        # File/Folder Selection (row 0)
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        ttk.Label(file_frame, text="Select MP3 File or Folder:").grid(row=0, column=0, sticky="w")
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(file_frame, textvariable=self.path_var, state='readonly')
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))
        ttk.Button(file_frame, text="Browse File", command=self.browse_file).grid(row=1, column=1, padx=(0, 5))
        ttk.Button(file_frame, text="Browse Folder", command=self.browse_folder).grid(row=1, column=2)

        # Options Frame (row 1)
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(options_frame, text="Force Update (overwrite existing lyrics)", variable=self.force_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(options_frame, text="Delay between requests (seconds):").grid(row=1, column=0, sticky="w", pady=2)
        delay_spin = ttk.Spinbox(options_frame, from_=0.1, to=10.0, increment=0.1, textvariable=self.delay_var, width=10)
        delay_spin.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=2)
        ttk.Label(options_frame, text="Thread count:").grid(row=2, column=0, sticky="w", pady=2)
        thread_spin = ttk.Spinbox(options_frame, from_=1, to=10, increment=1, textvariable=self.thread_var, width=10)
        thread_spin.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=2)
        ttk.Checkbutton(options_frame, text="Keep section headers ([Chorus], [Verse], etc.)", variable=self.section_format_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=2)

        # Action Buttons (row 2)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        button_frame.columnconfigure((0, 1, 2), weight=1)
        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_processing)
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=(0, 5), sticky="ew")
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).grid(row=0, column=2, sticky="ew")

        # Progress Frame (row 3)
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky="w")
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        # Log Frame (row 4)
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=4, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.config(state='disabled')
        main_frame.rowconfigure(4, weight=2)
    
    def setup_drag_and_drop(self):
        # Drag-and-drop support for file/folder selection
        def drop(event):
            path = event.data.strip().replace('{', '').replace('}', '')
            self.path_var.set(path)
        self.root.drop_target_register('DND_Files')
        self.root.dnd_bind('<<Drop>>', drop)
    
    def browse_file(self):
        """Browse for a single MP3 file"""
        filename = filedialog.askopenfilename(
            title="Select MP3 File",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        if filename:
            self.path_var.set(filename)
    
    def browse_folder(self):
        """Browse for a folder containing MP3 files"""
        folder = filedialog.askdirectory(title="Select Folder with MP3 Files")
        if folder:
            self.path_var.set(folder)
    
    def clear_log(self):
        """Clear the log display"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def update_log(self):
        """Update the log display from the queue"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.config(state='normal')
                self.log_text.insert(tk.END, message + '\n')
                self.log_text.see(tk.END)
                self.log_text.config(state='disabled')
        except queue.Empty:
            pass
        
        # Schedule next update
        self.root.after(100, self.update_log)
    
    def start_processing(self):
        """Start the processing in a separate thread"""
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("Error", "Please select a file or folder to process.")
            return
        
        if not os.path.exists(path):
            messagebox.showerror("Error", "Selected path does not exist.")
            return
        
        self.processing = True
        self.failed_files = []
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = 100
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.process_files, args=(path,), daemon=True)
        thread.start()
    
    def stop_processing(self):
        """Stop the processing"""
        self.processing = False
        self.progress_var.set("Stopping...")
    
    def process_files(self, path):
        """Process files in a separate thread"""
        try:
            fetcher = GeniusLyricsFetcher(
                delay=self.delay_var.get(),
                keep_sections=self.section_format_var.get()
            )
            
            # Process based on path type
            if os.path.isfile(path):
                self.process_single_file(fetcher, path)
            else:
                self.process_directory(fetcher, path)
                
        except Exception as e:
            logging.error(f"Processing error: {e}")
        finally:
            self.root.after(0, self.processing_finished)
    
    def process_single_file(self, fetcher, file_path):
        """Process a single file"""
        self.progress_var.set(f"Processing: {os.path.basename(file_path)}")
        
        if not self.processing:
            return
        
        try:
            success = fetcher.process_file(file_path, self.force_var.get())
            if success:
                logging.info(f"Successfully processed: {file_path}")
            else:
                logging.error(f"Failed to process: {file_path}")
                self.failed_files.append((file_path, "Processing failed"))
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            self.failed_files.append((file_path, str(e)))
    
    def process_directory(self, fetcher, directory_path):
        """Process all MP3 files in a directory"""
        directory = Path(directory_path)
        mp3_files = list(directory.rglob("*.mp3"))
        if not mp3_files:
            logging.warning(f"No MP3 files found in {directory_path}")
            return
        logging.info(f"Found {len(mp3_files)} MP3 files to process")
        successful = 0
        failed = 0
        total = len(mp3_files)
        thread_count = self.thread_var.get()
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            future_to_file = {executor.submit(self._process_file_threadsafe, fetcher, str(file_path), self.force_var.get()): file_path for file_path in mp3_files}
            for i, future in enumerate(as_completed(future_to_file)):
                file_path = future_to_file[future]
                try:
                    success = future.result()
                    if success:
                        successful += 1
                    else:
                        failed += 1
                        self.failed_files.append((str(file_path), "Processing failed"))
                except Exception as e:
                    logging.error(f"Error processing {file_path}: {e}")
                    failed += 1
                    self.failed_files.append((str(file_path), str(e)))
                # Update progress in the main thread
                self.root.after(0, self._update_progress, i+1, total, file_path.name)
        logging.info(f"Processing complete: {successful} successful, {failed} failed")
    
    def _process_file_threadsafe(self, fetcher, file_path, force):
        # This runs in a worker thread
        return fetcher.process_file(file_path, force)
    
    def _update_progress(self, current, total, filename):
        self.progress_var.set(f"Processing {current}/{total}: {filename}")
        self.progress_bar['value'] = (current/total)*100
        self.root.update_idletasks()
    
    def processing_finished(self):
        """Called when processing is finished"""
        self.processing = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress_bar.stop()
        self.progress_var.set("Ready")
        
        if self.failed_files:
            msg = "Some files failed to process:\n\n" + "\n".join(f"{os.path.basename(f)}: {reason}" for f, reason in self.failed_files)
            messagebox.showwarning("Processing Complete with Errors", msg)

def main():
    global DND_AVAILABLE
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
        DND_AVAILABLE = True
    except ImportError:
        root = tk.Tk()
    app = GeniusLyricsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 