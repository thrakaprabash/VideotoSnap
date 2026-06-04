import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from PIL import Image, ImageTk
from video_processor import extract_snapshots

class VideoSnapshotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Snapshot Extractor Pro")
        self.root.geometry("650x700")
        self.root.resizable(False, False)
        
        # Apply modern style
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        main_frame = ttk.Frame(root, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- 1. Video File Selection ---
        ttk.Label(main_frame, text="Video File:", font=('', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.video_path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.video_path_var, width=50, state='readonly').grid(row=0, column=1, sticky=tk.EW, padx=5, pady=(0, 5))
        ttk.Button(main_frame, text="Browse...", command=self.browse_video).grid(row=0, column=2, sticky=tk.E, pady=(0, 5))
        
        # --- 2. Custom Output Directory ---
        ttk.Label(main_frame, text="Output Folder:", font=('', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.output_dir_var, width=50, state='readonly').grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_folder).grid(row=1, column=2, sticky=tk.E, pady=5)
        ttk.Label(main_frame, text="(Leave empty for default folder next to video)", font=('', 8)).grid(row=2, column=1, sticky=tk.W, padx=5, pady=(0, 10))

        # --- 3. Advanced Settings Panel ---
        settings_frame = ttk.LabelFrame(main_frame, text="Extraction Settings", padding="15 15 15 15")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Row 0: Snaps & Format
        ttk.Label(settings_frame, text="Number of Snaps:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.num_snaps_var = tk.StringVar(value="20")
        ttk.Spinbox(settings_frame, from_=1, to=10000, textvariable=self.num_snaps_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(settings_frame, text="Format:").grid(row=0, column=2, sticky=tk.E, pady=5, padx=(20, 5))
        self.format_var = tk.StringVar(value="JPG")
        ttk.Combobox(settings_frame, textvariable=self.format_var, values=["JPG", "PNG"], state="readonly", width=8).grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Row 1: Quality & Watermark
        ttk.Label(settings_frame, text="Quality (0-100):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.IntVar(value=95)
        quality_scale = ttk.Scale(settings_frame, from_=10, to=100, variable=self.quality_var, orient=tk.HORIZONTAL)
        quality_scale.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        
        self.watermark_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Add Timestamp Watermark", variable=self.watermark_var).grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=5, padx=(20, 5))
        
        # Row 2: Time Range
        ttk.Label(settings_frame, text="Start Time (sec):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.start_var = tk.StringVar()
        ttk.Entry(settings_frame, textvariable=self.start_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(settings_frame, text="End Time (sec):").grid(row=2, column=2, sticky=tk.E, pady=5, padx=(20, 5))
        self.end_var = tk.StringVar()
        ttk.Entry(settings_frame, textvariable=self.end_var, width=10).grid(row=2, column=3, sticky=tk.W, pady=5)
        ttk.Label(settings_frame, text="(Leave times empty to process full video)", font=('', 8)).grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # --- 4. Generate Button ---
        self.generate_btn = ttk.Button(main_frame, text="Generate Snapshots", command=self.start_generation)
        self.generate_btn.grid(row=4, column=0, columnspan=3, pady=(20, 10), ipadx=10, ipady=5)
        
        # --- 5. Progress ---
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=6, column=0, columnspan=3, sticky=tk.W)
        
        # --- 6. Live Thumbnail Preview ---
        self.preview_label = ttk.Label(main_frame, text="Live Preview Area", anchor=tk.CENTER, background="#333333", foreground="white")
        # Ensure a minimum height for the preview panel
        self.preview_label.grid(row=7, column=0, columnspan=3, pady=15, sticky=tk.NSEW)
        main_frame.rowconfigure(7, minsize=260)
        
        self.preview_image_ref = None # Store reference to avoid garbage collection

    def browse_video(self):
        filename = filedialog.askopenfilename(
            title="Select Video",
            filetypes=(("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"), ("All files", "*.*"))
        )
        if filename:
            self.video_path_var.set(filename)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir_var.set(folder)

    def update_progress(self, current, total, thumbnail_rgb):
        """Callback from video_processor, runs in background thread."""
        percent = (current / total) * 100
        # Convert numpy RGB to PIL Image
        img = Image.fromarray(thumbnail_rgb)
        
        # Schedule GUI update on the main thread
        self.root.after(0, self._update_gui_progress, percent, current, total, img)

    def _update_gui_progress(self, percent, current, total, pil_image):
        """Updates UI safely on the main thread."""
        self.progress_var.set(percent)
        self.status_var.set(f"Extracting: {current} / {total} snaps...")
        
        # Display thumbnail
        tk_image = ImageTk.PhotoImage(pil_image)
        self.preview_label.configure(image=tk_image, text="")
        self.preview_image_ref = tk_image 

    def extraction_thread(self, kwargs):
        """Runs in background thread to avoid freezing GUI."""
        try:
            output_dir, count = extract_snapshots(**kwargs)
            self.root.after(0, self.extraction_complete, True, f"Successfully extracted {count} snaps to:\n{output_dir}")
        except Exception as e:
            self.root.after(0, self.extraction_complete, False, str(e))

    def start_generation(self):
        video_path = self.video_path_var.get()
        if not video_path:
            messagebox.showerror("Error", "Please select a video file first.")
            return
            
        try:
            num_snaps = int(self.num_snaps_var.get())
            if num_snaps <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive integer for number of snaps.")
            return
            
        # Parse optional time inputs
        start_sec_val = self.start_var.get().strip()
        start_sec = float(start_sec_val) if start_sec_val else None
        
        end_sec_val = self.end_var.get().strip()
        end_sec = float(end_sec_val) if end_sec_val else None
        
        # Collect parameters
        kwargs = {
            'video_path': video_path,
            'num_snaps': num_snaps,
            'output_dir': self.output_dir_var.get() or None,
            'start_sec': start_sec,
            'end_sec': end_sec,
            'img_format': self.format_var.get(),
            'quality': self.quality_var.get(),
            'add_watermark': self.watermark_var.get(),
            'progress_callback': self.update_progress
        }

        # Disable UI elements during processing
        self.generate_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_var.set("Starting extraction...")
        self.preview_label.configure(image='', text="Starting...")
        
        # Start background thread
        thread = threading.Thread(target=self.extraction_thread, args=(kwargs,))
        thread.daemon = True
        thread.start()

    def extraction_complete(self, success, message):
        """Re-enables UI and shows result dialog."""
        self.generate_btn.config(state=tk.NORMAL)
        if success:
            self.status_var.set("Done!")
            messagebox.showinfo("Success", message)
        else:
            self.status_var.set("Error!")
            messagebox.showerror("Extraction Error", f"An error occurred:\n{message}")
            self.progress_var.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoSnapshotApp(root)
    root.mainloop()
