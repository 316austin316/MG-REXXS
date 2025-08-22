import os
import struct
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import threading
import time
import cv2
from PIL import Image, ImageTk

# --- Custom Dark Mode Dialog Classes ---

class DarkMessageBox:
    def __init__(self, parent, title, message, message_type="info"):
        self.parent = parent
        self.title = title
        self.message = message
        self.message_type = message_type
        self.result = None
        
        # Create top-level window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x300")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"500x300+{x}+{y}")
        
        # Dark mode colors
        self.bg_color = "#2E2E2E"
        self.fg_color = "#EAEAEA"
        self.button_bg_color = "#4A4A4A"
        self.button_fg_color = "#EAEAEA"
        self.button_active_bg_color = "#5A5A5A"
        
        # Configure dialog
        self.dialog.config(bg=self.bg_color)
        
        # Create content
        self.create_widgets()
        
        # Wait for user interaction
        self.dialog.wait_window()
    
    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.dialog, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a frame for the message with scrollbar if needed
        message_frame = tk.Frame(main_frame, bg=self.bg_color)
        message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create text widget for better text handling
        text_widget = tk.Text(message_frame, 
                             bg=self.bg_color, fg=self.fg_color,
                             wrap=tk.WORD, relief=tk.FLAT, borderwidth=0,
                             font=("TkDefaultFont", 10), height=10)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(message_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Insert the message text
        text_widget.insert(tk.END, self.message)
        text_widget.config(state=tk.DISABLED)  # Make it read-only
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X)
        
        if self.message_type == "yesno":
            # Yes/No buttons
            yes_btn = tk.Button(button_frame, text="Yes", 
                              bg=self.button_bg_color, fg=self.button_fg_color,
                              activebackground=self.button_active_bg_color,
                              command=self.yes_clicked, width=10)
            yes_btn.pack(side=tk.RIGHT, padx=(5, 0))
            
            no_btn = tk.Button(button_frame, text="No", 
                             bg=self.button_bg_color, fg=self.button_fg_color,
                             activebackground=self.button_active_bg_color,
                             command=self.no_clicked, width=10)
            no_btn.pack(side=tk.RIGHT)
            
            # Focus on Yes button
            yes_btn.focus_set()
        else:
            # OK button
            ok_btn = tk.Button(button_frame, text="OK", 
                             bg=self.button_bg_color, fg=self.button_fg_color,
                             activebackground=self.button_active_bg_color,
                             command=self.ok_clicked, width=10)
            ok_btn.pack(side=tk.RIGHT)
            ok_btn.focus_set()
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.ok_clicked() if self.message_type != "yesno" else self.yes_clicked())
        self.dialog.bind('<Escape>', lambda e: self.no_clicked() if self.message_type == "yesno" else self.ok_clicked())
    
    def ok_clicked(self):
        self.result = True
        self.dialog.destroy()
    
    def yes_clicked(self):
        self.result = True
        self.dialog.destroy()
    
    def no_clicked(self):
        self.result = False
        self.dialog.destroy()

def show_dark_info(parent, title, message):
    """Show a dark-themed info dialog"""
    dialog = DarkMessageBox(parent, title, message, "info")
    return dialog.result

def show_dark_warning(parent, title, message):
    """Show a dark-themed warning dialog"""
    dialog = DarkMessageBox(parent, title, message, "warning")
    return dialog.result

def show_dark_error(parent, title, message):
    """Show a dark-themed error dialog"""
    dialog = DarkMessageBox(parent, title, message, "error")
    return dialog.result

def ask_dark_yesno(parent, title, message):
    """Show a dark-themed yes/no dialog"""
    dialog = DarkMessageBox(parent, title, message, "yesno")
    return dialog.result

# --- Constants and Core Logic (Copied from the base script) ---

# Constants for Mersenne Twister (MT19937) - standard parameters
N = 624
M = 397
MATRIX_A = 0x9908b0df
UPPER_MASK = 0x80000000 # 32-bit MSB
LOWER_MASK = 0x7fffffff # 32-bit LSBs

