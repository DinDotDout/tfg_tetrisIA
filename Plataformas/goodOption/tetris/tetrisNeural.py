import pygame
import random
import sys

pygame.font.init()

# GLOBALS VARS
s_width = 750
s_height = 650
play_width = 300  # meaning 300 // 10 = 30 width per block
play_height = 600  # meaning 600 // 20 = 30 height per block
block_size = 30

top_left_x = (s_width - play_width) // 2
top_left_y = s_height - play_height


# SHAPE FORMATS

S = [['.....',
      '.....',
      '..00.',
      '.00..',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '...0.',
      '.....']]

Z = [['.....',
      '.....',
      '.00..',
      '..00.',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '.0...',
      '.....']]

I = [['.....',
      '0000.',
      '.....',
      '.....',
      '.....'],
     ['..0..',
      '..0..',
      '..0..',
      '..0..',
      '.....'],
     ]

O = [['.....',
      '.....',
      '.00..',
      '.00..',
      '.....']]

J = [['.....',
      '.0...',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..00.',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '...0.',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '.00..',
      '.....']]

L = [['.....',
      '...0.',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '..00.',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '.0...',
      '.....'],
     ['.....',
      '.00..',
      '..0..',
      '..0..',
      '.....']]

T = [['.....',
      '..0..',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '..0..',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '..0..',
      '.....']]

shapes = [S, Z, I, O, L, J, T]
shape_colors = [(0, 255, 0), (255, 0, 0), (0, 255, 255),
                (255, 255, 0), (255, 165, 0), (0, 0, 255), (128, 0, 128)]
# index 0 - 6 represent shape


class Piece(object):  # *
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = shape_colors[shapes.index(shape)]
        self.rotation = 0


def create_grid(locked_pos={}):  # *
    grid = [[(0, 0, 0) for _ in range(10)] for _ in range(20)]

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if (j, i) in locked_pos:
                c = locked_pos[(j, i)]
                grid[i][j] = c
    return grid


def convert_shape_format(shape):
    positions = []
    format = shape.shape[shape.rotation % len(shape.shape)]

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                positions.append((shape.x + j, shape.y + i))

    for i, pos in enumerate(positions):
        positions[i] = (pos[0] - 2, pos[1] - 4)
    return positions


def valid_space(shape, grid):
    accepted_pos = [[(j, i) for j in range(10) if grid[i][j] == (0, 0, 0)] for i in range(20)]
    accepted_pos = [j for sub in accepted_pos for j in sub]

    formatted = convert_shape_format(shape)
    
    for pos in formatted:
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
    return True


def valid_space_rotation(shape, grid):
    accepted_pos = [[(j, i) for j in range(10) if grid[i]
                     [j] == (0, 0, 0)] for i in range(20)]
    accepted_pos = [j for sub in accepted_pos for j in sub]

    formatted = convert_shape_format(shape)

    for pos in formatted:
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
    return True


def check_lost(positions):
    for pos in positions:
        x, y = pos
        if y < 1:
            return True

    return False


def get_shape(n):
    if shapes[n] == 2 or shapes[n] == 3:
        return Piece(5, 3, shapes[n])
    return Piece(4, 3, shapes[n])


def draw_text_middle(surface, text, size, color):
    font = pygame.font.SysFont("comicsans", size, bold=True)
    label = font.render(text, 1, color)

    surface.blit(label, (top_left_x + play_width / 2 - (label.get_width()/2),
                         top_left_y + play_height/2 - label.get_height()/2))


def draw_grid(surface, grid):
    sx = top_left_x
    sy = top_left_y

    for i in range(len(grid)):
        pygame.draw.line(surface, (128, 128, 128), (sx, sy +
                                                    i*block_size), (sx+play_width, sy + i*block_size))
        for j in range(len(grid[i])):
            pygame.draw.line(surface, (128, 128, 128), (sx + j *
                                                        block_size, sy), (sx + j*block_size, sy + play_height))


