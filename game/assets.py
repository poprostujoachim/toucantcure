import os

import pygame

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
