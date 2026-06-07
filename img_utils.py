import cv2
import numpy as np
import os
import pandas as pd
import json

def load_config(config_path="config.json"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file missing: {config_path}")
    with open(config_path, 'r') as f:
        return json.load(f)


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

def process_and_save_image(image_path, output_path):
    """Resizes and filters image. Returns True if saved, False if rejected."""
    img = cv2.imread(image_path)
    if img is None:
        return False
        
    if is_mostly_black(img):
        if os.path.exists(image_path):
            os.remove(image_path)
        return False
        
    config = load_config()
    try:
        tw = config["size"]["width"]
        th = config["size"]["height"]
    except KeyError as e:
        raise KeyError(f"Invalid config.json format. Missing required key: {e}")
    
    ih, iw = img.shape[:2]
    tr = tw / th
    ir = iw / ih
    
    cropped = False
    if ir > tr:
        # Image is wider, crop width
        new_w = int(ih * tr)
        start_x = (iw - new_w) // 2
        img = img[:, start_x:start_x+new_w]
        cropped = True
    elif ir < tr:
        # Image is taller, crop height
        new_h = int(iw / tr)
        start_y = (ih - new_h) // 2
        img = img[start_y:start_y+new_h, :]
        cropped = True
        
    resized = False
    # Skip resize if the image is already the target size
    if img.shape[1] != tw or img.shape[0] != th:
        img = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
        resized = True
        
    # Only rewrite to disk if we modified the image or are saving to a new path
    if cropped or resized or image_path != output_path:
        cv2.imwrite(output_path, img)
        
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
