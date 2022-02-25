import pygame, enum, os, time, random, csv, button
from pygame import mixer

# INITIALIZATION
# ------------------------------------------------------------------------------------------------------------------------
pygame.init()
mixer.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')
clock = pygame.time.Clock()
FPS = 60
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLUMNS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3

screen_scroll = 0
bg_scroll = 0
level = 0
font = pygame.font.SysFont('Futura', 30)
start_game = False
start_intro = False



# colors
BG = (144, 201, 120)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PINK = (235, 65, 54)


# load music and sounds
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0)
#pygame.mixer.music.play(-1, 0.0, 0)

jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0)

shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0)

grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0)

# images
# store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()


start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()


bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
    'Health': health_box_img,
    'Ammo': ammo_box_img,
    'Grenade': grenade_box_img
}

# CLASSES
# ------------------------------------------------------------------------------------------------------------------------
class Velocity():
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Soldier(pygame.sprite.Sprite):
    def __init__(self, x, y, scale, speed, type, flipped, grenades_count):
        super().__init__()
        # variables
        self.alive = True
        self.type = type
        self.x = x
        self.y = y
        self.velocity = Velocity(0, 0)
        self.direction = 1
        self.speed = speed
        self.jump = False
        self.in_air = True
        self.flipped = flipped
        self.health = 100
        self.max_health = self.health

        # ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        # Bullets
        self.shooting = False
        self.shoot_cooldown = 0
        self.ammo = 20
        self.start_ammo = self.ammo

        # grenades
        self.grenade = False
        self.grenade_thrown = False
        self.grenades_count = grenades_count


        # animation variables
        self.animation_list = []
        self.animate_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks() # now


        # animation images
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for anim_type in animation_types:
            # reset temporary list of images
            temp_list = []
            # get number of files in the folder
            num_of_frames = len(os.listdir(f'img/{self.type}/{anim_type}'))
            # loop through each image/frame for the animations
            for i in range(num_of_frames):
                image = pygame.image.load(f'img/{self.type}/{anim_type}/{i}.png').convert_alpha()
                image = pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
                temp_list.append(image)
            self.animation_list.append(temp_list)


        # settings
        self.img = self.animation_list[self.action][self.animate_index]
        self.rect = self.img.get_rect()
        self.rect.center = (x, y)
        self.width = self.img.get_width()
        self.height = self.img.get_height()


    def update(self):
        self.update_animation()
        self.check_alive()
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1


    def move(self, moving_right, moving_left):
        screen_scroll = 0

        # update action
        if self.alive:
            if self.shooting:
                self.shoot()
            elif self.grenade and not self.grenade_thrown and self.grenades_count > 0:
                self.throw_grenade()
                self.grenade_thrown = True
                self.grenades_count -= 1
            if self.in_air:
                self.update_action(2) # 2: jumping
            elif moving_right or moving_left:
                self.update_action(1) # 1: running
            else:
                self.update_action(0) # 0: idle


        # reset movement variables
        dx = 0
        dy = 0

        # assign movement variables if moving left or right
        if moving_left:
            dx = -self.speed
            self.flipped = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flipped = False
            self.direction = 1

        # jump
        if self.jump and not self.in_air:
            self.velocity.y = -11
            self.jump = False
            self.in_air = True

        # apply gravity
        self.velocity.y += GRAVITY
        if self.velocity.y > 10:
            self.velocity.y
        dy += self.velocity.y

        # check for collision
        # x collision with objects
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                # if the ai has hit a wall then make it turn around
                if self.type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0


        # y collision
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # check if below the ground, i.e jumping
                if self.velocity.y < 0:
                    self.velocity.y = 0
                    dy = tile[1].bottom - self.rect.top
                # check if above the ground, i.e falling
                elif self.velocity.y >= 0:
                    self.velocity.y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        # check for collision with water or fallen off map 
        if pygame.sprite.spritecollide(self, water_group, False) or self.rect.y > SCREEN_HEIGHT:
            self.health = 0


        # check for collision with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # check if going off the edges of the screen
        if self.type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0


        # update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        # update scroll based on player position
        if self.type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        # update image depending on current frame
        self.img = self.animation_list[self.action][self.animate_index]

        # check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.animate_index += 1
            # if animation hasw run out then reset back to the start
            if self.animate_index >= len(self.animation_list[self.action]):
                if self.action == 3:
                    self.animate_index = len(self.animation_list[self.action]) - 1
                else:
                    self.animate_index = 0

    def update_action(self, new_action):
        # check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.animate_index = 0
            self.update_time = pygame.time.get_ticks()


    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0 :
            self.shoot_cooldown = 5
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
            bullet_group.add(bullet)
            self.ammo -= 1
            shot_fx.play()


    def throw_grenade(self):
        if not self.flipped:
            grenade = Grenade(player.rect.centerx + (player.rect.size[0] * 0.5), player.rect.centery, 1)
        else:
            grenade = Grenade(player.rect.centerx - (player.rect.size[0] * 0.5), player.rect.centery, -1)
        grenade_group.add(grenade)

    def ai(self):
        if self.alive and player.alive:
            if random.randint(1, 200) == 1 and not self.idling:
                self.update_action(0)  # 0: idle
                self.idling = True
                self.idling_counter = 50

            # check if the ai is near the player
            if self.vision.colliderect(player.rect):
                # stop running and shoot the player 
                self.update_action(0) # 0: Idle
                self.shoot()
            # if ai doesnt see player
            else:
                if not self.idling:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_right, ai_moving_left)
                    self.update_action(1)
                    self.move_counter += 1

                    # update ai vision as the enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        # scroll
        self.rect.x += screen_scroll


    def draw(self):
        if self.flipped:
            screen.blit(pygame.transform.flip(self.img, True, False), self.rect)
        else:
            screen.blit(self.img, self.rect)

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)
            return False
        else:
            return True

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # move bullet
            
        self.rect.x += (self.direction * self.speed)

        # check bounds
        # offscreen
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.kill()

        # check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # player collisions
        if pygame.sprite.spritecollide(player, bullet_group, False) and player.alive:
            player.health -= 20
            self.kill()

        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False) and enemy.alive:
                enemy.health -= 40
                self.kill()

