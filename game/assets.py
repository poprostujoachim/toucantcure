import os

import pygame

from game.settings import CITY_HOUSES, HOUSE_CANVAS

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

_frame_cache = {}


def load_frames(filename, frame_count, size, fallback_color="magenta"):
    key = (filename, frame_count, size)
    if key in _frame_cache:
        return _frame_cache[key]

    try:
        sheet = pygame.image.load(os.path.join(ASSETS_DIR, filename)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        print(f"Warning: could not load {filename}, using a placeholder")
        fallback = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.ellipse(fallback, fallback_color, fallback.get_rect())
        _frame_cache[key] = [fallback]
        return _frame_cache[key]

    frame_width = sheet.get_width() // frame_count
    frames = []
    for i in range(frame_count):
        frame = sheet.subsurface((i * frame_width, 0, frame_width, sheet.get_height()))
        frames.append(pygame.transform.scale(frame, size))

    _frame_cache[key] = frames
    return frames


_house_cache = {}


def load_city_house(city, height):
    """A city's house for menus: the pixel-dutch-house sprite when the city has one, else the old square icon."""
    key = (city, height)
    if key not in _house_cache:
        style = CITY_HOUSES.get(city)
        if style is None:
            image = load_frames(f"city_assets/{city}/house.png", 1, (height, height), fallback_color=(190, 150, 110))[0]
        else:
            width, canvas_height = HOUSE_CANVAS
            image = load_frames(f"pixel-dutch-house/{style}_house.png", 1, HOUSE_CANVAS,
                                fallback_color=(190, 150, 110))[0]
            if height >= canvas_height:
                scale = height // canvas_height
                image = pygame.transform.scale(image, (width * scale, canvas_height * scale))
            else:
                image = pygame.transform.smoothscale(image, (round(width * height / canvas_height), height))
        _house_cache[key] = image
    return _house_cache[key]


_recolor_cache = {}


def white_frames(frames):
    key = (id(frames), "white")
    if key not in _recolor_cache:
        _recolor_cache[key] = [pygame.mask.from_surface(f).to_surface(setcolor=(255, 255, 255, 255),
                                                                     unsetcolor=(0, 0, 0, 0)) for f in frames]
    return _recolor_cache[key]


def tinted_frames(frames, color):
    key = (id(frames), color)
    if key not in _recolor_cache:
        tinted = []
        for frame in frames:
            copy = frame.copy()
            copy.fill(color, special_flags=pygame.BLEND_RGB_MULT)
            tinted.append(copy)
        _recolor_cache[key] = tinted
    return _recolor_cache[key]


def flipped_frames(frames):
    key = (id(frames), "flip")
    if key not in _recolor_cache:
        _recolor_cache[key] = [pygame.transform.flip(f, True, False) for f in frames]
    return _recolor_cache[key]