def clear_rows(grid, locked):

    inc = 0
    for i in range(len(grid)-1, -1, -1):
        row = grid[i]
        if (0, 0, 0) not in row:
            inc += 1
            ind = i
            for j in range(len(row)):
                try:
                    del locked[(j, i)]
                except:
                    continue

    if inc > 0:
        for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < ind:
                newKey = (x, y + inc)
                locked[newKey] = locked.pop(key)

    return inc


def draw_next_shape(shapes, surface):
    # shape = get_shape(shapes[0])
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render('Next Shape', 1, (255, 255, 255))

    sx = top_left_x + play_width + 50
    sy = top_left_y + play_height/2 - 300
    surface.blit(label, (sx + 10, sy))
    for k in range(6):
        shape = get_shape(shapes[k])
        format = shape.shape[shape.rotation % len(shape.shape)]
        for i, line in enumerate(format):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    draw_shape(shape, surface, sx + j *
                               block_size, sy + i*block_size)
        sy += 91


def draw_shape(shape, surface, posX, posY):
    if(shape.shape == S or shape.shape == Z or shape.shape == O):
        pygame.draw.rect(surface, shape.color,
                         (posX, posY, block_size, block_size), 0)
    else:
        pygame.draw.rect(surface, shape.color, (posX, posY +
                                                block_size, block_size, block_size), 0)


def swap_piece(piece, surface):
    sx = top_left_x - 200
    sy = top_left_y + 50
    format = piece.shape[piece.rotation % len(piece.shape)]
    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                draw_shape(piece, surface, sx + j *
                           block_size, sy + i*block_size)


def update_score(nscore):
    score = max_score()

    with open('scores.txt', 'w') as f:
        if int(score) > nscore:
            f.write(str(score))
        else:
            f.write(str(nscore))


def max_score():
    with open('scores.txt', 'r') as f:
        lines = f.readlines()
        if lines:
            score = lines[0].strip()
        else:
            score = "0"
    return score


def draw_window(surface, grid, score=0, last_score=0):
    surface.fill((0, 0, 0))

    pygame.font.init()
    font = pygame.font.SysFont('comicsans', 60)
    label = font.render('Tetris', 1, (255, 255, 255))

    surface.blit(label, (top_left_x + play_width /
                         2 - (label.get_width() / 2), 5))

    # current score
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render('Score: ' + str(score), 1, (255, 255, 255))

    sx = top_left_x - 200
    sy = top_left_y + 200

    surface.blit(label, (sx + 20, sy + 160))
    # last score
    label = font.render('High Score: ' + last_score, 1, (255, 255, 255))

    sx = top_left_x - 200
    sy = top_left_y + 100

    surface.blit(label, (sx + 20, sy + 160))

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            pygame.draw.rect(surface, grid[i][j], (top_left_x + j*block_size,
                                                   top_left_y + i*block_size, block_size, block_size), 0)

    pygame.draw.rect(surface, (255, 0, 0), (top_left_x,
                                            top_left_y, play_width, play_height), 5)

    draw_grid(surface, grid)
    # pygame.display.update()


