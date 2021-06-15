import random
import numpy as np
from time import sleep
import copy

import tetris_game.tetrisStructure.piece as piece
    
def get_next_states(board):
    '''Get all possible next states'''
    states = {}

    displacementsL = list(reversed(range(-5, 0)))
    displacementsR = list(range(0, 6))

    rotations = 4
    if type(board.mainPiece) is piece.OPiece: # O piece is in the same position even if we rotate
        rotations = 1
    elif type(board.mainPiece) is piece.SPiece or type(board.mainPiece) is piece.ZPiece:
        rotations = 2

    initialBoard = copy.deepcopy(board) # Save initial board state
    gamePiece = copy.deepcopy(board.mainPiece) # We will use this piece to preserve rotation

    if board.canStore:  # Add store move to dictionary
        board.swap_piece()
        landingHeight = board.piecePos[1]
        props = get_board_props(board)
        states[(6, 0)] = props

        grid = [x[:] for x in initialBoard.grid] # reset board game
        bag = [x for x in initialBoard.bag] # reset board bag
        
        board.reset(grid = grid, bag = bag, piecePos = copy.deepcopy(initialBoard.piecePos),
            mainPiece = copy.deepcopy(gamePiece), storedPiece = copy.deepcopy(initialBoard.storedPiece),
            canStore = initialBoard.canStore, score= initialBoard.score)

    for rotation in range(rotations): # For all rotations

        testMovements(displacementsL, rotation, board, initialBoard, gamePiece, states) # test left movents
        
        testMovements(displacementsR, rotation, board, initialBoard, gamePiece, states) # test right movents

        board.rotate_piece(True, True) # rotates piece for next iteration
        gamePiece = copy.deepcopy(board.mainPiece) # replace gamePiece with new rotation

    # for rotation in range(rotations): # For all rotations

    #     board.rotate_piece(False, True) # rotates piece for next iteration

    #     testMovements(displacementsL, -rotation, board, initialBoard, gamePiece, states) # test left movents
        
    #     testMovements(displacementsR, -rotation, board, initialBoard, gamePiece, states) # test right movents

    #     gamePiece = copy.deepcopy(board.mainPiece) # replace gamePiece with new rotation

    return states, initialBoard

def testMovements(displacements, rotation, board, initialBoard, gamePiece, states):
    for displacement in displacements: # try all displacement
        isValid = True # No movement is also valid
        if displacement > 0: # move right
            isValid, _ = board.move_piece(np.array([1,0]))
        elif displacement < 0: # move left
            isValid, _ = board.move_piece(np.array([-1,0]))

        # store current position
        piecePos = copy.deepcopy(board.piecePos)
        if isValid:
            

            # Drop piece to bottom and get pos height, and lines cleared
            landingHeight, lines = board.drop_piece()
            # tile local positions
            tiles = [i.position[1] for i in board.mainPiece.tiles]

            # Calculate heuristic and add it to dictionary as a valid route
            props = get_board_props(board, landingHeight[0], tiles, lines)
 
            states[(displacement, rotation)] = props
   
            # Reset board but keep piece horizontal displacement
            grid = [x[:] for x in initialBoard.grid] # reset board game
            bag = [x for x in initialBoard.bag] # reset board bag
            board.reset(grid = grid, bag = bag, piecePos = piecePos,
                mainPiece = copy.deepcopy(gamePiece), storedPiece = copy.deepcopy(initialBoard.storedPiece), 
                canStore = initialBoard.canStore, score= initialBoard.score)

        else:
            # cannot keep moving in direction
            break
        
    # Reset board and position at the end
    grid = [x[:] for x in initialBoard.grid] # reset board game
    bag = [x for x in initialBoard.bag] # reset board bag
    board.reset(grid = grid, bag = bag, piecePos = copy.deepcopy(initialBoard.piecePos),
        mainPiece = copy.deepcopy(gamePiece), storedPiece = copy.deepcopy(initialBoard.storedPiece), 
        canStore = initialBoard.canStore, score= initialBoard.score)

def play(board, displacement, rotation):
    '''Makes a play given a position and a rotation, returning the reward and if the game is over'''
    # initialScore = board.score
    lastPos = board.piecePos
    score = 1
    if displacement == 6:
        board.swap_piece()
    else:
        displacement = displacement*np.array([1, 0])
        for i in range(rotation):
            board.rotate_piece(True, True)
        # Move piece to column
        board.move_piece(displacement)
        
        # Drop piece
        lastPos, lines = board.drop_piece()
        scores = {
            0: 0,
            1: 40,
            2: 100,
            3: 300,
            4: 1200
        }

        score += scores[len(lines)]
    if board.gameOver:
        score -= 5
    return score, board.gameOver, lastPos

