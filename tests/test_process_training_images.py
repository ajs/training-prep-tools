import os
from typing import Union, Tuple

import pytest
from PIL import Image

from training_prep_tools.process_training_images import ImageInfo, white_pixel, black_pixel, FuzzyImageRecall, \
    get_filename_key, guess_border


@pytest.mark.parametrize(
    'filename, expect',
    [
        ("x", "x"),
        ("abc-1.png", "abc-000001.png"),
        ("abc-01.png", "abc-000001.png"),
    ]
)
def test_get_filename_key(filename: os.PathLike, expect: str):
    assert get_filename_key(filename) == expect, f"filename key handling: {filename} -> {expect}"


@pytest.mark.parametrize(
    'mode',
    ('1', 'L', 'RGB', 'RGBA', 'CMYK'),
)
def test_autocrop(mode):
    white = white_pixel(mode)
    black = black_pixel(mode)
    image = Image.new(mode, (3, 3), white)
    assert image.getpixel((0, 0)) == white, "Image should have white pixels"
    cropped = FuzzyImageRecall._autocrop(image)
    assert cropped.size == (3, 3), "Autocrop white image should make no change"
    image.putpixel((1, 1), black)
    cropped = FuzzyImageRecall._autocrop(image)
    assert cropped.size == (1, 1), "Autocrop expected to return 1x1"
    image.putpixel((0, 0), black)
    cropped = FuzzyImageRecall._autocrop(image)
    assert cropped.size == (2, 2), "Autocrop expected to return 2x2"
    assert cropped.getpixel((0, 0)) == black, "Expect returned image to contain black in upper left"
    assert cropped.getpixel((1, 0)) == white, "Expect returned image to contain black in upper left"


def make_image_corners(mode, *corners):
    """Used for testing, make an Image with the given mode and corner pixel values"""
    corner_lookup = {
        'L': {
            'white': white_pixel("L"),
            'black': black_pixel("L"),
        },
        'RGB': {
            'white': white_pixel("RGB"),
            'black': black_pixel("RGB"),
        }
    }
    corners = [corner_lookup[mode][corner] for corner in corners]
    base_value = corners[0]
    image = Image.new(mode, (3, 3), base_value)
    corner_locs = ((0, 0), (2, 0), (0, 2), (2, 2))
    for loc, value in zip(corner_locs, corners):
        image.putpixel(loc, value)
    return image


@pytest.mark.parametrize(
    'image, expected, what_is',
    [
        (make_image_corners("L", 'white', 'white', 'white', 'white'), 255, "Greyscale all white"),
        (make_image_corners("L", 'black', 'black', 'black', 'black'), 0, "Greyscale all black"),
        (make_image_corners("L", 'black', 'black', 'white', 'white'), 255, "Greyscale half and half"),
        (make_image_corners("L", 'black', 'black', 'black', 'white'), 0, "Greyscale one white"),
        (make_image_corners("RGB", 'white', 'white', 'white', 'white'), (255, 255, 255), "Greyscale all white"),
        (make_image_corners("RGB", 'black', 'black', 'black', 'black'), (0, 0, 0), "Greyscale all black"),
        (make_image_corners("RGB", 'black', 'black', 'white', 'white'), (255, 255, 255), "Greyscale half and half"),
        (make_image_corners("RGB", 'black', 'black', 'black', 'white'), (0, 0, 0), "Greyscale one white"),
    ]
)
def test_guess_border(image: Image, expected: Union[int, Tuple[int, int, int]], what_is: str):
    """Quick test for our border color guessing"""
    assert guess_border(image) == expected, f"Expect return value of {expected!r} for {what_is}"


def make_test_color_image(mode: str):
    """Used for testing color image detection"""
    image = make_test_grayscale_image('RGB')
    image.putpixel((255, 255), (0, 255, 127))  # Add just one color pixel to make it harder
    if mode != image.mode:
        image = image.convert(mode)
    return image


def make_test_grayscale_image(mode: str):
    """Used for testing color image detection"""
    image = Image.linear_gradient('L').convert('RGB')
    if mode != image.mode:
        if mode.endswith('A'):
            image.putalpha(Image.new('1', image.size, 1))
        image = image.convert(mode)
    return image


@pytest.mark.parametrize(
    'image, is_color, description',
    [
        (make_test_grayscale_image('1'), False, "B/W"),
        (make_test_grayscale_image('L'), False, "grayscale"),
        (make_test_grayscale_image('LA'), False, "grayscale with transparency"),
        (make_test_grayscale_image('RGB'), False, "RGB grayscale"),
        (make_test_color_image('RGB'), True, "RGB color image"),
        (make_test_grayscale_image('RGBA'), False, "RGBA grayscale"),
        (make_test_color_image('RGBA'), True, "RGBA color image"),
        (make_test_grayscale_image('CMYK'), False, "CMYK grayscale"),
        (make_test_color_image('CMYK'), True, "CMYK color image"),
    ]
)
def test_is_color_check(image, is_color, description):
    """Test the is_color check that is defined on ImageInfo"""
    assert ImageInfo.is_color(image) is is_color, f"Expect is_color={is_color!r} for {description}"
