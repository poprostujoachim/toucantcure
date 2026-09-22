import pygame

# 1. Update the import to pull your new function
from subfunctions.generation import draw_infinite_background
from subfunctions.enemy import Enemy
from subfunctions.player import Player

WIDTH, HEIGHT = 1280, 720
FPS = 120


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # 2. Add the city variable
    current_city = "Leiden"

    player = Player(WIDTH / 2, HEIGHT / 2)
    enemy = Enemy(100, 100, speed=120)

    running = True
    dt = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.update(keys, dt, (WIDTH, HEIGHT), current_city)
        enemy.update(player.pos, dt)

        # Calculate camera tracking based on the real Player object
        # We divide WIDTH and HEIGHT by 2 to keep Marcus perfectly centered
        camera_x = player.pos.x - (WIDTH / 2)
        camera_y = player.pos.y - (HEIGHT / 2)

        # Draw infinite background FIRST
        draw_infinite_background(screen, camera_x, camera_y, current_city)

        # Draw entities on top (Pass camera_x and camera_y to them)
        enemy.draw(screen, camera_x, camera_y)
        player.draw(screen, camera_x, camera_y)

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()
