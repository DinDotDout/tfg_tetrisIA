import pygame
import random
import sys
import numpy as np

import board as b

pygame.font.init()


# GLOBALS VARS
s_width = 750
s_height = 650
play_width = 300  # meaning 300 // 10 = 30 width per block
play_height = 600  # meaning 600 // 20 = 30 height per block
block_size = 30

top_left_x = (s_width - play_width) // 2
top_left_y = s_height - play_height

UP = np.array([0,1])
DOWN = np.array([0,-1])
LEFT = np.array([-1,0])
RIGHT = np.array([1,0])


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
    pygame.display.update()

def draw_next_shape(surface, bag):
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

def main(win):  # *
    last_score = max_score()
    board = b.Board()
    board.create_grid()

    change_piece = False
    save_piece = False
    already_saved = False
    run = True

    saved_piece = None

    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 1
    level_time = 0
    score = 0

    while run:
        fall_time += clock.get_rawtime()
        level_time += clock.get_rawtime()
        clock.tick()

        if level_time/1000 > 5:
            level_time = 0
            if level_time > 0.12:
                level_time -= 0.005

        if fall_time/1000 > fall_speed:
            fall_time = 0
            board.move_piece(DOWN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                # pygame.display.quit()
                # pygame.quit()
                # exit()
            input_controller(event, board)
           

        # if save_piece and not already_saved:
        #     if not saved_piece:  # if it's the first time we save a piece
        #         current_piece.x = 4
        #         current_piece.y = 2
        #         saved_piece = current_piece
        #         current_piece = get_shape(piece_array.pop(0))
        #         next_addition -= 1
        #     else:
        #         current_piece.x = 4
        #         current_piece.y = 2
        #         aux = saved_piece
        #         saved_piece = current_piece
        #         current_piece = aux
        #     already_saved = True
        #     save_piece = False

        draw_window(win, board.grid_colors(), score, last_score)
        draw_next_shape(win, board.bag)
        # if saved_piece:
        #     swap_piece(saved_piece, win)
        # draw_next_shape(piece_array, win)
        # pygame.display.update()

        # if check_lost(locked_positions):
        #     draw_text_middle(win, "YOU LOST!", 80, (255, 255, 255))
        #     pygame.display.update()
        #     pygame.time.delay(1500)
        #     run = False
        #     update_score(score)

def input_controller(event, board):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_LEFT:  # Move left
            board.move_piece(LEFT)
        if event.key == pygame.K_RIGHT:  # Move right
            board.move_piece(RIGHT)
        if event.key == pygame.K_DOWN:  # Move down
            board.move_piece(DOWN)
        if event.key == pygame.K_UP:  # Drop piece
            board.drop_piece()

        if event.key == pygame.K_d:  # Rotate right
            board.rotate_piece(True, True)
        if event.key == pygame.K_a:  # Rotate left
            board.rotate_piece(False, True)
        # if event.key == pygame.K_SPACE:  # Save piece
        #     save_piece = True

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