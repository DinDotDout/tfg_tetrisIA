import cv2
import numpy as np
import math
from tetris_game.tetrisStructure import board, piece as tetrisPiece


S = [[0.56, 131.16, 52.36],[0.68, 162.72, 61.72]]
Z = [[35.32, 11.56, 145.32],[41.72, 13.96, 163.3]]
I = [[141.52, 118.08, 0.0], [163.2, 146.4, 0.0]]
O = [[0.0, 110.28, 138.28], [0.16, 139.0, 163.2]]
L = [[2.16, 56.32, 144.24], [2.04, 68.32, 163.2]]
J = [[152.56, 0.6, 26.56], [163.2, 1.96, 31.8]]
T = [[148.36, 0.0, 100.12], [163.2, 0.0, 125.76]]
GREY = [[73.96, 74.92, 76.04], [90.4, 91.6, 92.36]]
NoMatch = [[255.0,255.0,255.0]]
BLACK = [[10.0, 10.0, 10.0]]
# MAIN = [[165, 245, 27]]
shapes = [BLACK, S, Z, I, T, J, L, O, GREY, NoMatch]

shapes_str = ["e", "S", "Z", "I", "T", "J", "L", "O", "gr","No"]


EMPTY = 0

frame = None
gameBoard = None
allMatch = False
newBoard = False

# GAME DETECTION
# ------------------------------------------------
def game_processing():
    '''Draw game detection points and create matrices with game info'''
    _check_game_grid()
    _check_out_of_grid()
    _check_stored_piece()
    _check_next_pieces()
    _update_board_info()

def _pixelBGR2HSV(img, x, y):
    bgr_pixel = np.uint8([[img[y, x]]])
    hsv_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)
    return hsv_pixel

def _centerpoint_matrixBGR(x, y, tam):
    '''Returns de "tam" size matrix from a centerpoint'''
    global frame
    first = math.trunc(tam/2)
    x_start = x-first
    y_start = y-first
    x_end = x+first
    y_end = y+first
    b = frame[y_start:y_end, x_start:x_end, 0]
    g = frame[y_start:y_end, x_start:x_end, 1]
    r = frame[y_start:y_end, x_start:x_end, 2]
    return [b, g, r]

def _centerpoint_mean(x, y):
    '''Calculates mean in a matrix'''
    tam = 5 # size of sample, must be odd
    bgr = _centerpoint_matrixBGR(x, y, tam)

    mean_b = np.sum(bgr[0])/(tam*tam) # total elements = tam*tam
    mean_g = np.sum(bgr[1])/(tam*tam)
    mean_r = np.sum(bgr[2])/(tam*tam)
    return [mean_b, mean_g, mean_r]

def _max(l):
    '''Max element in matrix'''
    max = 0
    for i in l:
        for j in i:
            if j > max:
             max = j
    return max

def _min(l):
    '''Min element in matrix'''
    min = 256 # color limit + 1
    for i in l:
        for j in i:
            if j < min:
             min = j
    return min


def centerpoint_dist(x, y):
    '''Calculates distance from highest and lowest elements in a matrix'''
    tam = 5
    bgr = _centerpoint_matrixBGR(x, y, tam)

    dist_b = max(bgr[0]) - min(bgr[0])

    dist_g = max(bgr[1]) - min(bgr[1])
    
    dist_r = max(bgr[2])- min(bgr[2])

    return [dist_b, dist_g, dist_r]

def centerpoint_sd(x, y):
    '''Calculates standard deviation for each colour'''
    tam = 5
    bgr = _centerpoint_matrixBGR(x, y, tam)
    mean = _centerpoint_mean(x, y)

    # BLUE
    dif = 0
    for i in bgr[0]:
        for j in i:
            dif = dif + (j - mean[0])**2
    sd_b = math.sqrt(dif/tam**2)

    # GREEN
    dif = 0
    for i in bgr[1]:
        for j in i:
            dif = dif + (j - mean[1])**2
    sd_g = math.sqrt(dif/tam**2)

    # RED
    dif = 0
    for i in bgr[2]:
        for j in i:
            dif = dif + (j - mean[2])**2
    sd_r = math.sqrt(dif/tam**2)

    return [sd_b, sd_g, sd_r]



