import os
from dotenv import load_dotenv
from PlaywrightUtils import PlaywrightUtils
from GeoGuessrController import GeoGuessrController

load_dotenv()

pw = PlaywrightUtils()
pw.start_browser_geoguessr()
page = pw.create_stealth_page()
ctrl = GeoGuessrController(page)

ctrl.start_new_world_game()
ctrl.wait_for_game_start()

guess_map = page.locator('[data-qa="guess-map-canvas"]')
guess_map.hover()
page.wait_for_timeout(1500)

box = guess_map.bounding_box()
print(f"Bounding box: {box}")

# Try to access Google Maps instance
queries = [
    # Get zoom from the map object
    """() => {
        const frames = document.querySelectorAll('iframe');
        for (const f of frames) {
            try { if (f.contentWindow.google) return 'found google in iframe'; } catch(e) {}
        }
        return 'no iframe google';
    }""",

    # Check for map tiles to determine zoom
    """() => {
        const tiles = document.querySelectorAll('img[src*="maps"]');
        const srcs = [];
        tiles.forEach(t => srcs.push(t.src));
        return srcs.slice(0, 5);
    }""",

    # Look for any Google Maps related global variables
    """() => {
        const keys = Object.keys(window).filter(k => 
            k.toLowerCase().includes('map') || k.toLowerCase().includes('google')
        );
        return keys;
    }""",

    # Check if google.maps exists and what's available
    """() => {
        if (typeof google === 'undefined') return 'no google object';
        const keys = Object.keys(google.maps || {});
        return { maps_keys: keys.slice(0, 20) };
    }""",

    # Try to find map div and extract zoom from URL or data
    """() => {
        const mapDiv = document.querySelector('[data-qa="guess-map-canvas"]');
        if (!mapDiv) return 'no map div';
        return {
            innerHTML_length: mapDiv.innerHTML.length,
            children: mapDiv.children.length,
            childTags: Array.from(mapDiv.children).map(c => c.tagName + '.' + c.className).slice(0, 10)
        };
    }""",

    # Look for links with map coordinates
    """() => {
        const links = document.querySelectorAll('a[href*="maps"]');
        return Array.from(links).map(a => a.href).slice(0, 5);
    }""",

    # Check for any data attributes on the map or its parents
    """() => {
        const el = document.querySelector('[data-qa="guess-map-canvas"]');
        if (!el) return null;
        const attrs = {};
        for (const attr of el.attributes) {
            attrs[attr.name] = attr.value;
        }
        return attrs;
    }""",

    # Try to find map instance through DOM traversal
    """() => {
        const divs = document.querySelectorAll('div[style*="position"]');
        const mapRelated = [];
        divs.forEach(d => {
            if (d.querySelector('canvas') && d.closest('[data-qa="guess-map-canvas"]')) {
                mapRelated.push({
                    style: d.style.cssText.substring(0, 200),
                    className: d.className
                });
            }
        });
        return mapRelated.slice(0, 5);
    }""",
]

for i, q in enumerate(queries):
    try:
        result = page.evaluate(q)
        print(f"\nQuery {i+1}: {result}")
    except Exception as e:
        print(f"\nQuery {i+1} ERROR: {e}")

input("\nPress Enter to close...")
pw.close_browser()
