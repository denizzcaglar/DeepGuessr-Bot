import os
import csv
import msvcrt
from dotenv import load_dotenv
from PlaywrightUtils import PlaywrightUtils
from GeoGuessrController import GeoGuessrController

import img_utils

load_dotenv()
DATA_DIR, IMAGES_DIR, METADATA_FILE = "data", "data/images", "data/image_metadata.csv"
ROTATE = False  # Set to True if you want random rotations

def get_existing_panos():
    if not os.path.exists(METADATA_FILE): return []
    with open(METADATA_FILE, mode='r', encoding='utf-8') as f:
        return [row['pano_id'] for row in csv.DictReader(f) if 'pano_id' in row]

def main():
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    existing_panos = get_existing_panos()
    stop_requested = False
    
    print("Bot started. Press 's' IN THIS TERMINAL to stop gracefully, or Ctrl+C to abort.")
    
    pw = PlaywrightUtils()
    pw.start_browser_geoguessr()
    page = pw.create_stealth_page()
    ctrl = GeoGuessrController(page)
    
    try:
        while not stop_requested:
            # Check for terminal keypress
            if msvcrt.kbhit():
                if msvcrt.getch().decode('utf-8').lower() == 's':
                    print("\nStop requested. Finishing current round...")
                    stop_requested = True

            if stop_requested: break
            
            print("\nStarting new game...")
            ctrl.start_new_world_game()
            
            for r in range(1, 6):
                if msvcrt.kbhit():
                    if msvcrt.getch().decode('utf-8').lower() == 's':
                        print("\nStop requested. Finishing current round...")
                        stop_requested = True

                if stop_requested: break
                print(f"Round {r}/5...")
                ctrl.wait_for_game_start()
                
                meta = ctrl.get_current_round_metadata()
                if meta and meta['panoId'] not in existing_panos:
                    if ROTATE:
                        ctrl.random_look_around()
                    img_name = f"pano_{meta['panoId']}.png"
                    path = os.path.join(IMAGES_DIR, img_name)
                    ctrl.take_screenshot(path)
                    
                    # PROCESS & FILTER
                    if img_utils.process_and_save_image(path, path):
                        header = not os.path.isfile(METADATA_FILE)
                        with open(METADATA_FILE, mode='a', newline='', encoding='utf-8') as f:
                            w = csv.writer(f)
                            if header: w.writerow(["image_name", "lat", "lng", "country_code", "pano_id"])
                            w.writerow([img_name, meta['lat'], meta['lng'], meta['country_code'], meta['panoId']])
                        existing_panos.append(meta['panoId'])
                    else:
                        print(f"Skipping round: Image was mostly black/invalid.")
                    
                    # Scene is already loaded, minimal pause before guessing
                    ctrl.page.wait_for_timeout(200)
                
                ctrl.guess_random_location()
                if r < 5 and not ctrl.next_round(): break
                
    finally:
        pw.close_browser()

if __name__ == "__main__":
    main()
