import pygame
import button
import csv
import pickle

# INITIALIZATION
# -----------------------------------------------------------------------------------------
pygame.init()

clock = pygame.time.Clock()
FPS = 60

# game window
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640
LOWER_MARGIN = 100
SIDE_MARGIN = 300

screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN))
pygame.display.set_caption('Level Editor')

# define game variables
NUM_ROWS = 16  
MAX_COLUMNS = 150
TILE_SIZE = SCREEN_HEIGHT // NUM_ROWS
TILE_TYPES = 21

max_levels = 100
level = 0
current_tile = 0
scroll_left = False
scroll_right = False
scroll = 0
scroll_speed = 1


# Images
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()
save_img = pygame.image.load('img/save_btn.png').convert_alpha()
load_img = pygame.image.load('img/load_btn.png').convert_alpha()


# store tile in a list
img_list = []
for i in range(TILE_TYPES):
    img = pygame.image.load(f'img/tile/{i}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

 
# define colors
black = (0, 0, 0)
green = (144, 201, 120)
white = (255, 255, 255)
red = (200, 25, 25)
yellow = (255, 255, 0)
white = (255, 255, 255)

# define font
font = pygame.font.SysFont('Futura', 30)

# creat empty tile list
world_data = []
for r in range(NUM_ROWS):
    row = [-1] * MAX_COLUMNS
    world_data.append(row)

# create ground
for tile in range(0, MAX_COLUMNS):
    world_data[NUM_ROWS - 1][tile] = 0




# FUNCTIONS
# -----------------------------------------------------------------------------------------

def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def draw_bg():
    screen.fill(green)
    width = sky_img.get_width()
    for i in range(6):
        screen.blit(sky_img, ((i * width) - scroll * 0.5, 0))
        screen.blit(mountain_img, ((i * width) - scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((i * width) - scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((i * width) - scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

def draw_grid():
    # vertical lines
    for c in range(MAX_COLUMNS + 1):
        pygame.draw.line(screen, white, (c * TILE_SIZE - scroll, 0), (c * TILE_SIZE - scroll, SCREEN_HEIGHT))
    # horizontal lines
    for r in range(NUM_ROWS + 1):
        pygame.draw.line(screen, white, (0, r * TILE_SIZE), (SCREEN_WIDTH, r * TILE_SIZE))

def draw_world():
    for y, row in enumerate(world_data):
        for x, tile in enumerate(row):
            if tile >= 0:
                screen.blit(img_list[tile], (x * TILE_SIZE - scroll, y * TILE_SIZE))


# CLASSES
# -----------------------------------------------------------------------------------------

# GAME LOOP
# -----------------------------------------------------------------------------------------

# create buttons
save_button = button.Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT + LOWER_MARGIN - 70, save_img, 1)
load_button = button.Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT + LOWER_MARGIN - 70, load_img, 1)


button_list = []
button_column = 0
button_row = 0

for i in range(len(img_list)):
    tile_button = button.Button(SCREEN_WIDTH + (75 * button_column) + 50, 75 * button_row + 50, img_list[i], 1)
    button_list.append(tile_button)
    button_column += 1
    if button_column == 3:
        button_row += 1
        button_column = 0

run = True
while run:
    clock.tick(FPS)
    draw_bg()
    draw_grid()
    draw_world()
    draw_text(f'Level: {level}', font, black, 10, SCREEN_HEIGHT + LOWER_MARGIN - 90)
    draw_text(f'Press UP or DOWN to change level', font, black, 10, SCREEN_HEIGHT + LOWER_MARGIN - 60)

    # save and load data
    if save_button.draw(screen):
        # save level data
        with open(f'level{level}_data.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            for row in world_data:
                writer.writerow(row)

    if load_button.draw(screen):
        # load in level data
        # reset scroll back to the start of the level
        scroll = 0

        with open(f'level{level}_data.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    world_data[x][y] = int(tile)

    pygame.draw.rect(screen, green, (SCREEN_WIDTH, 0, SIDE_MARGIN, SCREEN_HEIGHT))

    # choose a tile
    button_count = 0
    for button_count, but in enumerate(button_list):
        if but.draw(screen):
            current_tile = button_count
    
    # highlight selected tile
    pygame.draw.rect(screen, red, button_list[current_tile].rect, 3)

    # scroll the map
    if scroll_left == True and scroll > 0:
        scroll -= 5 * scroll_speed
    if scroll_right == True:
        scroll += 5 * scroll_speed


    # add new tiles to the screen
    # get mouse position
    mouse_pos = pygame.mouse.get_pos()
    x = (mouse_pos[0] + scroll) // TILE_SIZE
    y = mouse_pos[1] // TILE_SIZE

    # check that the coordinates are within the tile area
    if mouse_pos[0] < SCREEN_WIDTH and mouse_pos[1] < SCREEN_HEIGHT:
        # update tile value
        if pygame.mouse.get_pressed()[0] == 1:
            if world_data[y][x] != current_tile:
                world_data[y][x] = current_tile
        if pygame.mouse.get_pressed()[2] == 1:
            world_data[y][x] = -1
    # events
    for event in pygame.event.get():
        # quit
        if event.type == pygame.QUIT:
            run = False

        # keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and level <= max_levels:
                level += 1
            if event.key == pygame.K_DOWN and level > 0:
                level -= 1
            if event.key == pygame.K_LEFT:
                scroll_left = True
            if event.key == pygame.K_RIGHT:
                scroll_right = True
            if event.key == pygame.K_RCTRL:
                scroll_speed = 5

        # keyboard release
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                scroll_left = False
            if event.key == pygame.K_RIGHT:
                scroll_right = False
            if event.key == pygame.K_RCTRL:
                scroll_speed = 1

    pygame.display.update()


pygame.quit()