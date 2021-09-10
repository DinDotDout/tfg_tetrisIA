import sys
import argparse
import serial
import numpy as np
import math
import time
import copy

import cv2

from . import fileVideoStream as fvs
from . import switchController as ctrler
from . import image_processing as img_process
from neural_net import heuristic_calc as hc, run as net
from tetris_game.tetrisStructure import board
from tetris_game.tetrisStructure import piece

np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning) 

# BUTTONS
# Arrow keys
up_pad = 38
down_pad = 40
left_pad = 37
right_pad = 39

a_button = ord("d") # rotate right
b_button = ord("a") # rotate left
l_button = ord(" ") # swap piece
pause_button = ord("p")

# Flow control
exit = 27 # Esc
activate_net = 13 # Intro

# up_pad = ord("i")
# down_pad = ord("l")
# left_pad = ord("j")
# right_pad = ord("k")


wait_time = 0 # Time to waste
timeMark = 0 # Time mark to start counting

auto_state = 1
def controller(k):
    '''Sends according command to the controller for the switch to receive'''
    if k == left_pad:
        ctrler.send_cmd(ctrler.DPAD_L)
    elif k == up_pad:
        ctrler.send_cmd(ctrler.DPAD_U)
    elif k == down_pad:
        ctrler.send_cmd(ctrler.DPAD_D)
    elif k == right_pad:
        ctrler.send_cmd(ctrler.DPAD_R)
    elif k == a_button:
        ctrler.send_cmd(ctrler.BTN_A)
    elif k == b_button:
        ctrler.send_cmd(ctrler.BTN_B)
    elif k == l_button:
        ctrler.send_cmd(ctrler.BTN_L)
    elif k == pause_button:
        ctrler.send_cmd(ctrler.BTN_PLUS)

def controller2(k):
    '''Sends according command to the controller for the switch to receive'''
    if k == left_pad:
        ctrler.send_cmd(ctrler.DPAD_L+ctrler.BTN_B)
    elif k == up_pad:
        ctrler.send_cmd(ctrler.DPAD_U)
    elif k == down_pad:
        ctrler.send_cmd(ctrler.DPAD_D)
    elif k == right_pad:
        ctrler.send_cmd(ctrler.DPAD_R+ctrler.BTN_B)
    elif k == a_button:
        ctrler.send_cmd(ctrler.BTN_A)
    elif k == b_button:
        ctrler.send_cmd(ctrler.BTN_B)
    elif k == l_button:
        ctrler.send_cmd(ctrler.BTN_L)
    elif k == pause_button:
        ctrler.send_cmd(ctrler.BTN_PLUS)


def start_time_counter():
    '''Stpres a time mark as reference for a time counter'''
    global timeMark
    timeMark = time.perf_counter()

def check_wait_timer(waitTime):
    '''Returns if the selected time has passe since the counter was started'''
    global timeMark
    currTime = time.perf_counter()

    if currTime - timeMark < waitTime:
        return False
    else:
        return True

def start_frame_waste(wait_reset):
    '''Resets the frame waste counter'''
    global wait_time
    wait_time = wait_reset
    
def waste_frames():
    '''Returns amount of frames left to wait'''
    global wait_time
    if wait_time > 0:
        wait_time = wait_time - 1
    return wait_time

def screen_selector():
    correct_screen = img_process.selection_screen_detection()
    if correct_screen:
        controller(a_button)
        global auto_state
        auto_state = auto_state + 1
        start_frame_waste(20)
    else:
        controller(right_pad)
        controller(up_pad)
        start_frame_waste(20)


# Auto mode selector
def state_controller(k):
    global auto_state
    switcher = {
        # 1: screen_selector,
        # 2: screen_selector,
        1: img_process.game_processing,
        2: img_process.game_processing,
        3: img_process.game_processing,
    }
    func = switcher.get(auto_state, "Invalid state")
    # print('\n'.join([''.join(['{:4}'.format(item) for item in row]) 
    #     for row in img_process.game_matrix]))
    # print("")
    func()
    img_process.game_processing()

moves = []
bag = []
storedPiece = None
clean = False
expectedPos = None
piece = None
lines = 0
env = None
lastenv = None
trigger = False
def run_net(frame):
    '''Asks neural net for output whenever it is deemed necessary'''
    global moves, clean, expectedPos, piece, bag, storedPiece, env, lastenv, trigger

    # next_piece_timer = 0.03 # wait for board effects to disappear
    # next_piece_timer_clear = 0.6 # wait for board effects to disappear
    # If board is different from last ask for new moves
    # if lines > 0:
    #     timer = next_piece_timer_clear
    # else:
    #     timer = next_piece_timer
    if img_process.gameBoard and (not np.array_equal(img_process.gameBoard.bag[:3], bag) or 
        type(storedPiece) != type(img_process.gameBoard.storedPiece)) and not moves:
        ask_net()


    # If there is and expected piece to be placed, draw it
    if piece:
        draw_expected_pos(expectedPos, piece, frame)

    next_move_timer = 0.03
    # if moves:
    #     if moves[-1] == left_pad or moves[0] == right_pad:
    #         next_move_timer = 0.015
    #     elif moves[-1] == b_button:
    #         next_move_timer = 0.025
    #     elif moves[-1] == up_pad:
    #         next_move_timer = 0.015

    # if not clean:
    #     next_move_timer = 0.02
    # Checks to see if time has passeds
    if check_wait_timer(next_move_timer):
        if clean: # clean last input if enough time has passed
            ctrler.send_cmd()
            clean = False
            start_time_counter()
            if not moves: # last move just executed
                # img_process.canMove = True # Allow new board to be created and clean up drawn piece
                piece = None
        elif moves: # send new move
            move = moves.pop()
            if move == up_pad:
                
                curr_board = img_process.check_board()
                if not _equal_grids(curr_board.grid, lastenv.grid):
                    trigger = True
                if lines <= 110:
                    controller(move)
            else:        
                controller(move)
            start_time_counter()
            clean = True


    # if not moves and check_wait_timer(0.8): # last move just executed
    #     img_process.canMove = True # Allow new board to be created and clean up drawn piece
    #     piece = None
            

