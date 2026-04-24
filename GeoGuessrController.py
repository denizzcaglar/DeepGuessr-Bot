import random
import math

class GeoGuessrController:
    def __init__(self, page):
        self.page = page
        self.game_state = {}
        self.page.on("response", self._handle_api)
        self.LAND_REGIONS = [
            # Europe
            (35, 70, -10, 40),
            # Russia / Central Asia
            (50, 70, 40, 140),
            # East Asia
            (20, 50, 100, 145),
            # South / Southeast Asia
            (0, 30, 65, 110),
            # Sub-Saharan Africa
            (-35, 15, 10, 50),
            # North Africa / Middle East
            (15, 38, -10, 60),
            # North America
            (25, 70, -165, -52),
            # Central America / Caribbean
            (8, 25, -92, -60),
            # South America
            (-55, 12, -82, -34),
            # Australia
            (-43, -10, 113, 154),
            # New Zealand
            (-47, -34, 166, 178),
            # Japan
            (31, 45, 130, 145),
            # UK / Ireland
            (51, 59, -8, 2),
        ]

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
        self.page.wait_for_timeout(200) # Fast sync
        self.page.get_by_role("button", name="Play", exact=True).click()

    def wait_for_game_start(self):
        self.page.wait_for_url("**/game/**", timeout=30000)
        for _ in range(20):
            if self.game_state and "rounds" in self.game_state: break
            self.page.wait_for_timeout(200)
        self.page.wait_for_timeout(2000) # Reverted to 2.0s (the original stable value)

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
        # Two ground truth points from manual calibration:
        # Lagos (6.5, 3.4) → pixel (191, 131)
        # Istanbul (41, 28.97) → pixel (220, 80)

        # Raw Mercator fractions
        def merc(lat_deg):
            r = math.radians(lat_deg)
            return math.log(math.tan(math.pi / 4 + r / 2))

        # Compute raw fracs for our two known points
        lagos_lat, lagos_lon = 6.5, 3.4
        istanbul_lat, istanbul_lon = 41.0, 28.97

        def raw_fracs(lat, lon):
            x = (lon + 180) / 360
            lat_max, lat_min = math.radians(85.051), math.radians(-85.051)
            merc_max = merc(math.degrees(lat_max))
            merc_min = merc(math.degrees(lat_min))
            y = 1 - (merc(lat) - merc_min) / (merc_max - merc_min)
            return x, y

        lx, ly = raw_fracs(lagos_lat, lagos_lon)
        ix, iy = raw_fracs(istanbul_lat, istanbul_lon)

        # Known pixel positions (as fractions of box)
        lx_px, ly_px = 195 / box["width"], 141 / box["height"]
        ix_px, iy_px = 220 / box["width"], 80 / box["height"]

        # Fit linear transform: pixel_frac = a * raw_frac + b
        # Using two points to solve for a and b on each axis
        ax = (ix_px - lx_px) / (ix - lx)
        bx = lx_px - ax * lx
        ay = (iy_px - ly_px) / (iy - ly)
        by = ly_px - ay * ly

        x_raw, y_raw = raw_fracs(lat, lon)
        x_frac = ax * x_raw + bx
        y_frac = ay * y_raw + by

        return {
            "x": box["width"] * x_frac,
            "y": box["height"] * y_frac
        }

    def random_lat_lon(self):
        region = random.choice(self.LAND_REGIONS)
        lat = random.uniform(region[0], region[1])
        lon = random.uniform(region[2], region[3])
        return lat, lon

    def guess_random_location(self):
        try:
            lat, lon = self.random_lat_lon()
            print(f"Guessing at lat={lat:.2f}, lon={lon:.2f}")
            
            game_id = self.page.url.split("/game/")[-1]
            
            status = self.page.evaluate(f"""
                async () => {{
                    const response = await fetch('/api/v3/games/{game_id}', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            token: '{game_id}',
                            lat: {lat},
                            lng: {lon},
                            timedOut: false,
                            timedOutWithGuess: false
                        }})
                    }});
                    return response.status;
                }}
            """)
            print(f"API guess status: {status}")
            self.page.wait_for_timeout(200) # Reduced from 1000ms

        except Exception as e:
            print(f"DEBUG: Visual Guess Error: {e}")

    def next_round(self):
        try:
            self.page.reload()
            self.page.wait_for_timeout(500) # Reduced from 2000ms
            self.page.wait_for_url("**/game/**", timeout=10000)
            return True
        except:
            return False

