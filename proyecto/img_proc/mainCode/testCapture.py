import cv2
import argparse
import FileVideoStream as fvs
import numpy as np
import math
# msg = ctypes.windll.user32.MessageBoxW.mes(1, "Your text", "Your title", 0)
# Arg parse
# -----------------------------------------------
parser = argparse.ArgumentParser('Tetris gaming')
parser.add_argument(type=int, default= 1,
                    help="Image device selector", dest = 'cap')
args = parser.parse_args()

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

shapes = [BLACK, S, Z, I, O, L, J, T, GREY,NoMatch]
shapes_str = ["e", "S", "Z", "I", "O", "L", "J", "T", "gr", "No"]
EMPTY = 0
# SCREEN DETECTION
# ------------------------------------------------

def pixelBGR2HSV(img, x, y):
    bgr_pixel = np.uint8([[img[y, x]]])
    # hsv_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)[0,0]
    hsv_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)
    return hsv_pixel

# Returns de "tam" size matrix from a centerpoint
def centerpoint_matrixBGR(x, y, tam):
    first = math.trunc(tam/2)
    x_start = x-first
    y_start = y-first
    x_end = x+first
    y_end = y+first
    b = frame[y_start:y_end, x_start:x_end, 0]
    g = frame[y_start:y_end, x_start:x_end, 1]
    r = frame[y_start:y_end, x_start:x_end, 2]
    return [b, g, r]

# Calculates mean in a matrix
def centerpoint_mean(x, y):
    tam = 5 # size of sample, must be odd
    bgr = centerpoint_matrixBGR(x, y, tam)

    mean_b = np.sum(bgr[0])/(tam*tam) # total elements = tam*tam
    mean_g = np.sum(bgr[1])/(tam*tam)
    mean_r = np.sum(bgr[2])/(tam*tam)
    return [mean_b, mean_g, mean_r]

# Max element in matrix
def max(l):
    max = 0
    for i in l:
        for j in i:
            if j > max:
             max = j
    # print(max)
    return max

# Min element in matrix
def min(l):
    min = 256 # color limit + 1
    for i in l:
        for j in i:
            if j < min:
             min = j
    # print(min)

    return min

# Calculates distance from highest and lowest elements in a matrix
def centerpoint_dist(x, y):
    tam = 5
    bgr = centerpoint_matrixBGR(x, y, tam)

    dist_b = max(bgr[0]) - min(bgr[0])

    dist_g = max(bgr[1]) - min(bgr[1])
    
    dist_r = max(bgr[2])- min(bgr[2])

    return [dist_b, dist_g, dist_r]

# Calculates standard deviation for each colour
def centerpoint_sd(x, y):
    tam = 5
    bgr = centerpoint_matrixBGR(x, y, tam)
    mean = centerpoint_mean(x, y)

    # print(bgr)
    # BLUE
    dif = 0
    for i in bgr[0]:
        for j in i:
            dif = dif + (j - mean[0])**2
    # print(dif)
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

# Matches a piece with color using a lower and upper limit
def piece_type(x, y):
    bgr_mean = centerpoint_mean(x, y)
    # Check for matching mean colors
    shape = 0
    found = False
    th_mean = 6
    dark = 0
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

    # if no match found
    if found == False:
        # if the mean colour is very dark, the element is still considered an empty block
        th_mean = 80
        if bgr_mean[0] < th_mean and bgr_mean[1] < th_mean and bgr_mean[2] < th_mean:
            shape = 0
        else:
            shape = len(shapes)-1
    return shape, dark