def main(win):  # *
    last_score = max_score()
    locked_positions = {}
    grid = create_grid(locked_positions)

    change_piece = False
    save_piece = False
    already_saved = False
    run = True
    ordered_index = [0, 1, 2, 3, 4, 5, 6]  # original list
    piece_array = ordered_index[:]  # list we will work on
    added_pieces = ordered_index[:]  # list of the next 6 pieces we add
    next_addition = 5   # n off turns we will need to refill list

    random.shuffle(piece_array)  # shuffle list
    random.shuffle(added_pieces)  # shuffle list

    piece_array.extend(added_pieces)  # add extra pieces to the beginning

    current_piece = get_shape(piece_array.pop(0))  # get current piece
    saved_piece = None
    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 1
    level_time = 0
    score = 0

    while run:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        level_time += clock.get_rawtime()
        clock.tick()

        if level_time/1000 > 5:
            level_time = 0
            if level_time > 0.12:
                level_time -= 0.005

        if fall_time/1000 > fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not(valid_space(current_piece, grid)) and current_piece.y > 0:
                current_piece.y -= 1
                change_piece = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                # pygame.display.quit()
                # pygame.quit()
                # exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_LEFT:  # Move left
                    current_piece.x -= 1
                    if not(valid_space(current_piece, grid)):
                        current_piece.x += 1
                if event.key == pygame.K_RIGHT:  # Move right
                    current_piece.x += 1
                    if not(valid_space(current_piece, grid)):
                        current_piece.x -= 1
                if event.key == pygame.K_DOWN:  # Move down
                    current_piece.y += 1
                    if not(valid_space(current_piece, grid)):
                        current_piece.y -= 1
                if event.key == pygame.K_UP:  # Drop piece
                    current_piece.y += 1
                    while (valid_space(current_piece, grid)):
                        current_piece.y += 1
                    current_piece.y -= 1

                if event.key == pygame.K_d:  # Rotate right
                    current_piece.rotation += 1
                    if not(valid_space(current_piece, grid)):
                        current_piece.rotation -= 1
                if event.key == pygame.K_a:  # Rotate left
                    current_piece.rotation -= 1
                    if not(valid_space(current_piece, grid)):
                        current_piece.rotation += 1
                if event.key == pygame.K_SPACE:  # Save piece
                    save_piece = True

            # if event.type == pygame.KEYUP:
            #     if event.key == pygame.K_LEFT:
            #         current_piece.x -= 1
            #         if not(valid_space(current_piece, grid)):
            #             current_piece.x += 1
            #     if event.key == pygame.K_RIGHT:
            #         current_piece.x += 1
            #         if not(valid_space(current_piece, grid)):
            #             current_piece.x -= 1
            #     if event.key == pygame.K_DOWN:
            #         current_piece.y += 1
            #         if not(valid_space(current_piece, grid)):
            #             current_piece.y -= 1
            #     if event.key == pygame.K_UP:
            #         current_piece.rotation += 1
            #         if not(valid_space(current_piece, grid)):
            #             current_piece.rotation -= 1

        shape_pos = convert_shape_format(current_piece)

        for i in range(len(shape_pos)):
            x, y = shape_pos[i]
            if y > -1:
                grid[y][x] = current_piece.color

        if change_piece:
            for pos in shape_pos:
                p = (pos[0], pos[1])
                locked_positions[p] = current_piece.color
            if len(added_pieces) == 6:
            # if next_addition == 0:  # check to see if list is empty
                added_pieces = ordered_index[:]  # refill list
                random.shuffle(added_pieces)  # shuffle list
                piece_array.extend(added_pieces)  # add new pieces
                next_addition = 6
            current_piece = get_shape(piece_array.pop(0))
            change_piece = False
            save_piece = False
            already_saved = False
            score += clear_rows(grid, locked_positions) * 10
            next_addition -= 1

        if save_piece and not already_saved:
            if not saved_piece:  # if it's the first time we save a piece
                current_piece.x = 4
                current_piece.y = 2
                saved_piece = current_piece
                current_piece = get_shape(piece_array.pop(0))
                next_addition -= 1
            else:
                current_piece.x = 4
                current_piece.y = 2
                aux = saved_piece
                saved_piece = current_piece
                current_piece = aux
            already_saved = True
            save_piece = False

        draw_window(win, grid, score, last_score)
        if saved_piece:
            swap_piece(saved_piece, win)
        draw_next_shape(piece_array, win)
        pygame.display.update()

        if check_lost(locked_positions):
            draw_text_middle(win, "YOU LOST!", 80, (255, 255, 255))
            pygame.display.update()
            pygame.time.delay(1500)
            run = False
            update_score(score)


def main_menu(win):  # *
    run = True
    while run:
        win.fill((0, 0, 0))
        draw_text_middle(win, 'Press Space To Play', 60, (255, 255, 255))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    main(win)

    pygame.display.quit()
    pygame.quit()
    exit()


win = pygame.display.set_mode((s_width, s_height))
pygame.display.set_caption('Tetris')
main_menu(win)
