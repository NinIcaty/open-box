import pygame, sys, random, math
pygame.init()
clock = pygame.time.Clock()
from ClassPlayer import *
# =======================
# ---  PARAMETERS  ------
# =======================
FPS = 60
WIDTH, HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
HALF_W = WIDTH // 2
GROUND_HEIGHT = int(HEIGHT * 0.12)
WORLD_WIDTH = 3500

# --- PLAYER SETTINGS ---
PLAYER_SPEED = 3
SPRINT_SPEED = 9
JUMP_POWER = int(HEIGHT * 0.0201)
PLAYER_WIDTH = int(WIDTH * 0.035)
PLAYER_HEIGHT = int(HEIGHT * 0.20)

# Combat & timing
REGEN_RATE = 0.5
REGEN_PER_FRAME = REGEN_RATE / FPS
REGEN_STAMINA_COST = 0.6
CRIT_THRESHOLD = 300
CRIT_DAMAGE = 30
NORMAL_DAMAGE = 5
PUNCH_COOLDOWN = 600
PUNCH_DURATION = 220
SPRINT_STAMINA_DRAIN = 0.9
STAMINA_MAX = 100.0
STAMINA_REGEN = 0.35
CRIT_STAMINA_REQUIRED_PCT = 0.75

# Powerup
POWERUP_DAMAGE = 35
POWERUP_RADIUS = int(min(WIDTH, HEIGHT) * 0.018)
POWERUP_THROW_SPEED = 14
POWERUP_GRAVITY = 0.6
POWERUP_SPAWN_INTERVAL = 10000  # ms

# Colors
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (220,50,50)
BLUE = (50,50,220)
DARK_BLUE = (80,150,255)
DARK_GREEN = (0,100,0)
GREY = (120,120,120)
PURPLE = (180,80,255)
ORANGE = (255,150,50)
YELLOW = (240,200,20)

# Window
win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("An open source project")

# ======================
# ---  CLASSES ---------
# ======================
class Projectile:
    def __init__(self, x, y, vx, vy, owner):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.owner = owner
        self.radius = POWERUP_RADIUS
        self.alive = True
    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius*2, self.radius*2)
    def update(self, obstacles):
        self.vy += POWERUP_GRAVITY
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > WORLD_WIDTH or self.y > HEIGHT + 200:
            self.alive = False
        for obs in obstacles:
            if self.rect().colliderect(obs):
                self.alive = False
                break
    def draw(self, surface, offset):
        pygame.draw.circle(surface, YELLOW, (int(self.x - offset), int(self.y)), self.radius)

class PowerupPickup:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = POWERUP_RADIUS
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius,
                                self.radius*2, self.radius*2)
        self.active = True
    def draw(self, surface, offset):
        if not self.active: return
        pygame.draw.circle(surface, ORANGE, (int(self.x - offset), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x - offset), int(self.y)), self.radius//2)



# ======================
# --- OBSTACLES ----
# ======================
def generate_obstacles(count=20):
    obs = []
    for _ in range(count):
        w = random.randint(50, 90)
        h = random.randint(30, 60)
        x = random.randint(200, WORLD_WIDTH - 200)
        y = HEIGHT - GROUND_HEIGHT - h
        obs.append(pygame.Rect(x, y, w, h))
    return obs

# ======================
# --- COMBAT & POWERUP ---
# ======================
def check_punch(attacker, target):
    if not attacker.alive or not target.alive: return
    if not attacker.punching or attacker.has_hit: return
    arm_x = attacker.x + (attacker.width if attacker.facing == 1 else -20)
    punch_rect = pygame.Rect(int(arm_x), int(attacker.y + attacker.height * 0.32), 20, int(attacker.height * 0.12))
    if punch_rect.colliderect(target.rect()) and not target.ducking:
        dmg = CRIT_DAMAGE if attacker.crit_ready else NORMAL_DAMAGE
        target.health = max(0.0, target.health - dmg)
        attacker.has_hit = True
        if attacker.crit_ready:
            attacker.crit_ready = False
            attacker.crit_charge = 0

def handle_projectile_hit(projectile, players):
    if not projectile.alive: return
    for p in players:
        if p is projectile.owner: continue
        if projectile.rect().colliderect(p.rect()):
            p.health = max(0.0, p.health - POWERUP_DAMAGE)
            projectile.alive = False
            if p.health <= 0: p.alive = False
            break