def _equal_grids(grid1, grid2):
    for x, y in zip(grid1[:20], grid2[:20]):
        for x1, y1 in zip(x, y):
            if x1 and not y1 or not x1 and y1:
                return False
    return True

def ask_net():
    '''Asks the neural net for moves and stores them'''
    global moves, bag, storedPiece, piece, expectedPos, lines, env, lastenv, trigger
    if not env:
        env = copy.deepcopy(img_process.gameBoard)
    else:
        env.bag = copy.deepcopy(img_process.gameBoard.bag)
        env.storedPiece = copy.deepcopy(img_process.gameBoard.storedPiece)
    if trigger:
        env = copy.deepcopy(img_process.gameBoard)
    lastenv = copy.deepcopy(env) # store env before movement

    # If can draw and last moves where cleared
    bag = img_process.gameBoard.bag[:3] # we will use it to avoid executing same sequence more than once
    storedPiece = img_process.gameBoard.storedPiece
    # bag = env.bag[:3] # we will use it to avoid executing same sequence more than once
    # storedPiece = env.storedPiece
    # displacement, rotation, expectedPos, piece, lines, env = net.get_net_output(env)
    displacement, rotation, expectedPos, piece, points, env = net.get_net_output(img_process.gameBoard)
    moves = queue_moves(displacement, rotation)
    drop = True
    trigger = False
    lines += points

    


def draw_expected_pos(expectedPos, piece, frame):
    '''Draws a piece that we want directly on the game grid'''
    pixel_x = 496
    pixel_y = 56
    box_spacing = 32
    for tile in  piece.tiles:
        x, y = expectedPos + tile.position
        cv2.putText(frame, "POS", (pixel_x+(x*box_spacing), pixel_y+((19-y)*box_spacing)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (piece.color[2], piece.color[1], piece.color[0]))


def queue_moves(displacement, rotation):
    "Return a queue with the movements to perform"
    moves = []

    # Piece swap
    if displacement == 6:
        moves.append(l_button)
        # print("swap")
        return moves

    # Drop piece
    moves.append(up_pad)
    
    # Place in correct column
    if displacement > 0:
        for i in range(displacement):
            moves.append(right_pad)
    elif displacement < 0:
        for i in range(abs(displacement)):
            moves.append(left_pad)
    
    # Rotate piece
    for i in range(rotation):
        moves.append(b_button)

    return moves

# Main
# -----------------------------------------------
def main():
    global moves, bag, clean, expectedPos, piece, lines

    # We get the 2 arguments and process them for its use
    parser = argparse.ArgumentParser('Tetris gaming')
    parser.add_argument('port')
    parser.add_argument(type=int, default= 1,
                        help="Image device selector", dest = 'cap')
    args = parser.parse_args()
    
    print('Opening serial port')
    # Only first baudrate seems to be able to sync
    if not ctrler.serialPort:
        ctrler.serialPort = serial.Serial(port=args.port, baudrate=19200, timeout=1)
    # ser = serial.Serial(port=args.port, baudrate=31250,timeout=1)
    # ser = serial.Serial(port=args.port, baudrate=40000,timeout=1)
    # ser = serial.Serial(port=args.port, baudrate=62500,timeout=1)

    # Attempt to sync with the MCU
    print('Synchronizing pc with Nintendo Switch')
    if not ctrler.sync():
        print('Could not sync!')

    print('Sending test packet')
    if not ctrler.send_cmd():
        print('Packet Error!')
        sys.exit()
    print('Packet succesful')
    print('Synchronized')

    # Frame buffer
    width = 1266
    height = 720
    print('Preparing frame buffer...')
    cap = fvs.FileVideoStream(args.cap, width = width, height = height).start()
    print('Frame buffer ready')

    print("Loading neural net data")
    found = net.load_model()
    if not found:
        return

    # Name of the window we will use
    winname = 'Nintendo Switch'
    cv2.namedWindow(winname)

    # Set screen to full size
    cv2.setWindowProperty(winname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    auto_pilot = False
    lastCommand = -1
    frame = None
    while(cv2.getWindowProperty(winname, cv2.WND_PROP_VISIBLE) >= 1):
        # k = cv2.waitKey(1)
        k = cv2.waitKeyEx(1) # Special keys active

        if k == exit: # Esc key
            break
        elif k == activate_net: # clean up autoplay info
            img_process.gameBoard = None 
            moves = []
            bag = []
            env = None
            lines = 0
            nextPiece = None
            storedPiece = None
            clean = False

            expectedPos = None
            piece = None
            auto_pilot = not auto_pilot

        if cap.has_frame():
            frame = cap.read()
            if auto_pilot: # Only process frame when there is a new one
                img_process.frame = frame # Send frame info to game processing
                img_process.game_processing() # Image detection on frame
        
        
        if auto_pilot: # Automatic mode
            run_net(frame)
        else: # Player controller mode
            # read keyboard input
            if k != -1: # If command received
                # command = chr(k)
                controller(k) # send command to switch
                start_time_counter()
                lastCommand = k
            else:
                if check_wait_timer(0.06) and lastCommand != -1: # Send command cleanup to switch after a some time
                    ctrler.send_cmd()
                    lastCommand = -1
        # show the frame 
        cv2.imshow(winname, frame)
        

    # When everything done, release the capture and controller
    cap.stop()
    cv2.destroyAllWindows()
    ctrler.close

