import os
import msvcrt
import random
from dotenv import load_dotenv
from PlaywrightUtils import PlaywrightUtils
from GeoGuessrController import GeoGuessrController
from inference import predict_coordinates, init_model

load_dotenv()

def main():
    stop_requested = False
    
    print("Bot started in PLAY mode. Press 's' to stop gracefully.")
    
    print("Initializing model...")
    init_model()
    
    pw = PlaywrightUtils()
    pw.start_browser_geoguessr()
    page = pw.create_stealth_page()
    ctrl = GeoGuessrController(page)
    
    try:
        while not stop_requested:
            if msvcrt.kbhit():
                if msvcrt.getch().decode('utf-8').lower() == 's':
                    stop_requested = True

            if stop_requested: break
            
            ctrl.start_new_world_game()
            
            for r in range(1, 6):
                if msvcrt.kbhit():
                    if msvcrt.getch().decode('utf-8').lower() == 's':
                        stop_requested = True

                if stop_requested: break
                ctrl.wait_for_game_start()
                
                meta = ctrl.get_current_round_metadata()
                if meta:
                    temp_img_path = "temp_inference.png"
                    ctrl.take_screenshot(temp_img_path)
                    
                    lat, lon = predict_coordinates(temp_img_path)
                    
                    wait_time = random.uniform(2.5, 7.5)
                    print(f"Thinking for {wait_time:.1f} seconds...")
                    ctrl.page.wait_for_timeout(int(wait_time * 1000))
                    
                    ctrl.guess_location(lat, lon)
                    
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
                        
                    if r == 5:
                        print("Game finished. Waiting 10 seconds to display final results...")
                        ctrl.page.wait_for_timeout(10000)
                        
                if r < 5 and not ctrl.next_round(): break
                
    finally:
        pw.close_browser()

if __name__ == "__main__":
    main()
