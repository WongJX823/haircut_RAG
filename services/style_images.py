"""
Maps haircut style names mentioned in a recommendation text to
reference images in assets/images/men/ and assets/images/women/.
"""

import os
import re

from vision.feature_extractor import GENDER_CONFIDENCE_THRESHOLD

IMAGES_DIR = "assets/images"

# style filename (without .jpg) -> aliases that may appear in the recommendation
STYLE_ALIASES = {
    "afro": ["afro"],
    "blunt_bob": ["blunt bob"],
    "bun": ["bun", "man bun", "top knot", "topknot", "messy bun"],
    "bob": ["bob", "a-line bob", "inverted bob", "textured bob"],
    "buzz_cut": ["buzz cut"],
    "cornrows": ["cornrows", "cornrow braids"],
    "crew_cut": ["crew cut"],
    "curtain_bangs": ["curtain bangs", "curtain fringe"],
    "dreadlocks": ["dreadlocks", "locs"],
    "faux_hawk": ["faux hawk", "fohawk"],
    "french_crop": ["french crop", "caesar cut"],
    "lob": ["lob", "long bob"],
    "long_layers": ["long layers", "layered cut"],
    "mohawk": ["mohawk"],
    "pixie_cut": ["pixie cut", "pixie"],
    "pompadour": ["pompadour"],
    "quiff": ["quiff"],
    "shag_cut": ["shag cut", "shag"],
    "side_part": ["side part"],
    "slick_back": ["slick back", "slicked back", "slicked-back"],
    "tapered_cut": ["tapered cut"],
    "textured_crop": ["textured crop"],
    "undercut": ["undercut"],
    "wolf_cut": ["wolf cut", "modern mullet", "mullet"],
}


def find_style_images(
    recommendation: str, gender: str, gender_confidence: float = 1.0, max_images: int = 3
) -> list[dict]:
    """Return reference images for styles mentioned in the recommendation.

    Each result: {"style": "Wolf Cut", "path": "assets/images/men/wolf_cut.jpg"}.
    Longer aliases are matched first so "long bob" claims its text before
    the shorter "bob" can match inside it.
    """
    text = recommendation.lower()

    if gender_confidence < GENDER_CONFIDENCE_THRESHOLD:
        folders = ["men", "women"]  # androgynous/bigender: use whichever image exists
    elif gender.lower() == "male":
        folders = ["men"]
    else:
        folders = ["women"]

    # (alias, style) pairs, longest alias first so specific names win
    pairs = sorted(
        ((alias, style) for style, aliases in STYLE_ALIASES.items() for alias in aliases),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )

    claimed_spans: list[tuple[int, int]] = []
    found: list[tuple[int, str]] = []  # (position in text, style)
    for alias, style in pairs:
        if any(style == s for _, s in found):
            continue
        for match in re.finditer(rf"\b{re.escape(alias)}\b", text):
            span = (match.start(), match.end())
            overlaps = any(s < span[1] and span[0] < e for s, e in claimed_spans)
            if overlaps:
                continue
            claimed_spans.append(span)
            found.append((match.start(), style))
            break

    found.sort()  # show styles in the order the recommendation mentions them

    results = []
    for _, style in found:
        for folder in folders:
            path = os.path.join(IMAGES_DIR, folder, f"{style}.jpg")
            if os.path.exists(path):
                results.append({
                    "style": style.replace("_", " ").title(),
                    "path": path,
                })
                break
        if len(results) >= max_images:
            break
    return results
