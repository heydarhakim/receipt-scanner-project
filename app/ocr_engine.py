import easyocr
import cv2
import numpy as np

# Initialize the reader once to load PyTorch model into memory
# 'gpu=False' if you don't have CUDA, 'gpu=True' if you do.
reader = easyocr.Reader(['id', 'en'], gpu=False)

def preprocess_image(image_path):
    """
    Enhances image for OCR: Grayscale -> Thresholding -> Denoising
    """
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply simple thresholding to binarize the image
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Optional: Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    return denoised

def extract_text(image_path):
    """
    Runs the pipeline: Preprocess -> PyTorch Inference -> Raw Text List
    """
    # Preprocess
    processed_img = preprocess_image(image_path)
    
    # Run Inference
    # detail=0 returns just the list of text strings
    results = reader.readtext(processed_img, detail=0, paragraph=False)
    
    return results