class MersenneTwister:
    def __init__(self):
        self.mt = [0] * N
        self.mti = N + 1

    def _initialize(self, seed):
        current_value = seed & 0xFFFFFFFF
        for i in range(N):
            term1 = (current_value * 69069 + 1) & 0xFFFFFFFF
            self.mt[i] = ((term1 >> 16) | (current_value & 0xffff0000)) & 0xFFFFFFFF
            current_value = (term1 * 69069 + 1) & 0xFFFFFFFF
        self.mti = N

    def _twist(self):
        for i in range(N):
            val_term1 = self.mt[i] & UPPER_MASK
            val_term2 = self.mt[(i + 1) % N] & LOWER_MASK
            y = (val_term1 + val_term2) & 0xFFFFFFFF
            self.mt[i] = self.mt[(i + M) % N] ^ (y >> 1)
            if (y & 1) != 0:
                self.mt[i] = (self.mt[i] ^ MATRIX_A) & 0xFFFFFFFF
            self.mt[i] &= 0xFFFFFFFF
        self.mti = 0

    def gen_rand_int32(self):
        if self.mti >= N:
            if self.mti == N + 1: pass
            self._twist()
        y = self.mt[self.mti]
        self.mti += 1
        y ^= (y >> 11)
        y ^= (y << 7) & 0x9d2c5680; y &= 0xFFFFFFFF
        y ^= (y << 15) & 0xefc60000; y &= 0xFFFFFFFF
        y ^= (y >> 18)
        return y & 0xFFFFFFFF

def gen_seed(file_path):
    # Use the version that splits at the first dot, likely closer to eol code
    filename = os.path.basename(file_path)
    name_lower = filename
    name_base = name_lower.split('.', 1)[0]
    # Fallback if split didn't find a dot (shouldn't happen with .xxs/.mp4 but safe)
    if not name_base:
         name_base = name_lower

    seed = 0
    for char in name_base:
        c = ord(char)
        seed = (seed * 0x2356f + c * 0x1d35) & 0xFFFFFFFF
    return seed & 0xFFFFFFFF

# --- GUI Adapted Processing Function ---