# ======================
# --- MAIN MENU --------
# ======================
def draw_button(surface, text, rect, hover):
    color = (180, 180, 180) if hover else (120, 120, 120)
    pygame.draw.rect(surface, color, rect, border_radius=10)
    pygame.draw.rect(surface, (0,0,0), rect, 2, border_radius=10)
    font = pygame.font.SysFont(None, 60)
    label = font.render(text, True, (0,0,0))
    surface.blit(label, (rect.centerx - label.get_width()//2, rect.centery - label.get_height()//2))

def main_menu():
    logo = pygame.image.load("logo.png").convert_alpha()
    logo = pygame.transform.scale(logo, (250, 250))
    start_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 50, 300, 80)
    quit_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 60, 300, 80)
    while True:
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        win.fill(DARK_BLUE)
        pygame.draw.rect(win, DARK_GREEN, (0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT))
        win.blit(logo, (WIDTH//2 - 50, HEIGHT//4 - 100))
        hover_start = start_rect.collidepoint(mouse)
        hover_quit = quit_rect.collidepoint(mouse)
        draw_button(win, "Start Game", start_rect, hover_start)
        draw_button(win, "Quit", quit_rect, hover_quit)
        if click[0]:
            if hover_start:
                return main()
            elif hover_quit:
                pygame.quit()
                sys.exit()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.flip()
        clock.tick(60)

# ======================
# ---  GAME LOOP -------
# ======================
def main():
    p1 = Player(100, HEIGHT - GROUND_HEIGHT - PLAYER_HEIGHT, RED,
                (pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_LSHIFT, pygame.K_s, pygame.K_q, pygame.K_e))
    p2 = Player(300, HEIGHT - GROUND_HEIGHT - PLAYER_HEIGHT, BLUE,
                (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_RSHIFT, pygame.K_DOWN, pygame.K_SLASH, pygame.K_QUOTE))
    players = [p1, p2]
    obstacles = generate_obstacles()
    projectiles = []
    pickups = []
    last_powerup_spawn = pygame.time.get_ticks()
    run = True
    while run:
        dt = clock.tick(FPS)
        keys_pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys_pressed[pygame.K_ESCAPE]:
                run = False

        # Spawn powerups
        now = pygame.time.get_ticks()
        if now - last_powerup_spawn > POWERUP_SPAWN_INTERVAL:
            px = random.randint(100, WORLD_WIDTH - 100)
            py = HEIGHT - GROUND_HEIGHT - POWERUP_RADIUS
            pickups.append(PowerupPickup(px, py))
            last_powerup_spawn = now

        # Move & update players
        for p in players:
            action = p.move(keys_pressed)
            if action == "throw" and p.has_powerup:
                vx = POWERUP_THROW_SPEED * p.facing
                vy = -POWERUP_THROW_SPEED * 0.8
                projectiles.append(Projectile(p.x + p.width//2, p.y + p.height//2, vx, vy, p))
                p.has_powerup = False
            p.update(obstacles)
            for pu in pickups:
                p.pickup_powerup_if_touching(pu)

        # Check punches
        check_punch(p1, p2)
        check_punch(p2, p1)

        # Update projectiles
        for proj in projectiles:
            proj.update(obstacles)
            handle_projectile_hit(proj, players)
        projectiles = [pr for pr in projectiles if pr.alive]

        # ======================
        # --- DRAW -------------
        # ======================
        win.fill(DARK_BLUE)
        offset1 = max(0, min(p1.x - HALF_W//2, WORLD_WIDTH - HALF_W))
        offset2 = max(0, min(p2.x - HALF_W//2, WORLD_WIDTH - HALF_W))

        # Left surface
        left_surface = pygame.Surface((HALF_W, HEIGHT))
        left_surface.fill(DARK_BLUE)
        pygame.draw.rect(left_surface, DARK_GREEN, (0, HEIGHT - GROUND_HEIGHT, HALF_W, GROUND_HEIGHT))
        for obs in obstacles:
            pygame.draw.rect(left_surface, DARK_GREEN, pygame.Rect(obs.x - offset1, obs.y, obs.width, obs.height))
        for proj in projectiles:
            proj.draw(left_surface, offset1)
        for pu in pickups:
            pu.draw(left_surface, offset1)
        p1.draw(left_surface, offset1)
        p2.draw(left_surface, offset1)
        win.blit(left_surface, (0,0))

        # Right surface
        right_surface = pygame.Surface((HALF_W, HEIGHT))
        right_surface.fill(DARK_BLUE)
        pygame.draw.rect(right_surface, DARK_GREEN, (0, HEIGHT - GROUND_HEIGHT, HALF_W, GROUND_HEIGHT))
        for obs in obstacles:
            pygame.draw.rect(right_surface, DARK_GREEN, pygame.Rect(obs.x - offset2, obs.y, obs.width, obs.height))
        for proj in projectiles:
            proj.draw(right_surface, offset2)
        for pu in pickups:
            pu.draw(right_surface, offset2)
        p1.draw(right_surface, offset2)
        p2.draw(right_surface, offset2)
        win.blit(right_surface, (HALF_W,0))

        # Divider
        pygame.draw.line(win, BLACK, (HALF_W,0), (HALF_W, HEIGHT), 4)

        # Bars
        for i, p in enumerate(players):
            x = 10 if i==0 else HALF_W + 10
            # HP
            pygame.draw.rect(win, p.color, (x,10, int(p.health*3), 20))
            pygame.draw.rect(win, BLACK, (x,10,300,20),2)
            # Crit
            pygame.draw.rect(win, YELLOW, (x,35,int(p.crit_charge/CRIT_THRESHOLD*300),10))
            pygame.draw.rect(win, BLACK, (x,35,300,10),2)
            # Stamina
            pygame.draw.rect(win, PURPLE, (x,50,int(p.stamina/100*300),10))
            pygame.draw.rect(win, BLACK, (x,50,300,10),2)

        # Win screen
        if not p1.alive or not p2.alive:
            text = "P1 Wins!" if p1.alive else "P2 Wins!"
            font = pygame.font.SysFont(None, 100)
            img = font.render(text, True, WHITE)
            win.blit(img, (WIDTH//2 - img.get_width()//2, HEIGHT//2 - img.get_height()//2))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main_menu()
