"""
Unit tests for feature merging (vision/feature_extractor.py)
and style-image matching (services/style_images.py).
"""

import pytest

from vision.feature_extractor import FaceFeatures, merge_features
from services.style_images import find_style_images


def _features(shape="Oval", htype="Straight", texture="Medium", gender="Male"):
    return FaceFeatures(
        face_shape=shape, hair_type=htype, hair_texture=texture, gender=gender
    )


# ── merge_features ───────────────────────────────────────────────────────────

def test_single_candidate_returned_unchanged():
    only = _features(shape="Round")
    assert merge_features([only]) == only


def test_majority_vote_wins():
    merged = merge_features([
        _features(shape="Round"),
        _features(shape="Round"),
        _features(shape="Oval"),
    ])
    assert merged.face_shape == "Round"


def test_tie_goes_to_first_candidate():
    # Image (first) says Oval, text (second) says Square → image wins the tie
    merged = merge_features([_features(shape="Oval"), _features(shape="Square")])
    assert merged.face_shape == "Oval"


def test_fields_vote_independently():
    merged = merge_features([
        _features(shape="Round", htype="Curly"),
        _features(shape="Round", htype="Wavy"),
        _features(shape="Heart", htype="Wavy"),
    ])
    assert merged.face_shape == "Round"   # 2 vs 1
    assert merged.hair_type == "Wavy"     # 2 vs 1

def test_empty_candidates_raise():
    with pytest.raises(ValueError):
        merge_features([])


# ── find_style_images ────────────────────────────────────────────────────────

pytestmark = pytest.mark.usefixtures("chdir_project_root")


@pytest.mark.usefixtures("chdir_project_root")
class TestStyleImages:
    def test_male_style_found_in_men_folder(self):
        results = find_style_images("Try a textured crop.", "Male")
        assert len(results) == 1
        assert "men" in results[0]["path"]

    def test_female_style_found_in_women_folder(self):
        results = find_style_images("A pixie cut would suit you.", "Female")
        assert len(results) == 1
        assert "women" in results[0]["path"]

    def test_long_bob_matches_lob_not_bob(self):
        # "long bob" must claim its text before the shorter alias "bob"
        results = find_style_images("A long bob is perfect.", "Female")
        styles = [r["style"] for r in results]
        assert "Lob" in styles
        assert "Bob" not in styles

    def test_styles_ordered_by_mention(self):
        text = "First consider a quiff, then maybe an undercut."
        styles = [r["style"] for r in find_style_images(text, "Male")]
        assert styles == ["Quiff", "Undercut"]

    def test_max_images_respected(self):
        text = "Options: quiff, undercut, pompadour, crew cut."
        assert len(find_style_images(text, "Male", max_images=2)) == 2

    def test_no_styles_mentioned_returns_empty(self):
        assert find_style_images("Moisturise your hair daily.", "Female") == []

    def test_low_confidence_gender_still_finds_image(self):
        # Androgynous/bigender presentation (confidence below threshold): use
        # whichever folder has the style, rather than committing to one gender.
        results = find_style_images("Get a buzz cut.", "Male", gender_confidence=0.5)
        assert len(results) == 1

    def test_bun_found_for_male(self):
        results = find_style_images("A man bun would look great on you.", "Male")
        assert len(results) == 1
        assert results[0]["style"] == "Bun"
        assert "men" in results[0]["path"]

    def test_bun_found_for_female(self):
        results = find_style_images("Try a messy bun for a relaxed look.", "Female")
        assert len(results) == 1
        assert results[0]["style"] == "Bun"
        assert "women" in results[0]["path"]

    def test_bun_aliases_all_match(self):
        for alias in ["bun", "man bun", "top knot", "topknot", "messy bun"]:
            results = find_style_images(f"Consider a {alias}.", "Male")
            assert len(results) == 1, f"alias '{alias}' did not match"
