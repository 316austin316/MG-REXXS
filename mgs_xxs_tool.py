import os
import struct
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import threading
import time 

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

# --- Tkinter GUI Application ---

class MgRexxsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MG-REXXS")
        self.root.geometry("550x220")
        self.root.resizable(False, False) # Prevent resizing
        
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

        # --- Input Row ---
        frame_input = ttk.Frame(self.root, padding="10 5 10 5")
        frame_input.pack(fill=tk.X)

        lbl_input = ttk.Label(frame_input, text="Input File:")
        lbl_input.pack(side=tk.LEFT, padx=(0, 5))

        self.entry_input = ttk.Entry(frame_input, textvariable=self.input_file_path, state='readonly', width=50)
        self.entry_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.btn_browse = ttk.Button(frame_input, text="Browse...", command=self.browse_file)
        self.btn_browse.pack(side=tk.LEFT)

        # --- Output Row ---
        frame_output = ttk.Frame(self.root, padding="10 5 10 5")
        frame_output.pack(fill=tk.X)

        lbl_output = ttk.Label(frame_output, text="Output File:")
        lbl_output.pack(side=tk.LEFT, padx=(0, 5))

        self.entry_output = ttk.Entry(frame_output, textvariable=self.output_file_path, state='readonly', width=60)
        self.entry_output.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # --- Process Button ---
        self.btn_process = ttk.Button(self.root, text="Process File", state='disabled', command=self.start_processing_thread)
        self.btn_process.pack(pady=10)

        # --- Progress Bar ---
        self.progress_var = tk.DoubleVar()
        # Use the configured style for the progress bar
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100,
                                            length=530, style='Horizontal.TProgressbar')
        self.progress_bar.pack(pady=5, padx=10)


        # --- Status Bar ---
        # Using tk.Label for easier background/foreground control if needed, styled similarly
        self.lbl_status = tk.Label(self.root, textvariable=self.status_text, relief=tk.SUNKEN, bd=1,
                                   anchor=tk.W, padx=5, pady=2,
                                   bg=self.status_bg_color, fg=self.status_fg_color)
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0), padx=0)
        
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Info", menu=help_menu)

        help_menu.add_command(label="About MG-REXXS", command=self.show_about)

    def show_about(self):
        about_text = """
MG-REXXS Tool

A GUI tool to encrypt/decrypt MGS2/MGS3 Master Collection .xxs files.

Credits:
- Original .xxs script/logic: eol
- GUI Code: 316austin316

Version: 1.0
        """
        messagebox.showinfo("About MG-REXXS", about_text)

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
             messagebox.showerror("Error", f"Could not determine output filename: {e}")
             self.output_file_path.set("")
             self.btn_process.config(state='disabled')


    def start_processing_thread(self):
        in_path = self.input_file_path.get()
        out_path = self.output_file_path.get()

        if not in_path or not out_path:
            messagebox.showwarning("Missing Info", "Please select an input file first.")
            return

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
            # Optionally show success message box
            # messagebox.showinfo("Success", "File processing completed successfully!")
            pass # Status bar already shows success message
        else:
            # Status bar already shows error message
            messagebox.showerror("Error", "File processing failed. Check status bar for details.")

        # Re-enable buttons
        self.btn_browse.config(state='normal')
        self.btn_process.config(state='normal')
        # Keep progress bar at 100 or 0 depending on success? Or reset?
        # self.progress_var.set(0) # Reset progress bar


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MgRexxsApp(root)
    root.mainloop()