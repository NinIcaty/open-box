from main import  *
# ======================
# --- PLAYER CLASS -----
# ======================
class Player:
    def __init__(self, x, y, color, keys):
        self.x = x
        self.y = y
        self.color = color
        self.keys = keys
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.normal_height = PLAYER_HEIGHT
        self.duck_height = int(self.normal_height * 0.6)
        self.vy = 0
        self.speed = PLAYER_SPEED
        self.jump_power = JUMP_POWER
        self.on_ground = False
        self.facing = 1
        self.ducking = False
        self.sprinting = False
        self.health = 100.0
        self.crit_charge = 0
        self.crit_ready = False
        self.punching = False
        self.punch_start = 0
        self.has_hit = False
        self.last_punch_time = -9999
        self.stamina = STAMINA_MAX
        self.has_powerup = False
        self.alive = True

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def move(self, keys_pressed):
        if not self.alive: return
        self.ducking = keys_pressed[self.keys[4]]
        self.sprinting = keys_pressed[self.keys[5]]
        current_speed = SPRINT_SPEED if self.sprinting and not self.ducking and self.stamina > 0 else self.speed
        if not self.ducking:
            if keys_pressed[self.keys[0]]:
                self.x -= current_speed
                self.facing = -1
            if keys_pressed[self.keys[1]]:
                self.x += current_speed
                self.facing = 1
        self.x = max(0, min(self.x, WORLD_WIDTH - self.width))
        if keys_pressed[self.keys[2]] and self.on_ground and not self.ducking:
            self.vy = -self.jump_power
            self.on_ground = False
        now = pygame.time.get_ticks()

        if keys_pressed[self.keys[3]] and not self.punching and now - self.last_punch_time > PUNCH_COOLDOWN and not self.ducking and not self.has_powerup:
            self.punching = True
            self.punch_start = now
            self.has_hit = False
            self.last_punch_time = now
            self.crit_ready = False
            self.crit_charge = 0
        if self.punching and now - self.punch_start > PUNCH_DURATION:
            self.punching = False
        if keys_pressed[self.keys[6]] and self.has_powerup:
            return "throw"

    def update(self, obstacles):
        if not self.alive:
            return
        self.vy += 1.0
        self.y += self.vy
        # Ground collision
        ground_y = HEIGHT - GROUND_HEIGHT - self.height
        self.on_ground = False
        if self.y >= ground_y:
            self.y = ground_y
            self.vy = 0
            self.on_ground = True
        # Obstacle collision
        for obs in obstacles:
            if self.rect().colliderect(obs):
                if self.vy > 0 and (self.y + self.height - self.vy) <= obs.y + 5:
                    self.y = obs.y - self.height
                    self.vy = 0
                    self.on_ground = True
        # Duck
        if self.ducking:
            if self.height != self.duck_height:
                diff = self.normal_height - self.duck_height
                self.y += diff
                self.height = self.duck_height
            self.stamina += STAMINA_REGEN
            if self.stamina > STAMINA_MAX:
                self.stamina = STAMINA_MAX
        else:
            if self.height != self.normal_height:
                diff = self.normal_height - self.duck_height
                self.y -= diff
                self.height = self.normal_height
        # Sprint stamina loss
        if self.sprinting and not self.ducking and self.stamina > 0:
            self.stamina -= SPRINT_STAMINA_DRAIN
            if self.stamina < 0: self.stamina = 0
        # HP regen
        regen_happened = False
        if not self.punching and not self.ducking and not self.sprinting and self.health < 100.0:
            self.health += REGEN_PER_FRAME
            if self.health > 100.0: self.health = 100.0
            self.stamina -= 0.05
            if self.stamina < 0: self.stamina = 0.0
            regen_happened = True
        # Crit charge
        if (not self.punching and not self.ducking and not self.sprinting and not regen_happened and self.stamina >= STAMINA_MAX*CRIT_STAMINA_REQUIRED_PCT):
            self.crit_charge += 1
            if self.crit_charge >= CRIT_THRESHOLD:
                self.crit_ready = True
                self.crit_charge = CRIT_THRESHOLD
        # Death
        if self.health <= 0 :#and self.alive:
            self.alive = False

    def pickup_powerup_if_touching(self, pickup):
        if pickup.active and pickup.rect.colliderect(self.rect()):
            pickup.active = False
            self.has_powerup = True

    def draw(self, surface, offset):
        x = int(self.x - offset)
        y = int(self.y)
        color = self.color if self.alive else GREY
        pygame.draw.rect(surface, color, (x, y, int(self.width), int(self.height)))
        eye_y = y + int(self.height * 0.25)
        eye_x = x + (int(self.width) - 8 if self.facing == 1 else 8)
        pygame.draw.circle(surface, BLACK, (eye_x, eye_y), max(3, int(self.width * 0.08)))

        # punch
        if self.punching:
            arm_len = int(self.width * 0.45)
            arm_y = y + int(self.height * 0.35)
            arm_color = PURPLE if self.crit_ready else ((255,100,100) if self.color == RED else (100,100,255))
            if self.facing == 1:
                pygame.draw.rect(surface, arm_color, (x + int(self.width), arm_y, arm_len, max(6, int(self.height*0.06))))
            else:
                pygame.draw.rect(surface, arm_color, (x - arm_len, arm_y, arm_len, max(6, int(self.height*0.06))))
        #Draw powerup in hand
        if self.has_powerup:
            ball_radius = POWERUP_RADIUS
            # Show ball
            if self.facing == 1:
                ball_x = x + self.width + ball_radius -2 # right hand
            else:
                ball_x = x - ball_radius - 2  # left hand, slightly closer
            ball_y = y + int(self.height * 0.35)
            pygame.draw.circle(surface, ORANGE, (ball_x, ball_y), ball_radius)
            pygame.draw.circle(surface, BLACK, (ball_x, ball_y), ball_radius // 2)
