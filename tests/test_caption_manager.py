"""Tests for caption_manager"""

import pathlib

import pytest

from training_prep_tools.caption_manager import (
    fname_ext,
    fname_base,
    fname_parts,
    is_image,
    make_caption,
    process_image_file,
    process_source_tree,
)


# ---------------------------------------------------------------------------
# fname helpers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    'filename, expected_base, expected_ext',
    [
        ("file.txt", "file", "txt"),
        ("archive.tar.gz", "archive.tar", "gz"),
        ("noext", "noext", None),
        ("dir/image.png", "dir/image", "png"),
    ]
)
def test_fname_parts(filename, expected_base, expected_ext):
    """fname_parts splits correctly into (base, ext)"""
    parts = fname_parts(filename)
    assert parts[0] == expected_base
    if expected_ext is None:
        assert len(parts) == 1
    else:
        assert parts[1] == expected_ext


@pytest.mark.parametrize(
    'filename, expected',
    [
        ("file.txt", "file"),
        ("dir/image.PNG", "dir/image"),
        ("noext", "noext"),
    ]
)
def test_fname_base(filename, expected):
    """fname_base returns the path without extension"""
    assert fname_base(filename) == expected


@pytest.mark.parametrize(
    'filename, expected',
    [
        ("file.txt", "txt"),
        ("image.PNG", "PNG"),
        ("archive.tar.gz", "gz"),
        ("noext", None),
    ]
)
def test_fname_ext(filename, expected):
    """fname_ext returns only the extension"""
    assert fname_ext(filename) == expected


# ---------------------------------------------------------------------------
# is_image
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    'filename, expected',
    [
        ("photo.png", True),
        ("photo.PNG", True),
        ("photo.jpg", True),
        ("photo.jpeg", True),
        ("photo.tiff", True),
        ("photo.tif", True),
        ("document.pdf", False),
        ("readme.txt", False),
        ("noext", False),
    ]
)
def test_is_image(filename, expected):
    """is_image correctly identifies image file extensions"""
    assert is_image(pathlib.Path(filename)) is expected


# ---------------------------------------------------------------------------
# make_caption
# ---------------------------------------------------------------------------

def test_make_caption_with_template_and_keywords():
    """Caption template with appended keywords"""
    config = {
        'caption': '{species} {topic}',
        'species': 'amanita',
        'topic': 'mushroom',
        'keywords': 'mycology, nature',
    }
    result = make_caption(config)
    assert result == 'amanita mushroom, mycology, nature'


def test_make_caption_with_template_no_keywords():
    """Caption template without keywords"""
    config = {
        'caption': '{species} {topic}',
        'species': 'russula',
        'topic': 'mushroom',
    }
    result = make_caption(config)
    assert result == 'russula mushroom'


def test_make_caption_keywords_only():
    """When only keywords are present, they become the caption"""
    config = {'keywords': 'bright red, pinhead mushroom'}
    result = make_caption(config)
    assert result == 'bright red, pinhead mushroom'


def test_make_caption_required_fields():
    """Required fields are assembled into a caption when no template is given"""
    config = {
        'required': 'topic, species',
        'topic': 'mushroom',
        'species': 'amanita',
    }
    result = make_caption(config)
    assert result == 'topic is mushroom, species is amanita'


def test_make_caption_desc_fallback():
    """desc field is used as fallback when nothing else is set"""
    config = {'desc': 'a photograph of a mushroom'}
    result = make_caption(config)
    assert result == 'a photograph of a mushroom'


def test_make_caption_generic_fallback():
    """Generic key=value fallback for arbitrary config dicts"""
    config = {'color': 'red', 'size': 'large'}
    result = make_caption(config)
    assert 'color is red' in result
    assert 'size is large' in result


def test_make_caption_required_with_missing_field():
    """Required field that is missing gets an empty string"""
    config = {
        'required': 'topic, species',
        'topic': 'mushroom',
    }
    result = make_caption(config)
    assert 'topic is mushroom' in result
    assert 'species is' in result


# ---------------------------------------------------------------------------
# process_image_file and process_source_tree
# ---------------------------------------------------------------------------

def test_process_image_file_writes_caption(tmp_path):
    """process_image_file writes a .txt caption alongside the image"""
    source_dir = tmp_path / 'source'
    source_dir.mkdir()
    target_dir = tmp_path / 'target'
    target_dir.mkdir()

    image_file = source_dir / 'photo.png'
    image_file.touch()

    config = {'caption': '{species} {topic}', 'species': 'russula', 'topic': 'mushroom'}
    process_image_file(image_file, target_dir, config)

    caption_file = target_dir / 'photo.txt'
    assert caption_file.exists(), "Caption file should have been created"
    assert caption_file.read_text() == 'russula mushroom'


def test_process_image_file_uses_yaml_override(tmp_path):
    """process_image_file merges per-image YAML when present"""
    source_dir = tmp_path / 'source'
    source_dir.mkdir()
    target_dir = tmp_path / 'target'
    target_dir.mkdir()

    image_file = source_dir / 'photo.png'
    image_file.touch()
    yaml_file = source_dir / 'photo.yaml'
    yaml_file.write_text('keywords: "close-up"\n')

    config = {
        'caption': '{species} {topic}',
        'species': 'russula',
        'topic': 'mushroom',
    }
    process_image_file(image_file, target_dir, config)

    caption_file = target_dir / 'photo.txt'
    assert caption_file.exists()
    assert caption_file.read_text() == 'russula mushroom, close-up'


def test_process_source_tree_basic(tmp_path):
    """process_source_tree reads caption_config.yaml and writes captions for images"""
    source = tmp_path / 'source'
    source.mkdir()
    target = tmp_path / 'target'

    (source / 'caption_config.yaml').write_text(
        'caption: "{species} {topic}"\nspecies: amanita\ntopic: mushroom\n'
    )
    (source / 'img1.png').touch()
    (source / 'img2.jpg').touch()
    (source / 'README.txt').touch()  # should be skipped

    process_source_tree(source, target)

    assert (target / 'img1.txt').read_text() == 'amanita mushroom'
    assert (target / 'img2.txt').read_text() == 'amanita mushroom'
    assert not (target / 'README.txt').exists(), "Non-image files should not produce captions"


def test_process_source_tree_keywords_accumulate(tmp_path):
    """Keywords from parent and child configs are merged, not replaced"""
    source = tmp_path / 'source'
    source.mkdir()
    sub = source / 'sub'
    sub.mkdir()
    target = tmp_path / 'target'

    (source / 'caption_config.yaml').write_text(
        'caption: "{species} {topic}"\nspecies: russula\ntopic: mushroom\nkeywords: "mycology, nature"\n'
    )
    (sub / 'caption_config.yaml').write_text('keywords: "close-up"\n')
    (sub / 'img.png').touch()

    process_source_tree(source, target)

    caption_file = target / 'sub' / 'img.txt'
    assert caption_file.exists()
    content = caption_file.read_text()
    assert 'close-up' in content
    assert 'mycology' in content
    assert 'nature' in content


def test_process_source_tree_flat_target(tmp_path):
    """flat_target=True places all captions in the top-level target directory"""
    source = tmp_path / 'source'
    source.mkdir()
    sub = source / 'sub'
    sub.mkdir()
    target = tmp_path / 'target'

    (source / 'caption_config.yaml').write_text('caption: "test"\n')
    (sub / 'img.png').touch()

    process_source_tree(source, target, flat_target=True)

    assert (target / 'img.txt').exists(), "Image caption should land in flat target dir"
    assert not (target / 'sub').exists(), "Sub-directory should not exist in flat target"
