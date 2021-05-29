import pygame, enum, os, time

# INITIALIZATION
# ------------------------------------------------------------------------------------------------------------------------
pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')
clock = pygame.time.Clock()
FPS = 60
BG = (144, 201, 120)
GRAVITY = 0.75

def draw_background():
    screen.fill(BG)
    pygame.draw.line(screen, (255, 0, 0), (0, 300), (SCREEN_WIDTH, 300))

bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
win_img = pygame.image.load('img/winner.png').convert_alpha()

# CLASSES
# ------------------------------------------------------------------------------------------------------------------------



class Velocity():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        

class Direction(enum.Enum):
    Up = 0
    Right = 1
    Down = 2
    Left = 3
    Aucun = 4

class Soldier(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, type, flipped):
        super().__init__()
        # variables
        self.alive = True
        self.type = type
        self.x = x
        self.y = y
        self.velocity = Velocity(0, 0)
        self.width = width
        self.height = height
        self.direction = Direction.Aucun
        self.acceleration = 10
        self.jump = False
        self.in_air = True
        self.shooting = False
        self.flipped = flipped
        self.shoot_cooldown = 0
        self.ammo = 20
        self.start_ammo = self.ammo
        self.health = 100
        self.max_health = self.health

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
                image = pygame.transform.scale(image, (self.width, self.height))
                temp_list.append(image)
            self.animation_list.append(temp_list)


        # settings
        self.img = self.animation_list[self.action][self.animate_index]
        self.rect = self.img.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.update_animation()
        self.check_alive()
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1


    def move(self):
        # update action
        if self.alive:
            if self.shooting:
                self.shoot()

            if self.in_air:
                self.update_action(2) # 2: jumping
            elif self.direction is not Direction.Aucun:
                self.update_action(1) # 1: running
            else:
                self.update_action(0) # 0: idle


        # reset movement variables
        dx = 0
        dy = 0

        # assign movement variables if moving left or right
        if self.direction == Direction.Left:
            dx = -self.acceleration
        if self.direction == Direction.Right:
            dx = self.acceleration

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

        # check collision with floor
        if self.rect.bottom + dy > 300:
            dy = 300 - self.rect.bottom
            self.in_air = False

        # update rectangle position
        self.rect.x += dx
        self.rect.y += dy

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

            if not self.flipped:
                bullet = Bullet(self.rect.centerx + (0.55 * self.rect.size[0]), self.rect.centery, Direction.Right)
            else:
                bullet = Bullet(self.rect.centerx - (0.55 * self.rect.size[0]), self.rect.centery, Direction.Left)
            bullet_group.add(bullet)
            self.ammo -= 1


    def draw(self):
        if self.flipped:
            screen.blit(pygame.transform.flip(self.img, True, False), self.rect)
        else:
            screen.blit(self.img, self.rect)

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.acceleration = 0
            self.alive = False
            self.update_action(3)
            return False
        else:
            return True


# create sprite groups
bullet_group = pygame.sprite.Group()
player = Soldier(200, 200, 170, 200, 'player', False)
enemy = Soldier(600, 200, 170, 200, 'enemy', True)

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
        dir = 0
        if self.direction == Direction.Left:
            dir = -1
        else:
            dir = 1
            
        self.rect.x += (dir * self.speed)

        # check bounds
        # offscreen
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.kill()

        # player collisions
        if pygame.sprite.spritecollide(player, bullet_group, False) and player.alive:
            player.health -= 20
            self.kill()

        if pygame.sprite.spritecollide(enemy, bullet_group, False) and enemy.alive:
            enemy.health -= 40
            self.kill()



# GAME LOOP
# ------------------------------------------------------------------------------------------------------------------------

def draw_text(text, font, color, x, y):
    # drawing text
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    screen.blit(textobj, textrect)

