from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
import sys

def get_base_path():
    """Returns the base path for resources, handling both dev and PyInstaller modes."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

ASSETS_DIR = os.path.join(get_base_path(), "assets")
DEFAULT_TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template.png")
DEFAULT_FONT_PATH = "arial.ttf" # os.path.join(ASSETS_DIR, "GreatVibes-Regular.ttf")

def process_single_certificate(name, output_dir="certificates", template_path=None, font_path=None, pos_y_pct=0.45, color="#000000", preview_mode=False):
    if template_path is None:
        template_path = DEFAULT_TEMPLATE_PATH
    if font_path is None:
        font_path = DEFAULT_FONT_PATH
        
    display_name = str(name).strip()
    
    if not preview_mode:
        safe_name = str(name).strip().replace(" ", "_")
        person_folder = os.path.join(output_dir, safe_name)
        os.makedirs(person_folder, exist_ok=True)
    
    # 1. Prepare the Template
    try:
        template = Image.open(template_path).convert("RGB")
    except Exception as e:
        print(f"Error loading template: {e}")
        return None
    
    # 2. Define Real A4 Landscape Dimensions (300 DPI for high quality)
    # A4 landscape is 3508 x 2480 pixels at 300 DPI
    a4_width, a4_height = 3508, 2480
    img = template.resize((a4_width, a4_height), Image.Resampling.LANCZOS)
    
    # For preview, we can perhaps use a smaller image if performance is bad? 
    # But user wants accurate positioning, so let's stick to ratio.
    # Actually, scaling down for preview generation is much faster and enough for UI.
    # But to ensure pixel-perfect relative positioning, let's keep logic same or consistent.
    # Let's optimize: if preview_mode, maybe process at 50% scale or just return full and let UI resize.
    # Returning full is fine, modern CPUs handle 8MP images okay. 
    # But resizing BEFORE drawing text is faster if we only show a thumbnail.
    # However, font size calcs depend on resolution.
    # Let's keep full res for accuracy of logic, UI thread can resize for display.

    draw = ImageDraw.Draw(img)
    
    # 3. Dynamic Font Scaling for Long Names
    max_width = img.width * 0.75
    font_size = 250  # Increased base size for high-res image
    
    # Try to load font, with fallback to Arial
    try:
        # Default to passed font_path (GreatVibes)
        name_font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"Error loading custom font: {e}")
        # Fallback to Arial
        try:
            name_font = ImageFont.truetype("arial.ttf", font_size)
        except:
            name_font = ImageFont.load_default()

    # Reduce font size if text is too wide
    while draw.textlength(display_name, font=name_font) > max_width and font_size > 50:
        font_size -= 10
        try:
            name_font = ImageFont.truetype(font_path, font_size)
        except:
            try:
                name_font = ImageFont.truetype("arial.ttf", font_size)
            except:
                name_font = ImageFont.load_default()
    
    # 4. Perfect Centering using Bounding Box
    bbox = draw.textbbox((0, 0), display_name, font=name_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    name_x = (img.width - text_width) / 2
    # Vertically positioned based on percentage
    name_y = (img.height * pos_y_pct) - (text_height / 2)
    
    draw.text((name_x, name_y), display_name, fill=color, font=name_font)
    
    if preview_mode:
        return img
    
    # 5. Save Outputs
    png_path = os.path.join(person_folder, f"{safe_name}.png")
    pdf_path = os.path.join(person_folder, f"{safe_name}.pdf")
    img.save(png_path, quality=95)
    
    # 6. Generate PDF in Real Landscape A4 Size
    c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    width_pts, height_pts = landscape(A4)
    c.drawImage(png_path, 0, 0, width=width_pts, height=height_pts)
    c.showPage()
    c.save()
    
    return {"name": display_name, "folder": person_folder, "png": png_path, "pdf": pdf_path}

def generate_bulk(input_path, output_dir="certificates", template_path=None, font_path=None, pos_y_pct=0.45):
    # Determine loader based on extension
    if input_path.endswith('.csv'):
        data = pd.read_csv(input_path)
    elif input_path.endswith('.xlsx') or input_path.endswith('.xls'):
        data = pd.read_excel(input_path)
    else:
        raise ValueError("Unsupported file format. Please use CSV or Excel.")

    results = []
    # Assume the column is 'name' - we might want to make this robust later 
    # but for now we look for the first column if 'name' doesn't exist?
    # Or just assume 'name' column exists as per data/names.csv
    
    cols = [c.lower() for c in data.columns]
    name_col = None
    if 'name' in cols:
        name_col = data.columns[cols.index('name')]
    else:
        # Fallback: use first column
        name_col = data.columns[0]
        
    for name in data[name_col]:
        if pd.isna(name): continue
        results.append(process_single_certificate(
            name, 
            output_dir=output_dir,
            template_path=template_path,
            font_path=font_path,
            pos_y_pct=pos_y_pct
        ))
    return results