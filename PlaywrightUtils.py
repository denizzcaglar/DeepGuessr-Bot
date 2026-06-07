import os
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

class PlaywrightUtils:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    def start_browser_geoguessr(self):
        import json
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        vp_w = config["size"]["width"]
        vp_h = config["size"]["height"]
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context(
            viewport={"width": vp_w, "height": vp_h},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        cookie_val = os.getenv("GEOGUESSR_COOKIE")
        if cookie_val:
            self.context.add_cookies([{"name": "_ncfa", "value": cookie_val, "domain": "www.geoguessr.com", "path": "/"}])
            
        return self.context

    def create_stealth_page(self):
        page = self.context.new_page()
        Stealth().apply_stealth_sync(page)
        return page
        
    def close_browser(self):
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