def get_board_props(board, landingHeight = 0, tiles = None, lines = None):
    '''Get board properties
        0: Rows cleared
        1: Holes
        2: Bumpiness

        3: Landing height
        4: Row transitions
        5: Column transitions
        6: Cumulative wells
        7: Eroded piece cells

        8: Aggregate height
    :rtype: Integer array'''
    
    if not lines:
        lines = []

    pieceHeight = 0
    erodedPieceCells = 0
    if tiles:
        tiles = copy.deepcopy(tiles)
        highestTile = max(tiles)
        lowestTile = min(tiles)
        trueLandingHeight = landingHeight + lowestTile # Landing height from bottom piece
        highestHeight = landingHeight + highestTile # Landing height for top piece
        meanHeight = (highestHeight - trueLandingHeight)/2 # Total piece height divided by 2
        pieceHeight= (meanHeight + trueLandingHeight + 1) # Calculate height from middle of the piece (bottom row counts as 1)

        for tile in tiles:
            for line in lines:
                tileY = tile
                _, lineY = line
                if tileY + landingHeight == lineY:
                    erodedPieceCells +=1
        erodedPieceCells *= len(lines)


    pieces = {
            piece.IPiece():0,
            piece.JPiece():1,
            piece.LPiece():2,
            piece.OPiece():3,
            piece.SPiece():4,
            piece.TPiece():5,
            piece.ZPiece():6
    }

    storedPiece = None
    if board.canStore:
        storedPiece = type(board.storedPiece)
    else:
        storedPiece = 8

    return [
    len(lines),
    _number_of_holes(board),
    _bumpiness(board),
    pieceHeight,
    _row_roughness(board), # check
    _col_roughness(board), # check
    _cumulative_wells(board),
    erodedPieceCells,
    _total_height(board),
    pieces.get(type(board.storedPiece), 7)
    ]

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
    return totalBumpiness

def _total_height(board):
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

    return sum_height

def _col_roughness(board):
    # print("Col roughness")
    '''Returns the number of vertical cell transitions.'''
    total = 0
    for x in range(board.gridSizeX):
        column_count = 0
        last_empty = False
        for y in reversed(range(board.killHeight)):
            empty = board.grid[y][x] == None
            if last_empty and not empty:
                column_count += 2
            last_empty = empty

        if last_empty and column_count == 1:
            continue

        total += column_count
    # print(total)
    return total

def _row_roughness(board):
    # print("Row roughness")
    '''Returns the number of horizontal cell transitions.'''
    total = 0
    for y in range(board.killHeight):
        row_count = 0
        last_empty = False
        
        for x in range(board.gridSizeX):
            empty = board.grid[y][x] == None
            if last_empty != empty:
                row_count += 1
                last_empty = empty
        if last_empty:
            row_count += 1

        if last_empty and row_count == 2: # One block at the beginning and one at the end 
            continue

        total += row_count
    # print(total)
    return total

def get_board_props2(board, landingHeight = 0, tiles = None, lines = None):
    '''Get properties of the board'''
    if not lines:
        lines = []
    newScore = len(lines)
    holes = _number_of_holes(board)
    total_bumpiness = _bumpiness(board)
    sum_height = _total_height(board)
    return [newScore, holes, total_bumpiness, sum_height]

def _cumulative_wells(board):
    """Returns the sum of all wells."""
    wells = [0 for i in range(board.gridSizeX)]
    depth = [0 for i in range(board.gridSizeX)]

    for y, row in enumerate(board.grid):
        left_block = True
        for x, code in enumerate(row):
            if code == None: # We may have a well
                left_block = x <= 0 or left_block
                right_block = x + 1 >= board.gridSizeX or board.grid[y][x + 1] != None
                if left_block and right_block:
                    depth[x] += 1
                    wells[x] += depth[x]
                else:
                    depth[x] = 0
                left_block = False
            else:
                depth[x] = 0
                left_block = True
    return sum(wells)

def get_state_size():
    '''Size of the state'''
    return 10

# def _cumulative_wells(board):
#     """Returns the sum of all wells."""
#     wells = [0 for i in range(board.gridSizeX)]
#     depth = [0 for i in range(board.gridSizeX)]

#     for x in range(board.gridSizeX):
#         left_block = True
#         for y in range(board.killHeight):
#             cell = board.grid[y][x]
#             if cell == None: # We may have a well
#                 left_block = x <= 0 or board.grid[y][x - 1] != None
#                 right_block = x + 1 >= board.gridSizeX or board.grid[y][x + 1] != None
#                 if left_block and right_block:
#                     depth[x] += 1
#                     wells[x] += depth[x]
#                 else:
#                     depth[x] = 0
#                 left_block = False
#             else:
#                 depth[x] = 0
#                 left_block = True
#             print()
#     return sum(wells)