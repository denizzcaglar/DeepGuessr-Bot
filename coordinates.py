import math
import json
import random

LAND_REGIONS = [
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

def random_lat_lon():
    region = random.choice(LAND_REGIONS)
    lat = random.uniform(region[0], region[1])
    lon = random.uniform(region[2], region[3])
    return lat, lon

def calibrate_map(self):
    guess_map = self.page.locator('[data-qa="guess-map-canvas"]')
    guess_map.hover()
    self.page.wait_for_timeout(800)
    box = guess_map.bounding_box()
    print(f"Box: {box}")

    self.page.evaluate("""
        window._clicks = [];
        window._mouseX = 0;
        window._mouseY = 0;
        window.addEventListener('mousemove', (e) => {
            window._mouseX = e.clientX;
            window._mouseY = e.clientY;
        });
        window.addEventListener('keydown', (e) => {
            if (e.key === 'c' || e.key === 'C') {
                const b = document.querySelector('[data-qa="guess-map-canvas"]').getBoundingClientRect();
                window._clicks.push({ x: window._mouseX - b.left, y: window._mouseY - b.top });
            }
        });
    """)

    import time
    print("Hover over the 3 corners of the map and press 'c' on your keyboard for each:")
    print("1. TOP-LEFT corner (should be near Alaska/Greenland)")
    print("2. TOP-RIGHT corner (should be near Russia far east)")
    print("3. BOTTOM-LEFT corner (should be near South America bottom)")

    while True:
        clicks = self.page.evaluate("window._clicks")
        if len(clicks) >= 3:
            break
        time.sleep(0.5)

    clicks = self.page.evaluate("window._clicks")
    print(f"Clicks: {clicks}")

    # The 3 corners in pixel space
    tl = clicks[0]  # top-left pixel
    tr = clicks[1]  # top-right pixel
    bl = clicks[2]  # bottom-left pixel

    # Store calibration: map pixel extent
    self.cal_left_x = tl['x']
    self.cal_right_x = tr['x']
    self.cal_top_y = tl['y']
    self.cal_bot_y = bl['y']

    print(f"Calibration: x=[{self.cal_left_x}, {self.cal_right_x}] y=[{self.cal_top_y}, {self.cal_bot_y}]")

def latlon_to_pixel(self, lat, lon, box):
    TILE_SIZE = 256
    ZOOM = 1
    MAP_CENTER_LAT = 11.901183
    MAP_CENTER_LON = 9.33603

    world_size = TILE_SIZE * (2 ** ZOOM)

    def merc(lat_deg):
        r = math.radians(lat_deg)
        return math.log(math.tan(math.pi / 4 + r / 2))

    world_x = (lon + 180) / 360 * world_size
    world_y = (math.pi - merc(lat)) / (2 * math.pi) * world_size

    center_x = (MAP_CENTER_LON + 180) / 360 * world_size
    center_y = (math.pi - merc(MAP_CENTER_LAT)) / (2 * math.pi) * world_size

    x = box["width"] / 2 + (world_x - center_x)
    y = box["height"] / 2 + (world_y - center_y)

    return {"x": x, "y": y}
