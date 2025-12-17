import easyocr
import os

# Initialize reader once to load PyTorch model into memory
# 'id' = Indonesian, 'en' = English
reader = easyocr.Reader(['id', 'en'], gpu=False) # Set gpu=True if CUDA is available

def process_image(image_path):
    """
    Runs PyTorch-based OCR on the image.
    Returns a list of text lines.
    """
    try:
        # detail=0 returns just the text list. 
        # For complex layouts, detail=1 gives coordinates (bounding boxes).
        result = reader.readtext(image_path, detail=0, paragraph=False)
        return result
    except Exception as e:
        print(f"OCR Error: {e}")
        return []