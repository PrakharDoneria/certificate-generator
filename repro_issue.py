
import generator
from PIL import ImageFont
import os

print(f"Base path: {generator.get_base_path()}")
print(f"Assets dir: {generator.ASSETS_DIR}")
print(f"Font path: {generator.DEFAULT_FONT_PATH}")

if os.path.exists(generator.DEFAULT_FONT_PATH):
    print("Font file exists.")
else:
    print("Font file does NOT exist.")

try:
    font = ImageFont.truetype(generator.DEFAULT_FONT_PATH, 100)
    print("Font loaded successfully.")
except Exception as e:
    print(f"Failed to load font: {e}")

try:
    result = generator.process_single_certificate(name="John Doe", output_dir="repro_output", preview_mode=False)
    print("Certificate generated.")
except Exception as e:
    print(f"Error during generation: {e}")
