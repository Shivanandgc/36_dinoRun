import math
import random
import pygame

# Stamina regained per frame (original was 0.8; lowered so steady mashing can actually exhaust you)
STAMINA_RECOVERY = 0.05


class GameEngine:

    # AI behaviour tuning (timings are in frames; the game runs at 60 FPS)
    FPS = 60
    AI_MAX_ENERGY = 100.0
    AI_ENERGY_RATE = 0.28          # energy gained per frame while building (~6 s to fill)
    AI_SURGE_MULT = 2.6            # force multiplier during a power surge
    AI_EXHAUSTED_MULT = 0.35       # force multiplier while exhausted
    AI_SURGE_FRAMES = (60, 120)    # surge lasts 1-2 seconds
    AI_EXHAUST_FRAMES = (120, 180) # exhaustion lasts 2-3 seconds
    AI_RECOVER_FRAMES = 90         # ramp from exhausted force back to normal

    # Exhaustion warning stays visible at least this long once triggered (ms),
    # because stamina recovers above 10 within a frame or two.
    EXHAUST_WARNING_MS = 800

    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        self.arm_position = 0.0
        self.target_limit = 100.0
        self.last_key = None
        
        self.stamina = 100.0
        self.max_stamina = 100.0
        
        self.winner = None
        self.game_state = "PLAYING"
        self.ai_strength = 0.35  

        # AI surge system state
        self.ai_state = "BUILDING"     # BUILDING, SURGE, EXHAUSTED, RECOVERING
        self.ai_energy = 0.0
        self.ai_timer = 0

        # Exhaustion warning: timestamp (ms) until which the warning stays visible
        self.exhausted_until = 0
        
        self.font_big = pygame.font.SysFont(None, 44)
        self.font_med = pygame.font.SysFont(None, 26)

    def handle_event(self, event):
        if self.game_state != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return

        if event.type == pygame.KEYDOWN:
            if self.stamina <= 10:
                return
            
            # Negative arm_position moves toward the player's winning side (-target_limit)
            if event.key == pygame.K_LEFT:
                if self.last_key != pygame.K_LEFT: 
                    self.arm_position -= 4.2
                    self.stamina = max(0.0, self.stamina - 2.0)
                    self.last_key = pygame.K_LEFT
            elif event.key == pygame.K_RIGHT:
                if self.last_key != pygame.K_RIGHT: 
                    self.arm_position -= 4.2
                    self.stamina = max(0.0, self.stamina - 2.0)
                    self.last_key = pygame.K_RIGHT

            self.note_exhaustion()

    def note_exhaustion(self):
        """Start/extend the warning hold whenever stamina is at or below the usable threshold."""
        if self.stamina <= 10:
            self.exhausted_until = pygame.time.get_ticks() + self.EXHAUST_WARNING_MS

    def exhaustion_warning_active(self):
        """True while the exhaustion warning should be drawn."""
        if self.game_state != "PLAYING":
            return False
        return self.stamina <= 10 or pygame.time.get_ticks() < self.exhausted_until

    def update_ai_state(self):
        """Advance the AI energy/surge/exhaustion cycle and return a force multiplier."""
        if self.ai_state == "BUILDING":
            self.ai_energy = min(self.AI_MAX_ENERGY, self.ai_energy + self.AI_ENERGY_RATE)
            if self.ai_energy >= self.AI_MAX_ENERGY:
                self.ai_state = "SURGE"
                self.ai_timer = random.randint(*self.AI_SURGE_FRAMES)
            # Energy makes the AI slightly stronger as it builds up (1.0 -> 1.3)
            return 1.0 + 0.3 * (self.ai_energy / self.AI_MAX_ENERGY)

        if self.ai_state == "SURGE":
            self.ai_timer -= 1
            # Energy drains as the surge is spent
            self.ai_energy = max(0.0, self.ai_energy - self.AI_MAX_ENERGY / self.AI_SURGE_FRAMES[1])
            if self.ai_timer <= 0:
                self.ai_state = "EXHAUSTED"
                self.ai_energy = 0.0
                self.ai_timer = random.randint(*self.AI_EXHAUST_FRAMES)
            return self.AI_SURGE_MULT

        if self.ai_state == "EXHAUSTED":
            self.ai_timer -= 1
            if self.ai_timer <= 0:
                self.ai_state = "RECOVERING"
                self.ai_timer = self.AI_RECOVER_FRAMES
            return self.AI_EXHAUSTED_MULT

        # RECOVERING: force ramps smoothly from exhausted level back to normal
        self.ai_timer -= 1
        if self.ai_timer <= 0:
            self.ai_state = "BUILDING"
            self.ai_energy = 0.0
            self.ai_timer = 0
            return 1.0
        progress = 1.0 - (self.ai_timer / self.AI_RECOVER_FRAMES)
        return self.AI_EXHAUSTED_MULT + (1.0 - self.AI_EXHAUSTED_MULT) * progress

    def update(self):
        if self.game_state != "PLAYING":
            return

        ai_multiplier = self.update_ai_state()
        ai_variance = random.uniform(0.3, 1.0)
        self.arm_position += self.ai_strength * ai_variance * ai_multiplier

        self.note_exhaustion()

        if self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + STAMINA_RECOVERY)

        if self.arm_position <= -self.target_limit:
            self.winner = "PLAYER"
            self.game_state = "GAME_OVER"
        elif self.arm_position >= self.target_limit:
            self.winner = "COMPUTER"
            self.game_state = "GAME_OVER"

    def reset(self):
        self.arm_position = 0.0
        self.stamina = 100.0
        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"
        self.ai_state = "BUILDING"
        self.ai_energy = 0.0
        self.ai_timer = 0
        self.exhausted_until = 0

    def render(self, screen):
        screen.fill((25, 28, 35))

        title_surf = self.font_big.render("ARM WRESTLE SHOWDOWN", True, (240, 240, 240))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 12))

        player_header = self.font_med.render("PLAYER", True, (80, 160, 255))
        computer_header = self.font_med.render("COMPUTER", True, (255, 100, 80))
        screen.blit(player_header, (60, 55))
        screen.blit(computer_header, (self.width - 150, 55))

        # AI state indicator (only visible during a surge or while the AI is tired)
        if self.game_state == "PLAYING":
            if self.ai_state == "SURGE":
                surge_on = (pygame.time.get_ticks() // 150) % 2 == 0
                ai_color = (255, 90, 40) if surge_on else (255, 200, 60)
                ai_surf = self.font_med.render("POWER SURGE!", True, ai_color)
                screen.blit(ai_surf, (self.width - 50 - ai_surf.get_width(), 78))
            elif self.ai_state == "EXHAUSTED":
                ai_surf = self.font_med.render("AI TIRED...", True, (120, 170, 230))
                screen.blit(ai_surf, (self.width - 50 - ai_surf.get_width(), 78))

        table_rect = pygame.Rect(40, 100, self.width - 80, 310)
        pygame.draw.rect(screen, (110, 50, 15), table_rect, border_radius=14)
        pygame.draw.rect(screen, (70, 30, 8), table_rect, width=5, border_radius=14)

        pygame.draw.line(screen, (45, 18, 4), (self.width // 2, 100), (self.width // 2, 410), 4)

        offset_x = (self.arm_position / self.target_limit) * 95
        hand_x = (self.width // 2) + int(offset_x)
        hand_y = 235

        p_shoulder = (70, 330)
        p_elbow = (140, 215)
        c_shoulder = (self.width - 70, 330)
        c_elbow = (self.width - 140, 215)

        pygame.draw.line(screen, (200, 145, 110), p_shoulder, p_elbow, 32)
        pygame.draw.line(screen, (215, 160, 125), p_elbow, (hand_x, hand_y), 26)
        pygame.draw.circle(screen, (185, 130, 95), p_elbow, 18)

        pygame.draw.line(screen, (170, 110, 85), c_shoulder, c_elbow, 32)
        pygame.draw.line(screen, (185, 125, 95), c_elbow, (hand_x, hand_y), 26)
        pygame.draw.circle(screen, (150, 95, 70), c_elbow, 18)

        pygame.draw.circle(screen, (225, 175, 140), (hand_x, hand_y), 24)
        pygame.draw.circle(screen, (160, 115, 85), (hand_x, hand_y), 24, width=3)

        stamina_label = self.font_med.render("STAMINA", True, (220, 220, 220))
        screen.blit(stamina_label, (40, 445))

        stamina_bg = pygame.Rect(140, 448, 240, 22)
        stamina_fill = pygame.Rect(140, 448, int(240 * (self.stamina / self.max_stamina)), 22)
        pygame.draw.rect(screen, (45, 50, 60), stamina_bg, border_radius=6)
        bar_color = (60, 210, 100) if self.stamina > 25 else (220, 60, 60)

        # Exhaustion warning: shown only while input is actually disabled
        exhausted = self.exhaustion_warning_active()
        flash_on = (pygame.time.get_ticks() // 200) % 2 == 0
        if exhausted:
            bar_color = (255, 40, 40) if flash_on else (110, 20, 20)
        pygame.draw.rect(screen, bar_color, stamina_fill, border_radius=6)

        if exhausted:
            # Flashing outline around the whole stamina bar
            outline_color = (255, 80, 80) if flash_on else (150, 40, 40)
            pygame.draw.rect(screen, outline_color, stamina_bg, width=3, border_radius=6)

            warn_color = (255, 60, 60) if flash_on else (255, 190, 60)
            warn_surf = self.font_med.render("EXHAUSTED!", True, warn_color)
            screen.blit(warn_surf, (stamina_bg.right + 15, 448))

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            win_text = "PLAYER WINS THE MATCH!" if self.winner == "PLAYER" else "COMPUTER WINS!"
            color = (80, 240, 100) if self.winner == "PLAYER" else (240, 80, 80)
            text_surf = self.font_big.render(win_text, True, color)
            screen.blit(
                text_surf,
                (self.width // 2 - text_surf.get_width() // 2, self.height // 2 - 45)
            )

            restart_surf = self.font_med.render(
                "Press [R] to Rematch", True, (240, 240, 240)
            )
            screen.blit(
                restart_surf,
                (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 10)
            )
