import pygame


class Enemy(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, speed=200, radius=15):
        super().__init__()
        self.pos = pygame.Vector2(start_x, start_y)
        self.speed = speed
        self.radius = radius

    def update(self, target_pos, delta_time):
        direction = target_pos - self.pos
        distance = direction.length()

        if distance > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * delta_time

    def draw(self, surface, camera_x, camera_y):
        # Shift the enemy's visual position based on the camera
        screen_x = int(self.pos.x - camera_x)
        screen_y = int(self.pos.y - camera_y)
        pygame.draw.circle(surface, "blue", (screen_x, screen_y), self.radius)