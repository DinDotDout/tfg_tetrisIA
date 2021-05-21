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
    newScore = board.score - initialScore
    holes = _number_of_holes(board)
    total_bumpiness, max_bumpiness = _bumpiness(board)
    sum_height, max_height, min_height = _height(board)
    return [newScore, holes, total_bumpiness, sum_height]

def get_next_states(board):
    '''Get all possible next states'''
    states = {}
    mainPiece = board.mainPiece
    
    displacements = list(range(-5, 6))
    movement = np.array([1,0])

    rotations = 4
    pieceType = type(mainPiece)
    if pieceType is OPiece: # O piece is in the same position even if we roate
        rotations = 1
    # elif pieceType is SPiece or pieceType is ZPiece or pieceType is IPiece: # Rotations 3 and 4 are similar to 1 and 2
    #     rotations = 2
    
    initialBoard = copy.deepcopy(board) # Save initial board state
    copyBoard = copy.deepcopy(board)
    initialScore = initialBoard.score

    gamePiece = copy.deepcopy(mainPiece) # We will use this piece to preserve rotation

    if board.canStore:
        board.swap_piece()
        props = get_board_props(board, initialScore)
        states[(6, 0)] = props
        grid = [x[:] for x in initialBoard.grid] # reset board game
        bag = [x for x in initialBoard.bag] # reset board bag
        board.reset(grid = grid, bag = bag, piecePos = copy.deepcopy(initialBoard.piecePos),
            mainPiece = copy.deepcopy(gamePiece), storedPiece = initialBoard.storedPiece,
            canStore = initialBoard.canStore, score= initialScore)
    lineClear = False

    # For all rotations
    for rotation in range(rotations):
        # For all positions
        for displacement in displacements:
            isValid = board.move_piece(displacement*movement) 
            if isValid:
                # Drop piece to bottom
                board.drop_piece()

                # Calculate heuristic and add it to dictionary as a valid route
                props = get_board_props(board, initialScore)
                states[(displacement, rotation)] = props

            grid = [x[:] for x in initialBoard.grid] # reset board game
            bag = [x for x in initialBoard.bag] # reset board bag
            board.reset(grid = grid, bag = bag, piecePos = copy.deepcopy(initialBoard.piecePos),
                mainPiece = copy.deepcopy(gamePiece), storedPiece = initialBoard.storedPiece, 
                canStore = initialBoard.canStore, score= initialScore)

        board.rotate_piece(True, True)
        gamePiece = copy.deepcopy(board.mainPiece) # replace gamePiece with new rotation

    return states, initialBoard
    
    # return states, initialBoard

def play(board, displacement, rotation):
    '''Makes a play given a position and a rotation, returning the reward and if the game is over'''
    initialScore = board.score
    lastPos = board.piecePos
    if displacement == 6:
        board.swap_piece()
    else:
        displacement = displacement*np.array([1, 0])
        for i in range(rotation):
            board.rotate_piece(True, True)
        # Move piece to column
        board.move_piece(displacement)
        
        # Drop piece
        lastPos = board.drop_piece()

    score = 1 + ((board.score - initialScore)**2)*board.gridSizeX
    if board.gameOver:
        score -= 5
    return score, board.gameOver, lastPos

def get_state_size():
    '''Size of the state'''
    return 4

def get_info(self, rows_cleared):
    """Returns the state of the board using statistics.
        0: Rows cleared
        1: Bumpiness
        2: Holes
        3: Landing height
        4: Row transitions
        5: Column transitions
        6: Cumulative wells
        7: Eroded piece cells
        8: Aggregate height
    :rtype: Integer array
    """
    if self.piece_last is not None:
        last_piece_coords = self.piece_last.get_shape_coords()
        eroded_piece_cells = len(rows_cleared) * sum(y in rows_cleared for x, y in last_piece_coords)
        landing_height = 0 if self.piece_last is None else 1 + self.rows - max(y for x, y in last_piece_coords)
    else:
        eroded_piece_cells = 0
        landing_height = 0

    return [
        len(rows_cleared),
        self.get_bumpiness(),
        self.get_hole_count(),
        landing_height,
        self.get_row_transitions(),
        self.get_column_transitions(),
        self.get_cumulative_wells(),
        eroded_piece_cells,
        self.get_aggregate_height(),
    ]

def get_cleared_rows(self):
    """Returns the the amount of rows cleared."""
    return list(filter(lambda y: self.is_row(y), range(self.rows)))

def get_row_transitions(self):
    """Returns the number of horizontal cell transitions."""
    total = 0
    for y in range(self.rows):
        row_count = 0
        last_empty = False
        for x in range(self.columns):
            empty = self.pieces_table[y][x] == 0
            if last_empty != empty:
                row_count += 1
                last_empty = empty

        if last_empty:
            row_count += 1

        if last_empty and row_count == 2:
            continue

        total += row_count
    return total

def get_column_transitions(self):
    """Returns the number of vertical cell transitions."""
    total = 0
    for x in range(self.columns):
        column_count = 0
        last_empty = False
        for y in reversed(range(self.rows)):
            empty = self.pieces_table[y][x] == 0
            if last_empty and not empty:
                column_count += 2
            last_empty = empty

        if last_empty and column_count == 1:
            continue

        total += column_count
    return total

def get_bumpiness(self):
    """Returns the total of the difference between the height of each column."""
    bumpiness = 0
    last_height = -1
    for x in range(self.columns):
        current_height = 0
        for y in range(self.rows):
            if self.pieces_table[y][x] != 0:
                current_height = self.rows - y
                break
        if last_height != -1:
            bumpiness += abs(last_height - current_height)
        last_height = current_height
    return bumpiness

def get_cumulative_wells(self):
    """Returns the sum of all wells."""
    wells = [0 for i in range(self.columns)]
    for y, row in enumerate(self.pieces_table):
        left_empty = True
        for x, code in enumerate(row):
            if code == 0:
                well = False
                right_empty = self.columns > x + 1 >= 0 and self.pieces_table[y][x + 1] == 0
                if left_empty or right_empty:
                    well = True
                wells[x] = 0 if well else wells[x] + 1
                left_empty = True
            else:
                left_empty = False
    return sum(wells)

def get_aggregate_height(self):
    """Returns the sum of the heights of each column."""
    aggregate_height = 0
    for x in range(self.columns):
        for y in range(self.rows):
            if self.pieces_table[y][x] != 0:
                aggregate_height += self.rows - y
                break
    return aggregate_height

def get_hole_count(self):
    """returns the number of empty cells covered by a full cell."""
    hole_count = 0
    for x in range(self.columns):
        below = False
        for y in range(self.rows):
            empty = self.pieces_table[y][x] == 0
            if not below and not empty:
                below = True
            elif below and empty:
                hole_count += 1
    return hole_count

