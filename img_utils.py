import cv2
import numpy as np
import os
import pandas as pd

def is_mostly_black(img, threshold=4, black_ratio=0.8):
    """Checks if an image is mostly dark/zeroed out."""
    # Convert to grayscale if it's color
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
        
    black_pixels = np.sum(gray < threshold)
    total_pixels = gray.size
    return (black_pixels / total_pixels) >= black_ratio

def process_and_save_image(image_path, output_path, size=(640, 640)):
    """Resizes and filters image. Returns True if saved, False if rejected."""
    img = cv2.imread(image_path)
    if img is None:
        return False
        
    # 1. Check if mostly black BEFORE resizing (faster)
    if is_mostly_black(img):
        if os.path.exists(image_path):
            os.remove(image_path)
        return False
        
    # 2. Resize using INTER_AREA as requested
    resized = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    
    # 3. Save to output path (can be same as image_path)
    cv2.imwrite(output_path, resized)
    return True

def cleanup_existing_data(data_dir="data"):
    """One-time cleanup for existing images and CSV."""
    images_dir = os.path.join(data_dir, "images")
    csv_path = os.path.join(data_dir, "image_metadata.csv")
    
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    valid_indices = []
    
    print(f"Cleaning up {len(df)} existing entries...")
    
    for idx, row in df.iterrows():
        img_name = row['image_name']
        img_path = os.path.join(images_dir, img_name)
        
        if os.path.exists(img_path):
            # Process (resize + check black)
            is_valid = process_and_save_image(img_path, img_path)
            if is_valid:
                valid_indices.append(idx)
            else:
                print(f"Removed black/invalid image: {img_name}")
        else:
            print(f"Image not found, removing from CSV: {img_name}")

    # Save cleaned CSV
    new_df = df.iloc[valid_indices]
    new_df.to_csv(csv_path, index=False)
    print(f"Cleanup complete. {len(new_df)} valid images remaining.")
