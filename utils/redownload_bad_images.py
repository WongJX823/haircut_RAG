"""
Re-downloads specific images that downloaded incorrectly.
Usage: python utils/redownload_bad_images.py
"""

import urllib.request
import urllib.parse
import json
import os
import time

OUTPUT_DIR = "assets/images"

headers = {
    "User-Agent": "HaircutAI-Project/1.0 (educational project; contact via GitHub)"
}


def wikimedia_search(query: str) -> str | None:
    """Search Wikimedia Commons and return the URL of the first image result."""
    encoded = urllib.parse.quote(query)
    api = (
        f"https://commons.wikimedia.org/w/api.php"
        f"?action=query&list=search&srsearch={encoded}+filetype:bitmap"
        f"&srnamespace=6&srlimit=5&format=json"
    )
    try:
        req = urllib.request.Request(api, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        results = data.get("query", {}).get("search", [])
        if not results:
            return None
        # Try each result until we find a good one
        for result in results:
            title = result["title"]
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
                    url = ii[0].get("thumburl") or ii[0].get("url")
                    if url:
                        return url
    except Exception as e:
        print(f"    search error: {e}")
    return None


def download(url: str, out_path: str, label: str) -> bool:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        if len(data) < 5000:
            print(f"  [warn] {label}: too small ({len(data)} bytes), likely wrong image")
            return False
        with open(out_path, "wb") as f:
            f.write(data)
        print(f"  [ok]   {label}  ({len(data)//1024} KB)")
        return True
    except Exception as e:
        print(f"  [fail] {label}: {e}")
        return False


# Images to fix with targeted search queries
TO_FIX = {
    "lob": [
        # Try direct URL first
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Lob_hairstyle.jpg/400px-Lob_hairstyle.jpg",
    ],
    "pompadour": [
        # Try direct URL for a modern male pompadour
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Elvis_Presley_1970.jpg/400px-Elvis_Presley_1970.jpg",
    ],
    "wolf_cut": [],  # Only search, no direct URL
}

SEARCH_QUERIES = {
    "lob": "lob hairstyle long bob woman salon",
    "pompadour": "pompadour hairstyle man barber modern",
    "wolf_cut": "wolf cut hairstyle woman shag layers",
}

print("=== Re-downloading problem images ===\n")

for style, direct_urls in TO_FIX.items():
    out_path = os.path.join(OUTPUT_DIR, f"{style}.jpg")
    print(f"Fixing: {style}.jpg")

    success = False

    # Try direct URLs first
    for url in direct_urls:
        print(f"  trying direct URL...")
        if download(url, out_path, style):
            success = True
            break
        time.sleep(1)

    # Fall back to search
    if not success:
        query = SEARCH_QUERIES.get(style, f"{style.replace('_', ' ')} hairstyle")
        print(f"  searching: {query}...")
        img_url = wikimedia_search(query)
        if img_url:
            if download(img_url, out_path, style):
                success = True

    if not success:
        print(f"  [FAILED] {style} — download manually from unsplash.com or pexels.com")
        print(f"           Save as: assets/images/{style}.jpg")

    time.sleep(1.5)

# Also try wolf_cut which was missing from before
style = "wolf_cut"
out_path = os.path.join(OUTPUT_DIR, f"{style}.jpg")
if not os.path.exists(out_path):
    print(f"\nDownloading missing: {style}.jpg")
    query = SEARCH_QUERIES[style]
    print(f"  searching: {query}...")
    img_url = wikimedia_search(query)
    if img_url:
        download(img_url, out_path, style)
    else:
        print(f"  [FAILED] Search returned no results")
        print(f"  Download manually: https://unsplash.com/s/photos/wolf-cut-hair")
        print(f"  Save as: assets/images/wolf_cut.jpg")

print("\nDone. Check assets/images/ for results.")
