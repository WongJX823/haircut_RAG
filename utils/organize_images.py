"""
Reorganises assets/images into men/ and women/ subfolders and
downloads missing gender-specific reference images from Wikimedia Commons.
Usage: python utils/organize_images.py
"""

import urllib.request
import urllib.parse
import json
import os
import shutil
import time

BASE = "assets/images"
MEN = os.path.join(BASE, "men")
WOMEN = os.path.join(BASE, "women")

headers = {
    "User-Agent": "HaircutAI-Project/1.0 (educational project; contact via GitHub)"
}

# Existing images -> destination folder (verified visually: photo shows that gender)
MOVES = {
    "buzz_cut.jpg":      MEN,
    "crew_cut.jpg":      MEN,
    "faux_hawk.jpg":     MEN,
    "mohawk.jpg":        MEN,
    "pompadour.jpg":     MEN,
    "quiff.jpg":         MEN,
    "shag_cut.jpg":      MEN,    # photo is a male 70s shag
    "side_part.jpg":     MEN,
    "slick_back.jpg":    MEN,
    "textured_crop.jpg": MEN,
    "undercut.jpg":      MEN,
    "dreadlocks.jpg":    MEN,    # photo is a man
    "afro.jpg":          WOMEN,
    "bob.jpg":           WOMEN,
    "cornrows.jpg":      WOMEN,
    "curtain_bangs.jpg": WOMEN,
    "lob.jpg":           WOMEN,
    "long_layers.jpg":   WOMEN,
    "pixie_cut.jpg":     WOMEN,
    "tapered_cut.jpg":   WOMEN,
}

# Old french_crop.jpg is a vintage photo of a woman — wrong for the men's
# french crop style and not a women's style in the knowledge base. Remove it.
REMOVE = ["french_crop.jpg"]

# Missing images to download: (folder, filename) -> list of search queries to try
DOWNLOADS = {
    (MEN, "afro.jpg"):          ["man with afro hairstyle", "afro hair man portrait"],
    (MEN, "curtain_bangs.jpg"): ["curtain hairstyle man", "man middle part hair", "male long fringe hairstyle"],
    (MEN, "french_crop.jpg"):   ["caesar haircut man", "short fringe haircut man", "crop haircut male"],
    (MEN, "wolf_cut.jpg"):      ["modern mullet haircut man", "mullet hairstyle young man"],
    (WOMEN, "buzz_cut.jpg"):    ["woman buzz cut hair", "woman with shaved head portrait"],
    (WOMEN, "shag_cut.jpg"):    ["shag haircut woman", "layered shag hairstyle woman"],
    (WOMEN, "wolf_cut.jpg"):    ["wolf cut woman hair", "mullet hairstyle woman"],
    (WOMEN, "blunt_bob.jpg"):   ["blunt bob haircut woman", "bob haircut woman portrait"],
}


def wikimedia_candidates(query: str, limit: int = 5) -> list[str]:
    """Return candidate file titles from Wikimedia Commons search."""
    encoded = urllib.parse.quote(query)
    api = (
        f"https://commons.wikimedia.org/w/api.php"
        f"?action=query&list=search&srsearch={encoded}"
        f"&srnamespace=6&srlimit={limit}&format=json"
    )
    req = urllib.request.Request(api, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    results = data.get("query", {}).get("search", [])
    # Skip non-photo files (PDFs, DJVUs, SVGs, drawings)
    bad_ext = (".pdf", ".djvu", ".svg", ".gif", ".tif", ".tiff")
    return [
        r["title"] for r in results
        if not r["title"].lower().endswith(bad_ext)
    ]


def get_image_url(title: str) -> str | None:
    title_encoded = urllib.parse.quote(title)
    info_api = (
        f"https://commons.wikimedia.org/w/api.php"
        f"?action=query&titles={title_encoded}&prop=imageinfo"
        f"&iiprop=url&iiurlwidth=600&format=json"
    )
    req = urllib.request.Request(info_api, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        info = json.loads(r.read())
    pages = info.get("query", {}).get("pages", {})
    for page in pages.values():
        ii = page.get("imageinfo", [])
        if ii:
            return ii[0].get("thumburl") or ii[0].get("url")
    return None


def download(url: str, out_path: str) -> bool:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        if len(data) < 8000:
            return False
        with open(out_path, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False


def main():
    os.makedirs(MEN, exist_ok=True)
    os.makedirs(WOMEN, exist_ok=True)

    print("=== Moving existing images ===")
    for filename, dest in MOVES.items():
        src = os.path.join(BASE, filename)
        dst = os.path.join(dest, filename)
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"  moved {filename} -> {os.path.basename(dest)}/")
        elif os.path.exists(dst):
            print(f"  [skip] {filename} already in {os.path.basename(dest)}/")
        else:
            print(f"  [miss] {filename} not found")

    for filename in REMOVE:
        src = os.path.join(BASE, filename)
        if os.path.exists(src):
            os.remove(src)
            print(f"  removed {filename} (wrong style match)")

    print("\n=== Downloading missing gender-specific images ===")
    failed = []
    for (folder, filename), queries in DOWNLOADS.items():
        out_path = os.path.join(folder, filename)
        label = f"{os.path.basename(folder)}/{filename}"
        if os.path.exists(out_path):
            print(f"  [skip] {label} already exists")
            continue
        done = False
        for query in queries:
            print(f"  {label}: searching '{query}'...")
            try:
                titles = wikimedia_candidates(query)
            except Exception as e:
                print(f"    search failed: {e}")
                time.sleep(3)
                continue
            for title in titles:
                url = get_image_url(title)
                if url and download(url, out_path):
                    print(f"    [ok] {title}")
                    done = True
                    break
                time.sleep(1)
            if done:
                break
            time.sleep(2)
        if not done:
            failed.append(label)
            print(f"    [FAILED] {label}")
        time.sleep(2)

    print("\nDone.")
    if failed:
        print(f"Failed ({len(failed)}): {', '.join(failed)}")
        print("Download these manually from unsplash.com / pexels.com")


if __name__ == "__main__":
    main()
