"""
Downloads one reference image per haircut style from Wikimedia Commons.
Fully public, no API key required.
Usage: python utils/download_images.py
"""

import urllib.request
import os
import time

OUTPUT_DIR = "assets/images"

# Direct Wikimedia Commons image URLs — stable, public domain / CC licensed
STYLES = {
    "crew_cut":          "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Crew_cut.jpg/400px-Crew_cut.jpg",
    "buzz_cut":          "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Buzz_cut.jpg/400px-Buzz_cut.jpg",
    "undercut":          "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Undercut_hair.jpg/400px-Undercut_hair.jpg",
    "pompadour":         "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Pompadour_hairstyle.jpg/400px-Pompadour_hairstyle.jpg",
    "afro":              "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Afro_hair.jpg/400px-Afro_hair.jpg",
    "pixie_cut":         "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Pixie_cut.jpg/400px-Pixie_cut.jpg",
    "bob":               "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Bob_haircut.jpg/400px-Bob_haircut.jpg",
    "dreadlocks":        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Dreadlocks.jpg/400px-Dreadlocks.jpg",
    "cornrows":          "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Cornrow_braids.jpg/400px-Cornrow_braids.jpg",
    "mohawk":            "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Mohawk_hairstyle.jpg/400px-Mohawk_hairstyle.jpg",
}

# Fallback: use the Wikimedia Commons API to search for images
SEARCH_FALLBACK = {
    "quiff":             "quiff hairstyle",
    "textured_crop":     "textured crop haircut",
    "slick_back":        "slick back hair",
    "side_part":         "side part hairstyle",
    "faux_hawk":         "faux hawk haircut",
    "curtain_bangs":     "curtain bangs hair",
    "wolf_cut":          "wolf cut hairstyle",
    "shag_cut":          "shag haircut",
    "long_layers":       "long layered hairstyle",
    "lob":               "lob long bob haircut",
    "tapered_cut":       "tapered natural hair",
    "french_crop":       "french crop haircut",
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

headers = {
    "User-Agent": "HaircutAI-Project/1.0 (educational project; contact via GitHub)"
}

def download(url: str, out_path: str, label: str) -> bool:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        if len(data) < 3000:
            print(f"  [warn] {label}: too small ({len(data)} bytes)")
            return False
        with open(out_path, "wb") as f:
            f.write(data)
        print(f"  [ok]   {label}.jpg  ({len(data)//1024} KB)")
        return True
    except Exception as e:
        print(f"  [fail] {label}: {e}")
        return False


def wikimedia_search(query: str) -> str | None:
    """Search Wikimedia Commons and return the URL of the first image result."""
    import json
    encoded = urllib.parse.quote(query)
    api = (
        f"https://commons.wikimedia.org/w/api.php"
        f"?action=query&list=search&srsearch={encoded}+filetype:bitmap"
        f"&srnamespace=6&srlimit=1&format=json"
    )
    try:
        req = urllib.request.Request(api, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        results = data.get("query", {}).get("search", [])
        if not results:
            return None
        title = results[0]["title"]  # e.g. "File:Quiff_hairstyle.jpg"
        # Get the actual image URL
        title_encoded = urllib.parse.quote(title)
        info_api = (
            f"https://commons.wikimedia.org/w/api.php"
            f"?action=query&titles={title_encoded}&prop=imageinfo"
            f"&iiprop=url&iiurlwidth=400&format=json"
        )
        req2 = urllib.request.Request(info_api, headers=headers)
        with urllib.request.urlopen(req2, timeout=10) as r2:
            info = json.loads(r2.read())
        pages = info.get("query", {}).get("pages", {})
        for page in pages.values():
            ii = page.get("imageinfo", [])
            if ii:
                return ii[0].get("thumburl") or ii[0].get("url")
    except Exception as e:
        print(f"    search error: {e}")
    return None


import urllib.parse

success = 0
failed = []

print("=== Downloading from direct URLs ===")
for style, url in STYLES.items():
    out_path = os.path.join(OUTPUT_DIR, f"{style}.jpg")
    if os.path.exists(out_path):
        print(f"  [skip] {style}.jpg already exists")
        success += 1
        continue
    if download(url, out_path, style):
        success += 1
    else:
        failed.append(style)
    time.sleep(0.5)

print("\n=== Searching Wikimedia Commons for remaining styles ===")
for style, query in SEARCH_FALLBACK.items():
    out_path = os.path.join(OUTPUT_DIR, f"{style}.jpg")
    if os.path.exists(out_path):
        print(f"  [skip] {style}.jpg already exists")
        success += 1
        continue
    print(f"  searching: {query}...")
    img_url = wikimedia_search(query)
    if img_url:
        if download(img_url, out_path, style):
            success += 1
        else:
            failed.append(style)
    else:
        print(f"  [fail] {style}: no results found")
        failed.append(style)
    time.sleep(0.8)

total = len(STYLES) + len(SEARCH_FALLBACK)
print(f"\nDone: {success}/{total} downloaded to {OUTPUT_DIR}/")
if failed:
    print(f"Failed ({len(failed)}): {', '.join(failed)}")
    print("\nFor failed styles, manually download from:")
    print("  https://unsplash.com  or  https://www.pexels.com")
    print(f"  Save as assets/images/<style_name>.jpg")
