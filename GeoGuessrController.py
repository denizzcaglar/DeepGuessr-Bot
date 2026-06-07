import random
import math

class GeoGuessrController:
    def __init__(self, page):
        self.page = page
        self.game_state = {}
        self.page.on("response", self._handle_api)


    def _handle_api(self, response):
        if "/api/v3/games" in response.url:
            try: self.game_state = response.json()
            except: pass

    def get_current_round_metadata(self):
        if not self.game_state or "rounds" not in self.game_state: return None
        latest = self.game_state["rounds"][-1]
        return {
            "lat": latest.get("lat"),
            "lng": latest.get("lng"),
            "panoId": latest.get("panoId"),
            "country_code": latest.get("streakLocationCode", "unknown")
        }

    def start_new_world_game(self):
        self.game_state = {}
        self.page.goto("https://www.geoguessr.com/maps/world")
        self.page.get_by_role("button", name="No Move").click()
        self.page.wait_for_timeout(200) 
        self.page.get_by_role("button", name="Play", exact=True).click()

    def wait_for_game_start(self):
        self.page.wait_for_url("**/game/**", timeout=30000)
        for _ in range(20):
            if self.game_state and "rounds" in self.game_state: break
            self.page.wait_for_timeout(200)
        self.page.wait_for_timeout(3000)

    def random_look_around(self):
        val = random.uniform(-2.0, 2.0)
        duration, key = abs(val), ("ArrowLeft" if val < 0 else "ArrowRight")
        print(f"Rotating {key} for {duration:.2f}s...")
        try:
            canvas = self.page.locator("canvas.widget-scene-canvas").first
            canvas.click()
            self.page.keyboard.down(key)
            self.page.wait_for_timeout(int(duration * 1000))
            self.page.keyboard.up(key)
        except: pass

    def take_screenshot(self, save_path):
        css_injection = """
            .game_topHud__P_g7z, 
            .game_controls__xgq6p, 
            .game_status___YFni, 
            .guess-map_guessMap__IP8n_, 
            .game-reactions_root__TSjX_ { 
                display: none !important; 
            }
        """
        self.page.add_style_tag(content=css_injection)
        self.page.screenshot(path=save_path)


    def close_map_data_dialog(self):
        try:
            close_btn = self.page.locator('dialog[aria-label="Map Data"] button[aria-label="Close dialog"]')
            if close_btn.is_visible():
                close_btn.click()
                self.page.wait_for_timeout(100)
        except:
            pass

    def latlon_to_pixel(self, lat, lon, box):
        import coordinates
        return coordinates.latlon_to_pixel(self, lat, lon, box)

    def calibrate_map(self):
        import coordinates
        coordinates.calibrate_map(self)

    def random_lat_lon(self):
        import coordinates
        return coordinates.random_lat_lon()

    def guess_random_location(self):
        try:
            lat, lon = self.random_lat_lon()
            self.guess_location(lat, lon)
        except Exception as e:
            print(f"DEBUG: Visual Guess Error: {e}")

    def guess_random_location_api(self):
        try:
            lat, lon = self.random_lat_lon()
            self.guess_api(lat, lon)
        except Exception as e:
            print(f"DEBUG: API Guess Error: {e}")

    def guess_api(self, lat, lon):
        game_token = self.game_state.get('token')
        if not game_token: return
        print(f"API Guessing at lat={lat:.2f}, lon={lon:.2f}")
        try:
            self.page.evaluate(f"""
                fetch('https://www.geoguessr.com/api/v3/games/{game_token}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ 
                        lat: {lat}, 
                        lng: {lon}, 
                        timedOut: false,
                        token: '{game_token}'
                    }})
                }})
            """)
            self.page.wait_for_timeout(1000)
        except Exception as e:
            print(f"DEBUG: API POST Error: {e}")

    def guess_location(self, lat, lon):
        try:
            print(f"Guessing at lat={lat:.2f}, lon={lon:.2f}")
            
            self.close_map_data_dialog()
            
            guess_map = self.page.locator('[data-qa="guess-map-canvas"]')
            # Hover first
            guess_map.hover()
            self.page.wait_for_timeout(800)  # Wait for map to fully expand
            
            # Get box AFTER expansion
            box = guess_map.bounding_box()
            print(f"Box after hover: w={box['width']} h={box['height']}")
        
            if box:
                pos = self.latlon_to_pixel(lat, lon, box)
                pos["x"] = max(5, min(pos["x"], box["width"] - 5))
                pos["y"] = max(5, min(pos["y"], box["height"] - 5))
                print(f"Clicking at: {pos}")
                self.page.mouse.click(box["x"] + pos["x"], box["y"] + pos["y"])
        
            self.page.wait_for_timeout(500)
            btn = self.page.locator('[data-qa="perform-guess"]:not([disabled])')
            btn.wait_for(state="visible", timeout=5000)
            btn.click()
        
            print("Showing round results...")
            self.page.wait_for_timeout(3000)

        except Exception as e:
            print(f"DEBUG: Visual Guess Error: {e}")

    def next_round(self):
        try:
            self.page.reload()
            self.page.wait_for_timeout(1000)
            self.page.wait_for_url("**/game/**", timeout=10000)
            return True
        except:
            return False