class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.velocity = Velocity(0, -11)
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self):
        self.velocity.y += GRAVITY


        dx = self.direction * self.speed
        dy = self.velocity.y

        # check collision 
        #x collision
        for tile in world.obstacle_list:
            # check collsion with walls
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed

        # y collision
        for tile in world.obstacle_list:
            if tile [1].colliderect(self.rect.x + dy, self.rect.y, self.width, self.height):
                self.speed = 0
                # check if below the ground, i.e thrown up
                if self.velocity.y < 0:
                    self.velocity.y = 0
                    dy = tile[1].bottom - self.rect.top
                # check if above the ground, i.e falling
                elif self.velocity.y >= 0:
                    self.velocity.y = 0
                    dy = tile[1].top - self.rect.bottom

        self.rect.x += dx
        self.rect.y += dy

        # countdown timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_fx.play()
            explosion = Explosion(self.rect.x, self.rect.y, 0.5)
            explosion_group.add(explosion)
            # do damage to anyone that is nearby 
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 50


            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        #3 scroll
        self.rect.x += screen_scroll
        EXPLOSION_SPEED = 4
        # update explosion animation
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            # if animation is complete
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        super().__init__()
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE//2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        # scroll
        self.rect.x += screen_scroll

        # check if the player has picked up the box
        if pygame.sprite.collide_rect(self, player):
            # check what kind of box
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades_count += 3
            # delete item box
            self.kill()

class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        self.health = health
        # calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        # iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile == 9 or tile == 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif 11 <= tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:
                        player = Soldier(x * TILE_SIZE, y * TILE_SIZE, 1.65, 8, 'player', False, 5)
                        health_bar = HealthBar(130, 13, player.health, player.max_health)
                    elif tile == 16:
                        enemy = Soldier(x * TILE_SIZE, y * TILE_SIZE, 1.65, 4, 'enemy', True, 0)
                        enemy_group.add(enemy)
                    elif tile == 17: # ammo box
                        ammo_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(ammo_box)
                    elif tile == 18:
                        health_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(health_box)
                    elif tile == 19: 
                        grenade_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(grenade_box)
                    elif tile == 20:
                        exit = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])

