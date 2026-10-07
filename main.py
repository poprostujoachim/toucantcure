import random

import pygame

from subfunctions.enemy import Enemy, spawn_swarm
from subfunctions.generation import draw_infinite_background, find_spawn_point
from subfunctions.player import Player

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

SHEET_BORDER_COLOR = (70, 70, 90)
TEXT_COLOR = (230, 230, 230)
SHEET_COLOR = (15, 15, 25)

# Test upgrades for the U key until the shop and level-ups exist.
TEST_UPGRADES = [
    ("max_hp", {"flat": 20}),
    ("move_speed", {"percent": 0.10}),
    ("armor", {"flat": 10}),
    ("crit_rate", {"flat": 0.05}),
    ("crit_damage", {"flat": 0.25}),
    ("luck", {"percent": 0.10}),
    ("pickup_range", {"percent": 0.25}),
    ("xp_gain", {"percent": 0.10}),
    ("projectile_speed", {"percent": 0.10}),
    ("attack_speed", {"percent": 0.10}),
    ("damage", {"percent": 0.10}),
]


def draw_stat_sheet(screen, font, stats):
    rows = stats.sheet()
    line_height = font.get_linesize()
    panel = pygame.Rect(0, 0, 420, line_height * (len(rows) + 1) + 20)
    panel.topright = (SCREEN_WIDTH - 10, 10)
    pygame.draw.rect(screen, SHEET_COLOR, panel)
    pygame.draw.rect(screen, SHEET_BORDER_COLOR, panel, 2)

    y = panel.top + 10
    screen.blit(font.render("Stats", True, TEXT_COLOR), (panel.left + 12, y))
    for label, text in rows:
        y += line_height
        screen.blit(font.render(label, True, TEXT_COLOR), (panel.left + 12, y))
        value = font.render(text, True, TEXT_COLOR)
        screen.blit(value, value.get_rect(topright=(panel.right - 12, y)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("TouCan'tCure")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)

    screen_center = screen.get_rect().center
    current_city = "Leiden"  # Picks the house style and the generated map.
    spawn = find_spawn_point(*screen_center, current_city)  # Nearest tile the player can walk on.
    player = Player(*spawn)
    lvl1_basic_e = Enemy(300, 200, speed=100, radius=20)
    lvl1_melee_e = Enemy(1000, 500, speed=140, radius=20, attack_style="contact")
    enemies = [lvl1_basic_e, lvl1_melee_e]
    enemies += spawn_swarm(1000, 150)
    enemy_projectiles = pygame.sprite.Group()  # Holds active enemy shots so we can update and remove them together.
    show_stats = False 
    is_paused = False


    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000, 0.05) 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False 
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t and player.alive:
                    player.take_damage(10) 
                    if not player.alive:
                        print("infected") 
                elif event.key == pygame.K_r:
                    player = Player(*spawn)
                elif event.key == pygame.K_TAB:
                    show_stats = not show_stats 
                elif event.key == pygame.K_u:
                    name, bonus = random.choice(TEST_UPGRADES)
                    player.stats.add(name, **bonus) 
                    print("upgrade:", name, bonus)
                elif event.key == pygame.K_ESCAPE:
                    is_paused = not is_paused
        
        if not is_paused:
            if player.alive:
                player.update(dt, pygame.key.get_pressed(), current_city)

            for enemy in enemies:
                new_projectiles = enemy.update(player.pos, dt)  
                enemy_projectiles.add(new_projectiles)
                if player.alive:
                    player.take_damage(enemy.contact_hit(player.pos, player.radius))

            for projectile in list(enemy_projectiles):
                if projectile.update(dt):
                    projectile.kill() 
                    continue
                if (projectile.pos - player.pos).length() <= projectile.radius + player.radius: 
                    player.take_damage(projectile.damage)
                    projectile.kill() 

        # The camera keeps the player in the middle of the screen.
        camera_x = player.pos.x - SCREEN_WIDTH / 2
        camera_y = player.pos.y - SCREEN_HEIGHT / 2

        draw_infinite_background(screen, camera_x, camera_y, current_city)  # Also clears the previous frame.
        player.draw(screen, camera_x, camera_y)
        for enemy in enemies:
            enemy.draw(screen, camera_x, camera_y)

        for projectile in enemy_projectiles:
            projectile.draw(screen, camera_x, camera_y)  # Draw each active enemy projectile.

        hp_text = font.render(f"HP: {player.hp:.0f}/{player.max_hp:.0f}", True, TEXT_COLOR)  # Show the player's current and max HP at the top-left.
        screen.blit(hp_text, (10, 10))  # Draw the HP text onto the game screen.
        if not player.alive:
            dead_text = font.render("infected - press R to restart", True, TEXT_COLOR) 
            screen.blit(dead_text, dead_text.get_rect(center=screen_center))
        if show_stats or is_paused:
            draw_stat_sheet(screen, font, player.stats)  # Draw the stat overlay when the player toggles it.

        if is_paused:
            paused_text = font.render("PAUSED", True, TEXT_COLOR)
            screen.blit(paused_text, paused_text.get_rect(center=screen_center))
            
        pygame.display.flip()  # Swap the back buffer to the visible screen.

    pygame.quit()


if __name__ == "__main__":
    main()
