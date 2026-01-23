
from PIL import Image, ImageDraw, ImageFont
import os

base_path = os.getcwd()
assets_dir = os.path.join(base_path, "assets")
font_path = os.path.join(assets_dir, "GreatVibes-Regular.ttf")

try:
    font = ImageFont.truetype(font_path, 250)
    print("Font loaded OK")
    
    img = Image.new("RGB", (3508, 2480), "white")
    draw = ImageDraw.Draw(img)
    
    text = "John Doe"
    bbox = draw.textbbox((0, 0), text, font=font)
    print(f"Bbox: {bbox}")
    
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    print(f"Width: {width}, Height: {height}")
    
except Exception as e:
    print(f"Error: {e}")
