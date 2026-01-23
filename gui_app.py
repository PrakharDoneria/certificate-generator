import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import sys
from PIL import Image, ImageDraw
import math

try:
    import generator
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import generator

COLORS = {
    "dark_bg": "#1A1A1A",
    "dark_secondary": "#2D2D2D",
    "white": "#FFFFFF",
    "light_bg": "#F8F8FA",
    "card_bg": "#FFFFFF",
    "accent_orange": "#E85D3D",
    "accent_gold": "#D4A853",
    "accent_teal": "#4A90A4",
    "text_primary": "#1A1A1A",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
    "border": "#E5E7EB",
    "success": "#10B981",
    "gradient_start": "#8B5CF6",
    "gradient_end": "#EC4899"
}

ctk.set_appearance_mode("Light")

class PulseLoader(ctk.CTkFrame):
    """Animated pulse loading indicator"""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.dots = []
        self.is_animating = False
        self.current_dot = 0
        
        for i in range(3):
            dot = ctk.CTkLabel(
                self, text="●", 
                font=ctk.CTkFont(size=18),
                text_color=COLORS["text_muted"]
            )
            dot.pack(side="left", padx=3)
            self.dots.append(dot)
    
    def start(self):
        self.is_animating = True
        self._animate()
    
    def stop(self):
        self.is_animating = False
        for dot in self.dots:
            dot.configure(text_color=COLORS["text_muted"])
    
    def _animate(self):
        if not self.is_animating:
            return
        
        for i, dot in enumerate(self.dots):
            if i == self.current_dot:
                dot.configure(text_color=COLORS["accent_orange"])
            else:
                dot.configure(text_color=COLORS["text_muted"])
        
        self.current_dot = (self.current_dot + 1) % 3
        self.after(200, self._animate)

class AnimatedProgressBar(ctk.CTkFrame):
    """Custom progress bar with smooth animation"""
    def __init__(self, master, **kwargs):
        super().__init__(master, height=6, fg_color=COLORS["border"], corner_radius=3, **kwargs)
        self.progress = ctk.CTkFrame(self, height=6, fg_color=COLORS["accent_orange"], corner_radius=3, width=0)
        self.progress.place(x=0, y=0)
        self._target = 0
        self._current = 0
        
    def set_progress(self, value):
        """Set progress (0-100)"""
        self._target = value
        self._animate_to_target()
    
    def _animate_to_target(self):
        if abs(self._current - self._target) < 1:
            self._current = self._target
            width = int((self._current / 100) * self.winfo_width())
            self.progress.configure(width=max(1, width))
            return
        
        self._current += (self._target - self._current) * 0.15
        width = int((self._current / 100) * self.winfo_width())
        self.progress.configure(width=max(1, width))
        self.after(16, self._animate_to_target)

class CertificateApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SoftBridge Certificate Generator")
        self.geometry("1400x900")
        self.configure(fg_color=COLORS["light_bg"])
        
        # Start maximized
        self.after(0, lambda: self.state("zoomed"))

        # Configure resource paths
        self.base_path = generator.get_base_path()
        self.assets_dir = os.path.join(self.base_path, "assets")
        self.banner_path = os.path.join(self.assets_dir, "banner.png")
        
        # Config variables
        self.template_path = tk.StringVar(value=generator.DEFAULT_TEMPLATE_PATH)
        self.data_path = tk.StringVar(value="")
        self.output_dir = tk.StringVar(value=os.path.join(os.getcwd(), "certificates"))
        self.name_pos_y = tk.DoubleVar(value=45.0)
        
        self._preview_timer = None
        self._is_generating = False

        self._create_widgets()
        self.schedule_preview_update()

    def _create_decorative_circles(self, parent):
        """Create decorative circles like Fairvest UI"""
        canvas = tk.Canvas(parent, bg=COLORS["dark_bg"], highlightthickness=0, width=350, height=300)
        canvas.pack(pady=20)
        
        # Large circle outline
        canvas.create_oval(50, 20, 300, 270, outline="#3D3D3D", width=2)
        
        # Gold circle
        canvas.create_oval(180, 80, 260, 160, fill=COLORS["accent_gold"], outline="")
        
        # Teal/blue semi-circle
        canvas.create_arc(80, 120, 220, 260, start=0, extent=180, 
                         fill=COLORS["accent_teal"], outline="")
        
        # Orange small circle
        canvas.create_oval(60, 180, 110, 230, fill=COLORS["accent_orange"], outline="")
        
        # Small white circle
        canvas.create_oval(250, 40, 280, 70, fill=COLORS["white"], outline="")
        
        return canvas

    def _create_widgets(self):
        # Main grid layout (Sidebar + Content)
        self.grid_columnconfigure(0, weight=0, minsize=350)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ========== LEFT PANEL: Dark Sidebar ==========
        self.sidebar = ctk.CTkFrame(self, fg_color=COLORS["dark_bg"], corner_radius=0, width=350)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Decorative circles
        self._create_decorative_circles(self.sidebar)
        
        # Brand Name
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=30)
        
        # Load and display logo if exists
        if os.path.exists(self.banner_path):
            try:
                pil_image = Image.open(self.banner_path)
                ratio = pil_image.width / pil_image.height
                new_h = 45
                new_w = int(new_h * ratio)
                self.logo_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(new_w, new_h))
                ctk.CTkLabel(brand_frame, image=self.logo_image, text="").pack(anchor="w")
            except:
                ctk.CTkLabel(brand_frame, text="softbridge.", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLORS["white"]).pack(anchor="w")
        else:
            ctk.CTkLabel(brand_frame, text="softbridge.", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLORS["white"]).pack(anchor="w")
        
        # Tagline
        ctk.CTkLabel(
            self.sidebar, text="Professional Certificate\nAutomation Suite",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"], justify="left"
        ).pack(padx=30, pady=(10, 30), anchor="w")
        
        # Action Buttons
        self.btn_generate = ctk.CTkButton(
            self.sidebar, text="Generate Bulk",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLORS["white"], text_color=COLORS["dark_bg"], hover_color="#E0E0E0",
            corner_radius=25, height=50, width=280,
            command=self.start_generation
        )
        self.btn_generate.pack(padx=30, pady=10)
        
        # Status/Loader
        self.loader = PulseLoader(self.sidebar)
        self.loader.pack(pady=20)
        
        stats_frame = ctk.CTkFrame(self.sidebar, fg_color=COLORS["dark_secondary"], corner_radius=15)
        stats_frame.pack(fill="x", padx=30, pady=20, side="bottom")
        
        self.status_label = ctk.CTkLabel(
            stats_frame, text="Ready", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["white"]
        )
        self.status_label.pack(padx=20, pady=15)

        # ========== RIGHT PANEL: Content Area ==========
        self.content = ctk.CTkFrame(self, fg_color=COLORS["light_bg"], corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        
        # Content Grid: Row 0 (Header), Row 1 (Split Settings/Preview)
        self.content.grid_rowconfigure(0, weight=0) # Header
        self.content.grid_rowconfigure(1, weight=1) # Main body
        self.content.grid_columnconfigure(0, weight=4) # Settings
        self.content.grid_columnconfigure(1, weight=5) # Preview (slightly larger)

        # --- Header ---
        topbar = ctk.CTkFrame(self.content, fg_color=COLORS["white"], height=70, corner_radius=0)
        topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        topbar.pack_propagate(False)
        ctk.CTkLabel(topbar, text="Certificate Studio", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["text_primary"]).pack(side="left", padx=30, pady=20)

        # --- Column 1: Settings (Scrollable) ---
        settings_frame = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        settings_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        # Template Card
        tmpl_card = self._create_card(settings_frame, "🎨", "Template", "Background Image")
        tmpl_card.pack(fill="x", pady=(0, 15))
        self.entry_template = ctk.CTkEntry(tmpl_card, textvariable=self.template_path, height=40, font=ctk.CTkFont(size=12))
        self.entry_template.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(tmpl_card, text="Browse Template", command=self.browse_template, fg_color=COLORS["accent_orange"], height=35).pack(anchor="w", padx=20, pady=(0, 20))
        
        # Data Card
        data_card = self._create_card(settings_frame, "📊", "Data Source", "CSV or Excel")
        data_card.pack(fill="x", pady=(0, 15))
        self.entry_data = ctk.CTkEntry(data_card, textvariable=self.data_path, height=40, font=ctk.CTkFont(size=12))
        self.entry_data.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(data_card, text="Browse Data", command=self.browse_data, fg_color=COLORS["accent_teal"], height=35).pack(anchor="w", padx=20, pady=(0, 20))

        # Output Card
        out_card = self._create_card(settings_frame, "📁", "Export To", "Destination Folder")
        out_card.pack(fill="x", pady=(0, 15))
        self.entry_output = ctk.CTkEntry(out_card, textvariable=self.output_dir, height=40, font=ctk.CTkFont(size=12))
        self.entry_output.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(out_card, text="Browse Folder", command=self.browse_output, fg_color=COLORS["accent_gold"], height=35).pack(anchor="w", padx=20, pady=(0, 20))

        # Positioning Card
        pos_card = self._create_card(settings_frame, "📐", "Layout", "Adjust Vertical Position")
        pos_card.pack(fill="x", pady=(0, 15))
        
        s_frame = ctk.CTkFrame(pos_card, fg_color="transparent")
        s_frame.pack(fill="x", padx=20, pady=15)
        self.slider_y = ctk.CTkSlider(s_frame, from_=0, to=100, variable=self.name_pos_y, command=self.on_slider_change, progress_color=COLORS["accent_orange"], button_color=COLORS["accent_orange"])
        self.slider_y.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.label_y_val = ctk.CTkLabel(s_frame, text="45%", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["accent_orange"])
        self.label_y_val.pack(side="right")
        
        # --- Column 2: Preview (Fixed) ---
        preview_outer = ctk.CTkFrame(self.content, fg_color=COLORS["white"], corner_radius=15)
        preview_outer.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=20)
        
        # Preview Header
        p_head = ctk.CTkFrame(preview_outer, fg_color="transparent", height=50)
        p_head.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(p_head, text="Live Preview", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkLabel(p_head, text="John Doe", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="right")
        
        # Preview Image Area
        self.preview_container = ctk.CTkFrame(preview_outer, fg_color=COLORS["light_bg"], corner_radius=10)
        self.preview_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.preview_label = ctk.CTkLabel(self.preview_container, text="Loading Preview...", text_color=COLORS["text_muted"])
        self.preview_label.pack(fill="both", expand=True)

        # Bind resize for dynamic preview
        self.preview_container.bind("<Configure>", self.on_preview_frame_resize)

    def on_slider_change(self, value):
        self.label_y_val.configure(text=f"{int(value)}%")
        self.schedule_preview_update()

    def _create_card(self, parent, icon, title, subtitle):
        card = ctk.CTkFrame(parent, fg_color=COLORS["white"], corner_radius=15)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header, text=icon, font=ctk.CTkFont(size=22)).pack(side="left")
        
        txt = ctk.CTkFrame(header, fg_color="transparent")
        txt.pack(side="left", padx=10)
        ctk.CTkLabel(txt, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(txt, text=subtitle, font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(anchor="w")
        return card

    def on_preview_frame_resize(self, event):
        if getattr(self, '_resize_job', None):
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(100, self.update_preview_layout)

    def schedule_preview_update(self):
        if self._preview_timer:
            self._preview_timer.cancel()
        self._preview_timer = threading.Timer(0.2, self.run_preview_thread)
        self._preview_timer.start()

    def run_preview_thread(self):
        tmpl = self.template_path.get()
        y_pct = self.name_pos_y.get() / 100.0
        
        if not os.path.exists(tmpl):
            return

        try:
            pil_img = generator.process_single_certificate(
                name="John Doe", 
                template_path=tmpl, 
                pos_y_pct=y_pct,
                preview_mode=True
            )
            
            if pil_img:
                self.after(0, lambda: self.display_preview(pil_img))
                
        except Exception as e:
            print(f"Preview Error: {e}")

    def display_preview(self, pil_img):
        self.latest_pil_img = pil_img
        self.update_preview_layout()

    def update_preview_layout(self):
        if not hasattr(self, 'latest_pil_img') or not self.latest_pil_img:
            return
            
        # Get container dimensions
        # self.update_idletasks() # Careful with this in resize loops, can cause recursion if not debounced.
        # But we need real size. logic handles safety.
        
        w = self.preview_container.winfo_width()
        h = self.preview_container.winfo_height()
        
        if w < 50 or h < 50: return

        # Calculate Aspect Ratio
        img_w, img_h = self.latest_pil_img.size
        ratio = img_w / img_h
        
        target_w = w - 20
        target_h = int(target_w / ratio)
        
        if target_h > h - 20:
            target_h = h - 20
            target_w = int(target_h * ratio)
            
        if target_w <= 0 or target_h <= 0: return

        try:
            pil_resized = self.latest_pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_resized, dark_image=pil_resized, size=(target_w, target_h))
            self.preview_label.configure(image=ctk_img, text="")
            self.preview_label.image = ctk_img
        except Exception as e:
            print(f"Resize error: {e}")

    def on_resize(self, event):
        # Optional: trigger update if we want preview to resize when main window resizes? 
        # Not needed since preview has its own window now.
        pass

    def browse_template(self):
        filename = filedialog.askopenfilename(
            title="Select Certificate Template",
            filetypes=[("Images", "*.png *.jpg *.jpeg")]
        )
        if filename:
            self.template_path.set(filename)
            self.schedule_preview_update()

    def browse_data(self):
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("Excel/CSV", "*.csv *.xlsx *.xls")]
        )
        if filename:
            self.data_path.set(filename)

    def browse_output(self):
        dirname = filedialog.askdirectory(title="Select Output Folder")
        if dirname:
            self.output_dir.set(dirname)

    def start_generation(self):
        data_file = self.data_path.get()
        if not data_file:
            messagebox.showwarning(
                "Missing Data File",
                "Please select an Excel or CSV file containing names."
            )
            return

        out_dir = self.output_dir.get()
        tmpl = self.template_path.get()
        y_pct = self.name_pos_y.get() / 100.0

        self.btn_generate.configure(state="disabled", text="...")
        self.loader.start()
        self.status_label.configure(text="Generating...")
        
        thread = threading.Thread(
            target=self.run_generator,
            args=(data_file, out_dir, tmpl, y_pct)
        )
        thread.start()

    def run_generator(self, data_file, out_dir, tmpl, y_pct):
        try:
            results = generator.generate_bulk(
                input_path=data_file,
                output_dir=out_dir,
                template_path=tmpl,
                pos_y_pct=y_pct
            )
            success_count = len([r for r in results if r])
            
            self.after(0, lambda: self.status_label.configure(text=f"{success_count} certificates"))
            self.after(0, lambda: self.loader.stop())
            self.after(0, lambda: self.btn_generate.configure(state="normal", text="Generate"))
            self.after(0, lambda: messagebox.showinfo(
                "Success! 🎉",
                f"Generated {success_count} certificates!\n\nSaved in: {out_dir}"
            ))
            
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.status_label.configure(text="Error"))
            self.after(0, lambda: self.loader.stop())
            self.after(0, lambda: self.btn_generate.configure(state="normal", text="Generate"))
            self.after(0, lambda: messagebox.showerror("Error", error_msg))

if __name__ == "__main__":
    app = CertificateApp()
    app.mainloop()