def process_file_threaded(input_path, output_path, status_callback, progress_callback, finished_callback):
    """
    Processes the file (encrypt/decrypt) in a background thread.

    Args:
        input_path (str): Path to the input file.
        output_path (str): Path for the output file.
        status_callback (function): Function to call with status string updates.
        progress_callback (function): Function to call with progress updates (0-100).
        finished_callback (function): Function to call when processing is done (success or fail).
    """
    try:
        status_callback(f"Processing: {os.path.basename(input_path)}")
        if not os.path.exists(input_path):
            raise FileNotFoundError("Input file not found.")

        # Determine which filename to use for seeding
        is_encrypting = output_path.lower().endswith(".xxs")
        seed_path = output_path if is_encrypting else input_path
        base_seed_name = os.path.basename(seed_path)
        status_callback(f"Mode: {'Encrypting' if is_encrypting else 'Decrypting'}")

        # 1. Calculate Seed
        seed = gen_seed(seed_path)
        status_callback(f"Seed: {seed} (0x{seed:08X}) for '{base_seed_name}'")

        # 2. Initialize Mersenne Twister
        mt = MersenneTwister()
        mt._initialize(seed)
        status_callback("PRNG initialized.")

        # 3. Get file size for progress
        file_size = os.path.getsize(input_path)
        status_callback(f"File size: {file_size} bytes.")
        if file_size == 0:
             raise ValueError("Input file is empty.")

        processed_bytes = 0
        update_interval = max(1, file_size // 100) # Update progress roughly 100 times

        # Use chunked reading/writing for potentially large files
        status_callback("Starting file processing...")
        progress_callback(0) # Start progress bar

        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            while True:
                chunk = f_in.read(4) # Read 4 bytes
                if not chunk:
                    break # End of file

                rand_num = mt.gen_rand_int32()

                if len(chunk) == 4:
                    original_value = struct.unpack('<I', chunk)[0]
                    processed_value = (original_value ^ rand_num) & 0xFFFFFFFF
                    f_out.write(struct.pack('<I', processed_value))
                else: # Handle remaining bytes (1, 2, or 3)
                    rand_bytes = struct.pack('<I', rand_num)
                    processed_chunk = bytes([b ^ rand_bytes[i] for i, b in enumerate(chunk)])
                    f_out.write(processed_chunk)

                processed_bytes += len(chunk)

                # Update progress (avoiding too frequent updates)
                if processed_bytes % update_interval == 0 or processed_bytes == file_size:
                    progress = int((processed_bytes / file_size) * 100)
                    progress_callback(progress)
                    # Give the event loop a tiny bit of time if needed, but usually IO bound
                    # time.sleep(0.001) # Uncomment if GUI feels sluggish during IO

        progress_callback(100) # Ensure progress hits 100%
        status_callback(f"Success! Output saved to {os.path.basename(output_path)}")
        finished_callback(True) # Signal success

    except Exception as e:
        status_callback(f"Error: {e}")
        # import traceback # Optional detailed error for console/log
        # traceback.print_exc()
        finished_callback(False) # Signal failure

# --- Video Viewer Class ---

class VideoViewer:
    def __init__(self, parent):
        self.parent = parent
        self.video_path = None
        self.cap = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.video_thread = None
        self.is_updating_slider = False  # Flag to prevent recursive calls
        self.video_lock = threading.Lock()  # Lock for video operations
        
        # Create video display frame
        self.video_frame = ttk.Frame(parent)
        self.video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video display label
        self.video_label = ttk.Label(self.video_frame, text="No video loaded")
        self.video_label.pack(expand=True)
        
        # Control frame
        self.control_frame = ttk.Frame(self.video_frame)
        self.control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Control buttons
        self.btn_play = ttk.Button(self.control_frame, text="Play", command=self.play_video, state='disabled')
        self.btn_play.pack(side=tk.LEFT, padx=(0, 5))
        
        self.btn_pause = ttk.Button(self.control_frame, text="Pause", command=self.pause_video, state='disabled')
        self.btn_pause.pack(side=tk.LEFT, padx=(0, 5))
        
        self.btn_stop = ttk.Button(self.control_frame, text="Stop", command=self.stop_video, state='disabled')
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 5))
        
        # Progress slider
        self.progress_var = tk.DoubleVar()
        self.progress_slider = ttk.Scale(self.control_frame, from_=0, to=100, 
                                       variable=self.progress_var, orient=tk.HORIZONTAL,
                                       command=self.seek_video)
        self.progress_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Time label
        self.time_label = ttk.Label(self.control_frame, text="00:00 / 00:00")
        self.time_label.pack(side=tk.RIGHT, padx=(5, 0))
    
    def load_video(self, video_path):
        """Load a video file for playback"""
        with self.video_lock:
            if self.cap:
                self.cap.release()
            
            self.video_path = video_path
            
            # Try to open video with different backends to avoid threading issues
            try:
                # First try with default backend
                self.cap = cv2.VideoCapture(video_path)
                if not self.cap.isOpened():
                    # Try with different backend
                    self.cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
                
                if not self.cap.isOpened():
                    show_dark_error(self.parent, "Error", f"Could not open video: {video_path}")
                    return False
                
                # Get video properties
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.fps = self.cap.get(cv2.CAP_PROP_FPS)
                
                # Validate properties
                if self.total_frames <= 0 or self.fps <= 0:
                    show_dark_error(self.parent, "Error", f"Invalid video properties: {video_path}")
                    return False
                
                # Enable controls
                self.btn_play.config(state='normal')
                self.btn_pause.config(state='normal')
                self.btn_stop.config(state='normal')
                
                # Show first frame
                self.show_frame(0)
                self.update_time_label()
                
                return True
                
            except Exception as e:
                show_dark_error(self.parent, "Error", f"Error loading video: {e}")
                return False
    
    def show_frame(self, frame_number):
        """Display a specific frame"""
        if not self.video_path:
            return
        
        try:
            # Create a new capture for each frame to avoid threading issues
            temp_cap = cv2.VideoCapture(self.video_path)
            if not temp_cap.isOpened():
                return
            
            temp_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = temp_cap.read()
            temp_cap.release()
            
            if ret:
                # Resize frame to fit display (max 640x480)
                height, width = frame.shape[:2]
                max_width, max_height = 640, 480
                
                if width > max_width or height > max_height:
                    scale = min(max_width / width, max_height / height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image and then to PhotoImage
                pil_image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(pil_image)
                
                # Update GUI in main thread
                self.parent.after(0, self._update_frame_gui, photo, frame_number)
        except Exception as e:
            print(f"Error reading frame {frame_number}: {e}")
            # Try to recover by seeking to a different frame
            if frame_number > 0:
                self.show_frame(frame_number - 1)
    
    def _update_frame_gui(self, photo, frame_number):
        """Update GUI elements in the main thread"""
        self.video_label.config(image=photo, text="")
        self.video_label.image = photo  # Keep a reference
        self.current_frame = frame_number
        self.update_progress()
        self.update_time_label()
    
    def play_video(self):
        """Start video playback"""
        if not self.cap or self.is_playing:
            return
        
        self.is_playing = True
        self.video_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.video_thread.start()
    
    def _play_loop(self):
        """Video playback loop"""
        try:
            while self.is_playing and self.current_frame < self.total_frames - 1:
                self.current_frame += 1
                self.show_frame(self.current_frame)
                
                # Calculate delay based on FPS
                delay = 1.0 / self.fps if self.fps > 0 else 0.033
                time.sleep(delay)
            
            if self.current_frame >= self.total_frames - 1:
                self.is_playing = False
        except Exception as e:
            print(f"Video playback error: {e}")
            self.is_playing = False
    
    def pause_video(self):
        """Pause video playback"""
        self.is_playing = False
    
    def stop_video(self):
        """Stop video playback and reset to beginning"""
        self.is_playing = False
        self.current_frame = 0
        self.show_frame(0)
        self.update_time_label()
    
    def seek_video(self, value):
        """Seek to a specific position in the video"""
        if not self.cap or self.is_updating_slider:
            return
        
        # Pause playback if it's currently playing
        was_playing = self.is_playing
        if was_playing:
            self.is_playing = False
        
        frame_number = int((float(value) / 100.0) * self.total_frames)
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        self.show_frame(frame_number)
        
        # Resume playback if it was playing before
        if was_playing:
            self.is_playing = True
            if not self.video_thread or not self.video_thread.is_alive():
                self.video_thread = threading.Thread(target=self._play_loop, daemon=True)
                self.video_thread.start()
    
    def update_progress(self):
        """Update progress slider"""
        if self.total_frames > 0:
            progress = (self.current_frame / self.total_frames) * 100
            # Only update if the difference is significant to avoid slider jumping
            current_progress = self.progress_var.get()
            if abs(progress - current_progress) > 1.0:  # Only update if difference > 1%
                self.is_updating_slider = True
                self.progress_var.set(progress)
                self.is_updating_slider = False
    
    def update_time_label(self):
        """Update time display"""
        if self.fps > 0:
            current_time = self.current_frame / self.fps
            total_time = self.total_frames / self.fps
            
            current_min = int(current_time // 60)
            current_sec = int(current_time % 60)
            total_min = int(total_time // 60)
            total_sec = int(total_time % 60)
            
            time_text = f"{current_min:02d}:{current_sec:02d} / {total_min:02d}:{total_sec:02d}"
            self.time_label.config(text=time_text)
    
    def cleanup(self):
        """Clean up video resources"""
        self.is_playing = False
        self.video_path = None

# --- Tkinter GUI Application ---

class MgRexxsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MG-REXXS")
        self.root.geometry("700x500")
        self.root.resizable(True, True) # Allow resizing for video viewer
        
        # --- Color Palette (Dark Mode) ---
        self.bg_color = "#2E2E2E"
        self.fg_color = "#EAEAEA"
        self.entry_bg_color = "#3C3C3C"
        self.entry_fg_color = self.fg_color
        self.button_bg_color = "#4A4A4A"
        self.button_fg_color = self.fg_color
        self.button_active_bg_color = "#5A5A5A"
        self.progress_trough_color = "#4A4A4A"
        self.progress_bar_color = "#007ACC" # Accent blue
        self.status_bg_color = self.bg_color # Match main background
        self.status_fg_color = self.fg_color
        
        # --- Style Configuration ---
        style = ttk.Style(self.root)
        style.theme_use('clam') # 'clam' is often easier to customize

        # Configure root window background
        self.root.config(bg=self.bg_color)

        # General widget styling
        style.configure('.', background=self.bg_color, foreground=self.fg_color)
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TEntry', fieldbackground=self.entry_bg_color, foreground=self.entry_fg_color,
                        insertcolor=self.fg_color, # Cursor color
                        bordercolor=self.button_bg_color) # Border to match buttons somewhat
        style.map('TEntry', fieldbackground=[('readonly', self.entry_bg_color)]) # Ensure readonly keeps color

        # Button styling
        style.configure('TButton', background=self.button_bg_color, foreground=self.button_fg_color,
                        borderwidth=1, focusthickness=3, focuscolor='') # Remove focus ring if desired
        style.map('TButton',
                  background=[('active', self.button_active_bg_color), ('disabled', '#383838')],
                  foreground=[('disabled', '#777777')])

        # Tab styling - make selected tabs darker and reduce visual height difference
        style.configure('TNotebook.Tab', 
                       background=self.button_bg_color, 
                       foreground=self.button_fg_color,
                       padding=[10, 3],  # Reduced vertical padding
                       relief='flat')  # Remove 3D effect
        style.map('TNotebook.Tab',
                 background=[('selected', '#2A2A2A'), ('active', self.button_active_bg_color)],
                 foreground=[('selected', self.button_fg_color), ('active', self.button_fg_color)],
                 relief=[('selected', 'flat'), ('active', 'flat')])  # Keep flat relief for all states

        # Progress bar styling
        style.configure('Horizontal.TProgressbar',
                        troughcolor=self.progress_trough_color,
                        background=self.progress_bar_color, # The actual bar color
                        bordercolor=self.bg_color, # Match background
                        lightcolor=self.bg_color, darkcolor=self.bg_color)
        

        self.input_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()
        self.status_text = tk.StringVar()
        self.status_text.set("Select a file (.xxs or other) to process.")

        # --- Menu Bar ---
        self.create_menu()

        # --- Create Notebook for Tabs ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- Converter Tab ---
        self.converter_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.converter_frame, text="Converter")

        # --- Input Row ---
        frame_input = ttk.Frame(self.converter_frame, padding="10 5 10 5")
        frame_input.pack(fill=tk.X)

        lbl_input = ttk.Label(frame_input, text="Input File:")
        lbl_input.pack(side=tk.LEFT, padx=(0, 5))

        self.entry_input = ttk.Entry(frame_input, textvariable=self.input_file_path, state='readonly', width=50)
        self.entry_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.btn_browse = ttk.Button(frame_input, text="Browse...", command=self.browse_file)
        self.btn_browse.pack(side=tk.LEFT)

        # --- Output Row ---
        frame_output = ttk.Frame(self.converter_frame, padding="10 5 10 5")
        frame_output.pack(fill=tk.X)

        lbl_output = ttk.Label(frame_output, text="Output File:")
        lbl_output.pack(side=tk.LEFT, padx=(0, 5))

        self.entry_output = ttk.Entry(frame_output, textvariable=self.output_file_path, state='readonly', width=60)
        self.entry_output.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # --- Process Button ---
        self.btn_process = ttk.Button(self.converter_frame, text="Process File", state='disabled', command=self.start_processing_thread)
        self.btn_process.pack(pady=10)

        # --- Progress Bar ---
        self.progress_var = tk.DoubleVar()
        # Use the configured style for the progress bar
        self.progress_bar = ttk.Progressbar(self.converter_frame, variable=self.progress_var, maximum=100,
                                            length=530, style='Horizontal.TProgressbar')
        self.progress_bar.pack(pady=5, padx=10)

        # --- Video Viewer Tab ---
        self.video_viewer = VideoViewer(self.notebook)
        self.notebook.add(self.video_viewer.video_frame, text="Video Viewer")

        # --- Status Bar ---
        # Using tk.Label for easier background/foreground control if needed, styled similarly
        self.lbl_status = tk.Label(self.root, textvariable=self.status_text, relief=tk.SUNKEN, bd=1,
                                   anchor=tk.W, padx=5, pady=2,
                                   bg=self.status_bg_color, fg=self.status_fg_color)
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0), padx=0)
        
    
    def create_menu(self):
        # Note: Menu bar styling is limited by OS native rendering on Windows
        # The system may override our custom colors
        menubar = tk.Menu(self.root, bg=self.bg_color, fg=self.fg_color, 
                         activebackground=self.button_active_bg_color, 
                         activeforeground=self.fg_color)
        self.root.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0, bg=self.bg_color, fg=self.fg_color,
                           activebackground=self.button_active_bg_color, 
                           activeforeground=self.fg_color)
        menubar.add_cascade(label="Info", menu=help_menu)

        help_menu.add_command(label="About MG-REXXS", command=self.show_about)

    def show_about(self):
        about_text = """MG-REXXS Tool Version: 1.1

A GUI tool to encrypt/decrypt MGS2/MGS3 Master Collection .xxs files.

Features:
• Decrypt .xxs files to standard formats (MP4)
• Encrypt standard files back to .xxs format
• Built-in video viewer with playback controls

Credits:
• Original .xxs algorithm/script: eol
• GUI code: 316austin316
"""
        show_dark_info(self.root, "About MG-REXXS", about_text)

    def browse_file(self):
        # Define file types (adapt if needed)
        filetypes = [
            ('MGS XXS Files', '*.xxs'),
            ('MP4 Videos', '*.mp4'),
            ('All Files', '*.*')
        ]
        # Ask for file path
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if not filepath:
            return # User cancelled

        self.input_file_path.set(filepath)
        self.status_text.set("Input file selected. Ready to process.")
        self.progress_var.set(0) # Reset progress bar

        # Determine output path automatically
        try:
            dirname = os.path.dirname(filepath)
            filename = os.path.basename(filepath)
            name_base, ext = os.path.splitext(filename)
            ext_lower = ext.lower()

            if ext_lower == '.xxs':
                # Decrypting: default to .mp4, could be configurable later
                output_ext = '.mp4'
                output_filename = name_base + output_ext
            else:
                # Encrypting: always output .xxs
                output_ext = '.xxs'
                output_filename = name_base + output_ext

            self.output_file_path.set(os.path.join(dirname, output_filename))
            self.btn_process.config(state='normal') # Enable process button
        except Exception as e:
             show_dark_error(self.root, "Error", f"Could not determine output filename: {e}")
             self.output_file_path.set("")
             self.btn_process.config(state='disabled')


    def start_processing_thread(self):
        in_path = self.input_file_path.get()
        out_path = self.output_file_path.get()

        if not in_path or not out_path:
            show_dark_warning(self.root, "Missing Info", "Please select an input file first.")
            return
            
        is_encrypting = out_path.lower().endswith(".xxs")
        if is_encrypting:
            output_basename = os.path.basename(out_path)
            warning_message = (
                "You are about to encrypt to an `.xxs` file.\n\n"
                f"IMPORTANT: The encryption key is *directly tied* to the output filename: '{output_basename}'\n\n"
                "This filename MUST EXACTLY match the one the game expects for this video.\n"
                "Using a different name will result in a key mismatch and likely failure to play.\n\n"
                "Do you want to proceed with encryption using this output name?"
            )
            # Ask for confirmation before starting
            proceed = ask_dark_yesno(self.root, "Encryption Filename Confirmation", warning_message)
        
            if not proceed:
                self.status_text.set("Encryption cancelled by user.")
                return  # Stop here if user clicks No


        # Disable buttons during processing
        self.btn_browse.config(state='disabled')
        self.btn_process.config(state='disabled')
        self.status_text.set("Starting...")
        self.progress_var.set(0) # Reset progress

        # Run processing in a separate thread
        self.processing_thread = threading.Thread(
            target=process_file_threaded,
            args=(in_path, out_path, self.update_status, self.update_progress, self.on_finished),
            daemon=True # Allows closing window even if thread is running (use cautiously)
        )
        self.processing_thread.start()

    # --- Callback Functions (Must update GUI safely) ---
    def update_status(self, message):
        # Schedule GUI update from the main thread
        self.root.after(0, lambda: self.status_text.set(message))

    def update_progress(self, value):
         # Schedule GUI update from the main thread
        self.root.after(0, lambda: self.progress_var.set(value))

    def on_finished(self, success):
        # Schedule GUI update from the main thread
        self.root.after(0, self._on_finished_gui, success) # Pass success flag

    def _on_finished_gui(self, success):
        # This runs in the main GUI thread
        if success:
            # Check if we created an MP4 file and auto-load it in the video viewer
            output_path = self.output_file_path.get()
            if output_path.lower().endswith('.mp4') and os.path.exists(output_path):
                # Switch to video viewer tab and load the video
                self.notebook.select(1)  # Switch to video viewer tab
                self.video_viewer.load_video(output_path)
                self.status_text.set(f"Success! Video loaded in viewer: {os.path.basename(output_path)}")
            else:
                # Status bar already shows success message
                pass
        else:
            # Status bar already shows error message
            show_dark_error(self.root, "Error", "File processing failed. Check status bar for details.")

        # Re-enable buttons
        self.btn_browse.config(state='normal')
        self.btn_process.config(state='normal')
        # Keep progress bar at 100 or 0 depending on success? Or reset?
        # self.progress_var.set(0) # Reset progress bar

    def on_closing(self):
        """Clean up resources when closing the app"""
        if hasattr(self, 'video_viewer'):
            self.video_viewer.cleanup()
        self.root.destroy()


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MgRexxsApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Handle window closing
    root.mainloop()