# Saves in the cell which piece colour was found and only updates if the color matches an existing piece
def check_block(pixel_x, pixel_y, real_block, info_block, is_game_grid):
    shape, dark = piece_type(pixel_x, pixel_y)
    if shape != EMPTY: # BLock is not empty
        if shape != len(shapes)-1: # If there was a match, update info
            real_block = 1
            info_block = shape
    else: # Empty block
        real_block = 0
        info_block = 0
    color = shapes[shape][0] # get correspondent dim color
    cv2.putText(frame, shapes_str[info_block], (pixel_x,pixel_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color) # Output info yo screen

    # if not(is_game_grid and dark == 1):
        # cv2.putText(frame, shapes_str[info_block], (pixel_x,pixel_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color) # Output info yo screen
    return real_block, info_block

grid_y_size = 20
grid_x_size = 10
game_matrix = [[0 for col in range(grid_x_size)] for row in range(grid_y_size)]
info_matrix = [[0 for col in range(grid_x_size)] for row in range(grid_y_size)]
def check_game_grid():
    global shapes
    global EMPTY
    pixel_x = 496
    pixel_y = 56
    box_spacing = 32
    pixel_x_aux = pixel_x
    for y in range(grid_y_size):
        for x in range(grid_x_size):
            game_matrix[y][x], info_matrix[y][x] = check_block(pixel_x, pixel_y, game_matrix[y][x], info_matrix[y][x], True)
            pixel_x = pixel_x + box_spacing
        pixel_x = pixel_x_aux
        pixel_y = pixel_y + box_spacing

    # print('\n'.join([''.join(['{:4}'.format(item) for item in row]) 
    #     for row in game_matrix]))  

# Checks a position and gets the shape of a piece
def check_piece(pixel_x, pixel_y, space, piece, piece_info):
    # piece position
    pixel_x_aux = pixel_x

    # Game grid info
    for y in range(len(piece)):
        for x in range(len(piece[0])):
            printe = False
            piece[y][x], piece_info[y][x] = check_block(pixel_x, pixel_y, piece[y][x], piece_info[y][x], False)
            pixel_x = pixel_x + space
        pixel_x = pixel_x_aux
        pixel_y = pixel_y + space

n_box_x = 4
n_box_y = 2
n_pieces = 6
next_pieces = [[[0 for col in range(n_box_x)] for row in range(n_box_y)] for col in range(n_pieces)]
next_pieces_info = [[[0 for col in range(n_box_x)] for row in range(n_box_y)] for col in range(n_pieces)]
# Checks upcoming pieces, first one is bigger than the others
def check_next_pieces():
    # NEXT PICE
    # piece position
    pixel_x = 824
    pixel_y = 91

    # space between blocks
    pixel_space = 17

    check_piece(pixel_x, pixel_y, pixel_space, next_pieces[0], next_pieces_info[0])

    # NEXT 5 PIECES
    # first piece position
    pixel_x = 823
    pixel_y = pixel_y_aux = 151

    # Space between pieces
    next_piece = 55
    
    # Space between piece boxes
    pixel_space = 15

    for i in range(1, n_pieces):
        check_piece(pixel_x, pixel_y, pixel_space, next_pieces[i], next_pieces_info[i])
        pixel_y = pixel_y + next_piece

stored_piece = [[0 for col in range(n_box_x)] for row in range(n_box_y)]
stored_piece_info = [[0 for col in range(n_box_x)] for row in range(n_box_y)]
# Check information related to the stored piece
def check_stored_piece():
    # Saved PICE
    # piece position
    pixel_x = 406
    pixel_y = 92

    piece_space = 17
    check_piece(pixel_x, pixel_y, piece_space, stored_piece, stored_piece_info)  

def mouse_callback(event, x, y, flags, params):
    if event == 1:
        print(centerpoint_mean(x, y))
        # for x in range(5):
        #      for y in range(5):
        #         frame[mat[]]
        #         cv2.circle(frame,(y,x), 0, (0,0,255), -1)

        # hsv_pixel = pixelBGR2HSV(frame, x, y)
        # print(hsv_pixel)

# OPENCV
# -----------------------------------------------
frame = None
# Frame buffer
def main():
    global frame
    width = 1266
    height = 720
    print('Preparing frame buffer...')

    cap = cv2.VideoCapture(args.cap, cv2.CAP_DSHOW)
    # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # cap = fvs.FileVideoStream(args.cap, width = width, height = height).start()
    print('Frame buffer ready')
    cv2.namedWindow('Nintendo Switch')

    cv2.setWindowProperty('Nintendo Switch', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    # read keyboard input
    while cv2.getWindowProperty('Nintendo Switch', cv2.WND_PROP_VISIBLE) >= 1:
        _, frame = cap.read()
        check_game_grid()
        check_next_pieces()
        check_stored_piece()
        cv2.imshow('Nintendo Switch', frame)
        keyCode = cv2.waitKey(1)
        if (keyCode & 0xFF) == ord("q"):
            break
                
    # cv2.setMouseCallback('Nintendo Switch1',None)
    # When everything done, release the capture and controller
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