def main_menu():
    # white color 
    color = (255,255,255)

    # light shade of the button 
    color_light = (170,170,170) 
    
    # dark shade of the button 
    color_dark = (100,100,100)

    # defining a font 
    smallfont = pygame.font.SysFont('Corbel',35) 
  
 

    # Start Button Rect
    start_button = pygame.Rect((SCREEN_WIDTH/2, SCREEN_HEIGHT/2), (200,40))
    start_button.center = screen.get_rect().center

    one = pygame.image.load('img/numbers/uno.png')
    one = pygame.transform.scale(one, (80, 80))
    two = pygame.image.load('img/numbers/dos.png')
    two = pygame.transform.scale(two, (80, 80))
    three = pygame.image.load('img/numbers/tres.png')
    three = pygame.transform.scale(three, (80, 80))
    four = pygame.image.load('img/numbers/cuatro.png')
    four = pygame.transform.scale(four, (80, 80))
    five = pygame.image.load('img/numbers/cinco.png')
    five = pygame.transform.scale(five, (80, 80))
    countdown = 5

    # rendering a text written in 
    # this font 
    text = smallfont.render('Start Game' , True , color)
    text.get_rect().center = start_button.center

    start = False
    startTime = pygame.time.get_ticks()

    while True: 
      
        for ev in pygame.event.get(): 
            
            if ev.type == pygame.QUIT: 
                pygame.quit() 
                
            #checks if a mouse is clicked 
            if ev.type == pygame.MOUSEBUTTONDOWN: 
                
                #if the mouse is clicked on the 
                # button the game is terminated 
                if start_button.collidepoint(mouse): 
                    start = True
                    startTimer = pygame.time.get_ticks()
                    
        # fills the screen with a color 
        screen.fill((60,25,60)) 
        
        # stores the (x,y) coordinates into 
        # the variable as a tuple 
        mouse = pygame.mouse.get_pos() 
        
        # if mouse is hovered on a button it 
        # changes to lighter shade 
        if start_button.collidepoint(mouse): 
            pygame.draw.rect(screen, color_light, start_button) 
            
        else: 
            pygame.draw.rect(screen, color_dark, start_button) 
        

        # superimposing the text onto our button 
        screen.blit(text, (start_button.left, start_button.top)) 


        # Images
        playerimg = pygame.image.load('img/player/Jump/0.png')
        playerimg = pygame.transform.scale(playerimg, (200, 200))
        playerimg = pygame.transform.rotate(playerimg, 16)

        enemyimg = pygame.image.load('img/enemy/Run/1.png')
        enemyimg = pygame.transform.scale(enemyimg, (200, 200))
        enemyimg = pygame.transform.rotate(enemyimg, 16)
        enemyimg = pygame.transform.flip(enemyimg, True, False)

        expolosionimg = pygame.image.load('img/explosion/exp2.png')
        expolosionimg = pygame.transform.scale(expolosionimg, (300, 300))

        daemonimg = pygame.image.load('img/daemon.png')
        daemonimg = pygame.transform.scale(daemonimg, (300, 400))

        screen.blit(playerimg, (100, 500))
        screen.blit(enemyimg, (700, 100))
        screen.blit(expolosionimg, (700, 500))
        screen.blit(daemonimg, (50, 30))
        

        # if game is starting
        if start:

            if pygame.time.get_ticks() - startTime > 1000:
                startTime = pygame.time.get_ticks()
                countdown -= 1

            if countdown == 5:
                screen.blit(five, (SCREEN_WIDTH/2, SCREEN_HEIGHT - 100))
            elif countdown == 4:
                screen.blit(four, (SCREEN_WIDTH/2, SCREEN_HEIGHT - 100))
            elif countdown == 3:
                screen.blit(three, (SCREEN_WIDTH/2, SCREEN_HEIGHT - 100))
            elif countdown == 2:
                screen.blit(two, (SCREEN_WIDTH/2, SCREEN_HEIGHT - 100))
            elif countdown == 1:
                screen.blit(one, (SCREEN_WIDTH/2, SCREEN_HEIGHT - 100))
            elif countdown <= 0:
                game()

        
        # updates the frames of the game 
        pygame.display.update()

    

def game():
    quit = False
    gameover = False
    while not quit:
        clock.tick(FPS)
        draw_background()

        # Event Handling
        for event in pygame.event.get():
            # quit game
            if event.type == pygame.QUIT:
                quit = True
            # PLAYER1 ----------------------------
            # keyboard presses
            if player.alive:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        quit = True
                    if event.key == pygame.K_a:
                        player.direction = Direction.Left
                        player.flipped = True
                    if event.key == pygame.K_d:
                        player.direction = Direction.Right
                        player.flipped = False
                    if event.key == pygame.K_w and player.alive:
                        player.jump = True
                    if event.key == pygame.K_SPACE and player.alive:
                        player.shooting = True

                # keyboard button released
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        player.direction = Direction.Aucun
                    if event.key == pygame.K_d:
                        player.direction = Direction.Aucun
                    if event.key == pygame.K_SPACE and player.alive:
                        player.shooting = False

            # PLAYER2 -----------------------------------
            # keyboard presses
            if enemy.alive:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        quit = True
                    if event.key == pygame.K_LEFT:
                        enemy.direction = Direction.Left
                        enemy.flipped = True
                    if event.key == pygame.K_RIGHT:
                        enemy.direction = Direction.Right
                        enemy.flipped = False
                    if event.key == pygame.K_UP and enemy.alive:
                        enemy.jump = True
                    if event.key == pygame.K_RCTRL and enemy.alive:
                        enemy.shooting = True

                # keyboard button released
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        enemy.direction = Direction.Aucun
                    if event.key == pygame.K_RIGHT:
                        enemy.direction = Direction.Aucun
                    if event.key == pygame.K_RCTRL and enemy.alive:
                        enemy.shooting = False

        
        # update and draw groups
        bullet_group.update()
        bullet_group.draw(screen)

        # player and enemy actions
        player.update()
        player.move()
        player.draw()

        enemy.update()
        enemy.move()
        enemy.draw()


        if check_winner() and not gameover:
            gameover = True

        # Draw HUD
        
        
        pygame.display.update()
                
    pygame.quit()

def check_winner():
    font = pygame.font.SysFont("Arial", 40)

    if not player.check_alive():
            draw_text('Player 2 Has Won!', font, (128, 0, 0), SCREEN_WIDTH/2  - 100, 60)
            return True
    elif not enemy.check_alive():
            draw_text('Player 1 Has Won!', font, (0, 128, 0), SCREEN_WIDTH/2  - 100, 60)
            return True



    
                

        

main_menu()