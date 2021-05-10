import random
import numpy as np
from time import sleep
import copy

from tetris_game.tetrisStructure.piece import OPiece, SPiece, ZPiece, IPiece


def _number_of_holes(board):
    "Number of holes in the board within game range (empty square with at least one block above it)"
    holes = 0
    for x in range(board.gridSizeX):
        n = 0
        for y in range(board.killHeight):
            if not board.grid[y][x]:
                n += 1
            if board.grid[y+1][x]:
                holes += n
                n = 0
    return holes



def _bumpiness(board):
    "Sum of the differences of heights between pair of columns"
    totalBumpiness = 0
    maxBumpiness = 0
    lastHeight = 0

    for x in range(board.gridSizeX):
        height = 0
        bumpiness = 0
        for y in range(board.killHeight, -1, -1):
            if board.grid[y][x]:
                height = y+1 # 0 height will be counted as 1
                break
        if x > 0 and x < board.gridSizeX: # We won't calculate 0 and the first column height
            bumpiness = abs(height-lastHeight)
            totalBumpiness += bumpiness
        lastHeight = height
        maxBumpiness = max(maxBumpiness, bumpiness)
    return totalBumpiness, maxBumpiness

def _height(board):
    '''Sum and maximum height of the board'''
    sum_height = 0
    max_height = 0
    min_height = board.killHeight

    for x in range(board.gridSizeX):
        height = 0
        for y in range(board.killHeight, -1, -1):
            if board.grid[y][x]:
                height = y+1 # 0 row will be counted as height 1
                break
        sum_height += height

        if height > max_height:
            max_height = height
        elif height < min_height:
            min_height = height
    return sum_height, max_height, min_height

def get_board_props(board, initialScore = 0):
    '''Get properties of the board'''
    # lines, board = self._clear_lines(board)
    newScore = board.score - initialScore
    holes = _number_of_holes(board)
    total_bumpiness, max_bumpiness = _bumpiness(board)
    sum_height, max_height, min_height = _height(board)
    return [newScore, holes, total_bumpiness, sum_height]

def get_next_states(board):
    '''Get all possible next states'''
    states = {}
    # boardList = []
    mainPiece = board.mainPiece
    
    displacements = list(range(-5, 6))
    movement = np.array([1,0])

    rotations = 4
    pieceType = type(mainPiece)
    if pieceType is OPiece: # O piece is in the same position even if we roate
        rotations = 1
    elif pieceType is SPiece or pieceType is ZPiece or pieceType is IPiece: # Rotations 3 and 4 are similar to 1 and 2
        rotations = 2
    
    initialBoard = copy.deepcopy(board) # Save initial board state

    initialScore = initialBoard.score
    gamePiece = copy.deepcopy(mainPiece) # We will use this piece to preserve rotation

    if board.canStore:
        board.swap_piece()
        props = get_board_props(board, initialScore)
        states[(6, 0)] = props
        grid = [x[:] for x in initialBoard.grid] # reset board game
        bag = [x for x in initialBoard.bag] # reset board bag
        board.reset(grid = grid, bag = bag, piecePos = copy.deepcopy(initialBoard.piecePos),
            mainPiece = copy.deepcopy(gamePiece), storedPiece = initialBoard.storedPiece, canStore = initialBoard.canStore)

    # For all rotations
    for rotation in range(rotations):
        # For all positions
        
        for displacement in displacements:
            # for i in range(rotation):
            #     board.rotate_piece(True, True)
            isValid = board.move_piece(displacement*movement) 
            if isValid:
                # Drop piece to bottom
                board.drop_piece()

                # Calculate heuristic and add it to dictionary as a valid route
                props = get_board_props(board, initialScore)
                states[(displacement, rotation)] = props

            # board = copy.deepcopy(initialBoard)
            grid = [x[:] for x in initialBoard.grid] # reset board game
            bag = [x for x in initialBoard.bag] # reset board bag
            board.reset(grid = grid, bag = bag, piecePos = copy.deepcopy(initialBoard.piecePos),
                mainPiece = copy.deepcopy(gamePiece), storedPiece = initialBoard.storedPiece, canStore = initialBoard.canStore)
                # board = copy.deepcopy(initialBoard) # reset board game
        
            # for i in range(rotation):
        board.rotate_piece(True, True)
        gamePiece = copy.deepcopy(board.mainPiece) # make a copy to preserve rotation
    # print()
            # board = copy.deepcopy(initialBoard) # Reset board state given that board.move_piece alters it
    # props = get_board_props(board, initialScore)
    # states[(2, 2)] = props
    # for x in range(1000):
    #     gamePiece = copy.deepcopy(mainPiece) # We will use this piece to preserve rotation
    # print(states)
    return states, initialBoard
    
    # return states, initialBoard

def play(board, displacement, rotation):
    '''Makes a play given a position and a rotation, returning the reward and if the game is over'''
    initialScore = board.score
    if displacement == 6:
        board.swap_piece()
    else:
        displacement = displacement*np.array([1, 0])
        # print(displacement)
        for i in range(rotation):
            # print(i)
            board.rotate_piece(True, True)
        # Move piece to column
        board.move_piece(displacement)
        
        # Drop piece
        board.drop_piece()

    score = 1 + ((board.score - initialScore)**2)
    if board.gameOver:
        score -= 2
    # print(score)
    return score, board.gameOver


def get_state_size():
    '''Size of the state'''
    return 4
    
    # '''Renders the current board'''
    # img = [Tetris.COLORS[p] for row in self._get_complete_board() for p in row]
    # img = np.array(img).reshape(Tetris.BOARD_HEIGHT, Tetris.BOARD_WIDTH, 3).astype(np.uint8)
    # img = img[..., ::-1] # Convert RRG to BGR (used by cv2)
    # img = Image.fromarray(img, 'RGB')
    # img = img.resize((Tetris.BOARD_WIDTH * 25, Tetris.BOARD_HEIGHT * 25))
    # img = np.array(img)
    # cv2.putText(img, str(self.score), (22, 22), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1)
    # cv2.imshow('image', np.array(img))
    # cv2.waitKey(1)