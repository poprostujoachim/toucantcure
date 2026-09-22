import pygame
from subfunctions.generation import is_walkable # Import your collision logic

class Player(pygame.sprite.Sprite):
    # CHANGED BY EVA: Lowered default speed from 300 to 150
    def __init__(self, start_x, start_y, speed=250, radius=20):
        super().__init__()
        self.pos = pygame.Vector2(start_x, start_y)
        self.speed = speed
        self.radius = radius

    # CHANGED BY EVA: Added city_name parameter to know which map to check
    def update(self, keys, delta_time, bounds, city_name):
        new_x, new_y = self.pos.x, self.pos.y

        # Calculate desired new position (using Arrow Keys)
        if keys[pygame.K_UP]:
            new_y -= self.speed * delta_time
        if keys[pygame.K_DOWN]:
            new_y += self.speed * delta_time
        if keys[pygame.K_LEFT]:
            new_x -= self.speed * delta_time
        if keys[pygame.K_RIGHT]:
            new_x += self.speed * delta_time

        # CHANGED BY EVA: Apply movement ONLY if the target tile is walkable
        if is_walkable(new_x, self.pos.y, city_name):
            self.pos.x = new_x
        if is_walkable(self.pos.x, new_y, city_name):
            self.pos.y = new_y

    def draw(self, surface, camera_x, camera_y):
        # Shift the player's visual position based on the camera
        screen_x = int(self.pos.x - camera_x)
        screen_y = int(self.pos.y - camera_y)
        pygame.draw.circle(surface, "red", (screen_x, screen_y), self.radius)