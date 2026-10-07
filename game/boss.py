from game.assets import flipped_frames, load_frames, tinted_frames, white_frames
from game.enemy import Enemy, get_shadow
from game.settings import (BOSS_ENRAGE_AT, BOSS_ENRAGE_SPEED_MULT, BOSS_ENRAGE_TINT, BOSS_STATS,
                           ENEMY_ANIMATION_FPS)


class Boss(Enemy):
    curable = False

    def __init__(self, run, pos, hp_mult=1.0):
        super().__init__(run, "bird", pos)
        stats = BOSS_STATS
        self.name = stats["name"]
        self.max_hp = stats["hp"] * hp_mult
        self.hp = self.max_hp
        self.speed = stats["speed"]
        self.damage = stats["damage"]
        self.xp = stats["xp"]
        self.radius = stats["radius"]
        width, height = stats["frame_size"]
        size = (width * stats["scale"], height * stats["scale"])
        self.frames = load_frames(stats["sprite"], 4, size, fallback_color="black")
        self.shadow = get_shadow(size[0] // 2)
        self.enraged = False

    def update(self, dt):
        if not self.enraged and self.hp <= self.max_hp * BOSS_ENRAGE_AT:
            self.enraged = True
            self.speed *= BOSS_ENRAGE_SPEED_MULT
        super().update(dt)

    def current_image(self):
        frames = self.frames
        if self.run.player.pos.x > self.pos.x:
            frames = flipped_frames(frames)
        if self.flash_timer > 0:
            frames = white_frames(frames)
        elif self.enraged:
            frames = tinted_frames(frames, BOSS_ENRAGE_TINT)
        return frames[int(self.animation_time * ENEMY_ANIMATION_FPS) % len(frames)]