class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE//2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE//2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):

    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE//2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class ScreenFade():
    def __init__(self, direction, color, speed):
        self.direction = direction 
        self.color = color
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed

        if self.direction == 1: # whole screen fade
            pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.color, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2: # vertical screen fade down
            pygame.draw.rect(screen, self.color, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True

        return fade_complete


# FUNCTIONS
# ------------------------------------------------------------------------------------------------------------------------
def draw_background():
    screen.fill(BG)
    width = sky_img.get_width()
    for i in range(5):
        screen.blit(sky_img, (width * i - bg_scroll * 0.5, 0))
        screen.blit(mountain_img, (width * i - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, (width * i - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, (width * i - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

def draw_text(text, font, color, x, y):
    # drawing text
    img = font.render(text, 1, color)
    screen.blit(img, (x, y))
    
def reset_level():
    # delete groups
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLUMNS
        data.append(r)

    return data


# GAME LOOP
# ------------------------------------------------------------------------------------------------------------------------
# create sprite groups
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# create buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

# create screen fades
intro_fade = ScreenFade(1, BLACK, 20)
death_fade = ScreenFade(2, PINK, 14)


moving_right = False
moving_left = False


# tile map
# create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLUMNS
    world_data.append(r)
# load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)

quit = False
gameover = False
while not quit:
    clock.tick(FPS)

    if start_game == False:
        # draw menu
        screen.fill(BG)
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            quit = True
    else:

        draw_background()
        world.draw()
        # show ammo
        draw_text(f'Health: {player.health}', font, RED, 10, 15)
        health_bar.draw(player.health)
        draw_text(f'Ammo: {player.ammo}', font, RED, 10, 40)
        for i in range(player.ammo):
            screen.blit(bullet_img, (120 + (i * 10), 43))
        draw_text(f'Grenades: {player.grenades_count}', font, RED, 10, 65)
        for i in range(player.grenades_count):
            screen.blit(grenade_img, (140 + (i * 10), 70))

        # update and draw groups
        bullet_group.update()
        bullet_group.draw(screen)

        grenade_group.update()
        grenade_group.draw(screen)

        explosion_group.update()
        explosion_group.draw(screen)

        item_box_group.update()
        item_box_group.draw(screen)

        water_group.update()
        water_group.draw(screen)

        decoration_group.update()
        decoration_group.draw(screen)

        exit_group.update()
        exit_group.draw(screen)


        # show intro 
        if start_intro:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0


        player.update()
        screen_scroll, level_complete = player.move(moving_right, moving_left)
        bg_scroll -= screen_scroll
        player.draw()
        player.check_alive()

        # check if player has completed the level
        if level_complete:
            start_intro = True
            level += 1
            bg_scroll = 0
            world_data = reset_level()
            if level <= MAX_LEVELS:
                # reload the world on the same level and recreate player
                with open(f'level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data)
                moving_left = False
                moving_right = False

        if not player.alive:
            screen_scroll = 0
            enemy_group.empty()
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    bg_scroll = 0
                    world_data = reset_level()
                    # reload the world on the same level and recreate player
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)
                    moving_left = False
                    moving_right = False


        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()


        if not player.alive and not enemy.alive:
            gameover = True

        
    # Event Handling
    for event in pygame.event.get():
        # quit game
        if event.type == pygame.QUIT:
            quit = True
        # PLAYER ----------------------------
        # keyboard presses
        if player.alive:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit = True
                if event.key == pygame.K_a:
                    moving_left = True
                    player.flipped = True
                if event.key == pygame.K_d:
                    moving_right = True
                    player.flipped = False
                if event.key == pygame.K_w and player.alive:
                    player.jump = True
                    jump_fx.play()
                if event.key == pygame.K_SPACE and player.alive:
                    player.shooting = True
                if event.key == pygame.K_q:
                    player.grenade = True

            # keyboard button released
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    moving_left = False
                if event.key == pygame.K_d:
                    moving_right = False
                if event.key == pygame.K_SPACE and player.alive:
                    player.shooting = False
                if event.key == pygame.K_q:
                    player.grenade = False
                    player.grenade_thrown = False
    pygame.display.update()
            
pygame.quit()





    
                

        