def piece_type(x, y):
    '''Finds match between cell mean and all possible piece colours within a lower and upper limit'''
    bgr_mean = _centerpoint_mean(x, y)
    # Check for matching mean colors
    shape = 0
    found = False
    th_mean = 9
    isMain = False
    for color in shapes:
        # Two darkness levels for some colors
        dark = 0
        for darkness in color:
            B = abs(bgr_mean[0] - darkness[0])
            G = abs(bgr_mean[1] - darkness[1])
            R = abs(bgr_mean[2] - darkness[2])
            if  B < th_mean and G < th_mean and R < th_mean:
                found = True
                break
            dark = dark + 1
        if found:
            break   
        shape = shape+1
    if dark == 1 and shape > 0 and shape < len(shapes)-2:
        isMain = True # main piece
    # if no match found
    if found == False:
        # if the mean colour is very dark, the element is still considered an empty block/avoid detecting fake grey blocks
        th_mean = 80
        if bgr_mean[0] < th_mean and bgr_mean[1] < th_mean and bgr_mean[2] < th_mean:
            shape = 0
        else:
            shape = len(shapes)-1

    return shape, isMain


def _check_block(pixel_x, pixel_y, real_block, info_block):
    '''Returns block colour found if a match is found, else it will not update the cell information.
    It also shows what was detected on screen'''
    global frame
    shape, isMain = piece_type(pixel_x, pixel_y)
    if shape != EMPTY: # BLock is not empty
        if shape != len(shapes)-1: # If there was a match, update info
            if isMain:
                real_block = 2
            else:
                real_block = 1
        info_block = shape
    else: # Empty block
        real_block = 0
        info_block = 0
    color = shapes[shape][0] # get correspondent dim color
    cv2.putText(frame, shapes_str[info_block], (pixel_x,pixel_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color) # Output info to screen
    return real_block, info_block

grid_y_size = 20
grid_x_size = 10
game_matrix = [[0 for col in range(grid_x_size)] for row in range(grid_y_size)]
info_matrix = [[0 for col in range(grid_x_size)] for row in range(grid_y_size)]
def _check_game_grid():
    '''Loops trhough each cell in the game grid and checks its content to store it'''
    global shapes
    global EMPTY
    pixel_x = 496
    pixel_y = 56
    box_spacing = 32
    pixel_x_aux = pixel_x
    for y in range(grid_y_size):
        for x in range(grid_x_size):
            game_matrix[y][x], info_matrix[y][x] = _check_block(pixel_x, pixel_y, game_matrix[y][x], info_matrix[y][x])
            pixel_x = pixel_x + box_spacing
        pixel_x = pixel_x_aux
        pixel_y = pixel_y + box_spacing

def _check_outside_block(pixel_x, pixel_y, real_block, info_block):
    '''Returns block colour found if a match is found, else it will not update the cell information.
    It also shows what was detected on screen'''
    global frame
    shape, isMain = piece_type(pixel_x, pixel_y)
    if isMain: # BLock is main
        real_block = 2
        info_block = shape
    else: # Empty block
        real_block = 0
        info_block = 0
    color = shapes[shape][0] # get correspondent dim color
    cv2.putText(frame, shapes_str[info_block], (pixel_x,pixel_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color) # Output info to screen
    return real_block, info_block   

game_out_matrix = [0 for col in range(grid_x_size)]
info_out_matrix = [0 for col in range(grid_x_size)]
def _check_out_of_grid():
    global shapes
    pixel_x = 496
    pixel_y = 24
    box_spacing = 32
    pixel_x_aux = pixel_x

    for x in range(grid_x_size):
        game_out_matrix[x], info_out_matrix[x] = _check_outside_block(pixel_x, pixel_y, game_out_matrix[x], info_out_matrix[x])
        pixel_x = pixel_x + box_spacing

def _check_piece(pixel_x, pixel_y, space, piece, piece_info):
    '''Given a position and how far appart blocks are it gets the shape of a piece'''
    # piece position
    pixel_x_aux = pixel_x

    # Game grid info
    for y in range(len(piece)):
        for x in range(len(piece[0])):
            piece[y][x], piece_info[y][x] = _check_block(pixel_x, pixel_y, piece[y][x], piece_info[y][x])
            pixel_x = pixel_x + space
        pixel_x = pixel_x_aux
        pixel_y = pixel_y + space

n_box_x = 4
n_box_y = 2
n_pieces = 6
next_pieces = [[[0 for col in range(n_box_x)] for row in range(n_box_y)] for col in range(n_pieces)]
next_pieces_info = [[[0 for col in range(n_box_x)] for row in range(n_box_y)] for col in range(n_pieces)]
def _check_next_pieces():
    '''Checks upcoming pieces and store their info'''
    # NEXT PICE
    # piece position
    pixel_x = 824
    pixel_y = 91

    # space between blocks
    pixel_space = 17

    _check_piece(pixel_x, pixel_y, pixel_space, next_pieces[0], next_pieces_info[0])

    # NEXT 5 PIECES
    # first piece position
    pixel_x = 823
    pixel_y = pixel_y_aux = 151

    # Space between pieces
    next_piece = 55
    
    # Space between piece boxes
    pixel_space = 15

    for i in range(1, n_pieces):
        _check_piece(pixel_x, pixel_y, pixel_space, next_pieces[i], next_pieces_info[i])
        pixel_y = pixel_y + next_piece

stored_piece = [[0 for col in range(n_box_x)] for row in range(n_box_y)]
stored_piece_info = [[0 for col in range(n_box_x)] for row in range(n_box_y)]
def _check_stored_piece():
    '''Check information related to the stored piece and store it'''
    # Saved PICE
    # piece position
    pixel_x = 406
    pixel_y = 92

    piece_space = 17
    _check_piece(pixel_x, pixel_y, piece_space, stored_piece, stored_piece_info)
    # print('\n'.join([''.join(['{:4}'.format(item) for item in row]) 
    # for row in stored_piece_info]))
    # print("________")

def _img_to_tetris_piece(startX, startY):
    '''Given a piece detection, it transforms it into our tetris simulation object'''
    piece = None
    totalGridYSize = grid_y_size-1 # 19
    xPos = 4
    yPos = totalGridYSize - startY # 20/19/18

    if yPos == 20:
        piece = tetrisPiece.get_piece_type(info_out_matrix[startX]-1)
    else:
        piece = tetrisPiece.get_piece_type(info_matrix[startY][startX]-1)

    if type(piece) != tetrisPiece.IPiece: # all pieces center block is down by one row
        yPos -= 1

    piecePos = np.array([xPos, yPos])

    return piece, piecePos

def _img_to_grid():
    '''Given the detected gamegrid, it converts it so that we can use it in our simulation'''
    # "I", "J", "L", "O", "S", "T", "Z"
    pieceColor = {
        "gr": [90.4, 91.6, 92.36],
        "I": tetrisPiece.IPiece.color,
        "J": tetrisPiece.JPiece.color,
        "L": tetrisPiece.IPiece.color,
        "O": tetrisPiece.LPiece.color,
        "S": tetrisPiece.SPiece.color,
        "T": tetrisPiece.TPiece.color,
        "Z": tetrisPiece.ZPiece.color,
    }
    topRows = [[None for col in range(grid_x_size)] for row in range(4)]
    gameGrid = [[None for col in range(grid_x_size)] for row in range(grid_y_size)]
    allMatch = True
    for i in range(len(info_matrix)):
        for j in range(len(info_matrix[0])):
            if game_matrix[i][j] != 2 and info_matrix[i][j] != 0 and info_matrix[i][j] != 9:
                gameGrid[i][j] = pieceColor[shapes_str[info_matrix[i][j]]]
            if shapes_str[info_matrix[i][j]] == "No": #No info
                allMatch = False


    # if NoMatch:
    #     print('\n'.join([''.join(['{:4}'.format(item) for item in row]) 
    #         for row in info_matrix]))
    #     print("____________________")
    gameGrid = np.concatenate((topRows, gameGrid))
    
    # print('\n'.join([''.join(['{:4}'.format(item) for item in row]) 
    #     for row in gameGrid.tolist()]))

    return gameGrid[::-1].tolist(), allMatch

def _img_to_stored():
    '''Given a stored piece detection, it transforms it into our tetris simulation object'''
    startY = 0
    startX = 0
    canStore = True # if empty can store
    found = False
    for i in range(n_box_y):
        for j in range(n_box_x):
            if stored_piece[i][j] == 1 or stored_piece[i][j] == 2:
                startY = i
                startX = j
                found = True
                break
        if found:
            break

    pieceType = None
    if found: # Found a piece
        if stored_piece_info[startY][startX] < len(shapes)-2: # there is a stored piece, not grey ergo can store
            # Can check by colour, which is more reliable
            pieceType = tetrisPiece.get_piece_type(stored_piece_info[startY][startX]-1)
        else:
            pieceType = check_piece_by_shape()
            canStore = False
    else:
        canStore = False
    return pieceType, canStore

def check_piece_by_shape():
    '''Given the detected blocks guesses what piece it is'''
    pieceType = None
    # yx
    if stored_piece[0][0] == 1 or stored_piece[0][0]  == 2: # 1
        if stored_piece[0][1] == 1 or stored_piece[0][1]  == 2: # 11
            if stored_piece[0][2] == 1 or stored_piece[0][2]  == 2: # 111
                pieceType = tetrisPiece.IPiece() #"I"
            else: # 1100
                pieceType = tetrisPiece.ZPiece() # "Z"
        else: # 10
            pieceType = tetrisPiece.JPiece() # "J"
    else: # 0
        if stored_piece[0][1] == 1 or stored_piece[0][1]  == 2: # 01
            if stored_piece[0][2] == 1 or stored_piece[0][2]  == 2: # 011
                if stored_piece[1][0] == 1 or stored_piece[1][0]  == 2: # 011/1
                    pieceType = tetrisPiece.SPiece() # "S"
                else:# 011/0
                    pieceType = tetrisPiece.OPiece() # "O"
            else: # 010
                pieceType = tetrisPiece.TPiece() # "T"
        else: # 00
            pieceType = tetrisPiece.LPiece() # "L"
    return pieceType
    

def _img_to_upcoming_pieces():
    '''Given the upcoming pieces detected, it transforms them into our tetris simulation bag'''

    bag = [7] * 6 # default piece value is 7 as none
    for k in range(n_pieces):
        found = False
        for i in range(n_box_y):
            for j in range(n_box_x):
                pieceType = next_pieces_info[k][i][j]
                if (next_pieces[k][i][j] == 1 or next_pieces[k][i][j] == 2) and pieceType < len(shapes)-2:
                    bag[k] = pieceType-1
                    found = True
                    break
            if found:
                break
    return bag


def _update_board_info():
    "Checks the info detected and creates a board object with it"
    global gameBoard, newBoard, allMatch
    
    pieceDetected = False
    startX = 0
    startY = -1
    
    for i in range(grid_x_size):
        if game_out_matrix[i] == 2 and info_out_matrix[i] < len(shapes) - 2:
            pieceDetected = True
            startX = i
            break
    if not pieceDetected:
        for i in range(4):
            for j in range(grid_x_size):
                if game_matrix[i][j] == 2 and info_matrix[i][j] < len(shapes) - 2:
                    pieceDetected = True
                    startY = i
                    startX = j
                    break
            if pieceDetected: # break second
                break

    if pieceDetected:
        # if canMove:
            piece, piecePos = _img_to_tetris_piece(startX, startY)
            gameGrid, allMatch = _img_to_grid()
            storedPiece, canStore = _img_to_stored()
            bag = _img_to_upcoming_pieces()
            gameBoard = board.Board(grid = gameGrid, bag = bag, piecePos = piecePos,
                        mainPiece = piece, storedPiece = storedPiece, canStore = canStore)
    
# # SELECTION SCREEN DETECTION
# # ______________________________________________________________________________
# def selection_screen_detection():
#     # color range to detect the mode we want
#     global frame
#     max_blue_hue = 190/2
#     min_blue_hue = 170/2
#     max_saturation = max_value = 255
#     max_blue_hsv = (max_blue_hue, max_saturation, max_value)
#     min_blue_hsv = (min_blue_hue, max_saturation*0.6, max_value*0.7)

#     # pixel we will check to see if we have the correct game mode
#     first_box_x = 300
#     first_box_y = 600
    
#     pixel_color = _pixelBGR2HSV(frame, first_box_x, first_box_y)
#     # Draw detection point
#     cv2.circle(frame,(first_box_x,first_box_y), 5, (0,0,255), -1)
#     if not cv2.inRange(pixel_color, min_blue_hsv, max_blue_hsv):
#         return False
#     else:
#         return True