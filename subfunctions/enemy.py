import pygame
import os

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')

FRAME_COUNT = 4
ANIMATION_FPS = 8


def load_enemy_frames(size):
    """Cut the sprite sheet into frames scaled to size, falling back to a blue circle."""
    try:
        sheet = pygame.image.load(os.path.join(ASSETS_DIR, 'duck_bird.png')).convert_alpha()
    except (pygame.error, FileNotFoundError):
        fallback = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(fallback, "blue", (size // 2, size // 2), size // 2)
        return [fallback]

    frame_width = sheet.get_width() // FRAME_COUNT
    frame_height = sheet.get_height()

    frames = []
    for i in range(FRAME_COUNT):
        frame = sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
        frames.append(pygame.transform.scale(frame, (size, size)))
    return frames


class Enemy(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, speed=200, radius=20):
        super().__init__()
        self.pos = pygame.Vector2(start_x, start_y)
        self.speed = speed
        self.radius = radius
        self.frames = load_enemy_frames(radius * 2)
        self.animation_time = 0

    def update(self, target_pos, delta_time):
        direction = target_pos - self.pos
        distance = direction.length()

        if distance > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * delta_time

        self.animation_time += delta_time

    def draw(self, surface):
        frame_index = int(self.animation_time * ANIMATION_FPS) % len(self.frames)
        texture = self.frames[frame_index]
        surface.blit(texture, texture.get_rect(center=(round(self.pos.x), round(self.pos.y))))
