import pytest
from vision.feature_extractor import FaceFeatures, merge_features


def _features(face_shape="Oval", hair_type="Straight", hair_texture="Medium", gender="Unspecified"):
    return FaceFeatures(face_shape=face_shape, hair_type=hair_type, hair_texture=hair_texture, gender=gender)


def test_merge_single_candidate_returned_unchanged():
    only = _features(face_shape="Round")
    assert merge_features([only]) is only


def test_merge_empty_raises():
    with pytest.raises(ValueError):
        merge_features([])


def test_merge_majority_vote_wins():
    image = _features(face_shape="Round")
    video = _features(face_shape="Round")
    text = _features(face_shape="Oval")
    merged = merge_features([image, video, text])
    assert merged.face_shape == "Round"


def test_merge_tie_breaks_by_priority_order():
    # Caller passes candidates in priority order: image before text.
    image = _features(face_shape="Oval")
    text = _features(face_shape="Round")
    merged = merge_features([image, text])
    assert merged.face_shape == "Oval"


def test_merge_combines_fields_independently():
    image = _features(face_shape="Square", hair_type="Straight")
    text = _features(face_shape="Square", hair_type="Curly", hair_texture="Thick", gender="Male")
    merged = merge_features([image, text])
    # face_shape: both agree
    assert merged.face_shape == "Square"
    # hair_type: tie, image (first) wins
    assert merged.hair_type == "Straight"
    # hair_texture/gender: only text provided a differing value but it's still just a 1-1 tie, image's default wins
    assert merged.hair_texture == image.hair_texture
    assert merged.gender == image.gender
