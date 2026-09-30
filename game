import random
import pygame

WIDTH, HEIGHT = 900, 400
GROUND_Y = 340
FPS = 60
BG_COLOR = (245, 245, 245)
GROUND_COLOR = (80, 80, 80)
GRAVITY, JUMP_FORCE = 0.6, -14
HIGH_SCORE_FILE = "dino_highscore.txt"


def dino_tint(on_ground):
    """Return an (r, g, b) colour override for the dino based on whether it's on the ground, or None for the default green."""
    pass


def on_obstacle_passed(obstacle, score):
    """Called once, the frame an obstacle finishes scrolling past the dino. Add a sound or a combo counter here."""
    pass


def max_jumps():
    """Return how many jumps the dino gets before it must land again (2 for a double jump), or None for the default of 1."""
    pass


def load_high_score():
    try:
        with open(HIGH_SCORE_FILE) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return 0


def save_high_score(value):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(value))
    except OSError:
        pass


class Dino:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 50, 60)
        self.vel_y = 0.0
        self.on_ground = True
        self.jump_count = 0
        self.color = (83, 141, 78)

    def jump(self):
        if self.jump_count < (max_jumps() or 1):
            self.vel_y = JUMP_FORCE
            self.on_ground = False
            self.jump_count += 1

    def update(self, ground_y):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.vel_y = 0
            self.on_ground = True
            self.jump_count = 0

    def draw(self, screen):
        color = dino_tint(self.on_ground) or self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        eye = pygame.Rect(self.rect.right - 12, self.rect.top + 10, 8, 8)
        pygame.draw.rect(screen, (255, 255, 255), eye, border_radius=4)
        pygame.draw.rect(screen, (0, 0, 0), (eye.x + 2, eye.y + 2, 4, 4))


class Obstacle:
    WIDTHS = [20, 30, 25]
    HEIGHTS = [40, 60, 50]

    def __init__(self, x, ground_y, speed):
        w = random.choice(self.WIDTHS)
        h = random.choice(self.HEIGHTS)
        self.rect = pygame.Rect(x, ground_y - h, w, h)
        self.speed = speed
        self.color = (180, 60, 40)
        self.passed = False

    def update(self):
        self.rect.x -= self.speed

    def is_off_screen(self):
        return self.rect.right < 0

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=4)


class Game:
    def __init__(self):
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 48)
        self.high_score = load_high_score()
        self.reset()

    def reset(self):
        self.dino = Dino(80, GROUND_Y)
        self.obstacles = []
        self.score = 0
        self.speed = 6
        self.spawn_timer = 0
        self.spawn_interval = 90
        self.state = "wait"

    def start_or_jump(self):
        if self.state == "lose":
            self.reset()
            return
        if self.state == "wait":
            self.state = "play"
        self.dino.jump()

    def update(self):
        if self.state != "play":
            return
        self.dino.update(GROUND_Y)
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.obstacles.append(Obstacle(WIDTH + 10, GROUND_Y, self.speed))
            self.spawn_timer = 0
            self.spawn_interval = random.randint(55, 110)

        hit = False
        for obs in self.obstacles:
            obs.update()
            if not obs.passed and obs.rect.right < self.dino.rect.left:
                obs.passed = True
                on_obstacle_passed(obs, self.score // 10)
            if obs.rect.colliderect(self.dino.rect):
                hit = True
        self.obstacles = [o for o in self.obstacles if not o.is_off_screen()]

        if hit:
            self.state = "lose"
            current = self.score // 10
            if self.high_score > current:
                self.high_score = current
                save_high_score(self.high_score)
            return

        self.score += 1
        if self.score % 300 == 0:
            self.speed += 0.5

    def draw(self, screen):
        screen.fill(BG_COLOR)
        pygame.draw.line(screen, GROUND_COLOR, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        self.dino.draw(screen)
        for obs in self.obstacles:
            obs.draw(screen)

        score_surf = self.font.render(f"Score: {self.score // 10}   Best: {self.high_score}", True, (50, 50, 50))
        screen.blit(score_surf, (WIDTH - 260, 20))

        if self.state == "wait":
            msg = self.big_font.render("Press SPACE to Start", True, (80, 80, 80))
            screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10)))
        elif self.state == "lose":
            msg = self.big_font.render("GAME OVER", True, (200, 40, 40))
            sub = self.font.render("Press SPACE to Restart", True, (80, 80, 80))
            screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dino Run")
    clock = pygame.time.Clock()
    game = Game()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                game.start_or_jump()
        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
