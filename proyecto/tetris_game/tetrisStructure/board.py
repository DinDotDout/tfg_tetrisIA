import numpy as np
import random as rnd
from . import tile as tc
from . import piece as pc

class Board():
    gridSizeY = 24
    gridSizeX = 10
    killHeight = 21

    def __init__(self, grid = None, bag = [], piecePos = None,
                    mainPiece = None, storedPiece = None, canStore = False):
        self.reset()
        # self.gameOver = False

        # if grid:
        #     self.grid = grid
        # else:
        #     self.grid = self._create_grid()

        # self.bag = bag # list off upcoming pieces
        
        # if  mainPiece and piecePos:
        #     self.piecePos = piecePos
        #     self.mainPiece = mainPiece
        # else:
        #     self._spawn_piece()
       
        # self.storedPiece = storedPiece
        # self.canStore = canStore
        # self.reseted = False
        # self.score = 0
    
    def reset(self, grid = None, bag = [], piecePos = None,
                    mainPiece = None, storedPiece = None, canStore = False):
        self.gameOver = False

        if grid:
            self.grid = grid
        else:
            self.grid = self._create_grid()

        self.bag = bag # list off upcoming pieces

        if mainPiece and piecePos is not None:
            self.piecePos = piecePos
            self.mainPiece = mainPiece
        else:
            self._spawn_piece()
       
        self.storedPiece = storedPiece
        self.canStore = canStore
        self.reseted = False
        self.score = 0


    def _create_grid(self):
        "Creates a grid of sized based off of gridSizeX and gridSizeY variables"
        # We add an extra row to manage pieces out of the players sight
        grid = [[None for col in range(self.gridSizeX)] for row in range(self.gridSizeY)]
        # for y in range(self.gridSizeY):
        #     for x in range(self.gridSizeX):
        #         grid[y][x] = GridCell()
        return grid

    def __str__(self):
        out = []
        for row in self.grid:
            out.append(''.join([str(cell) for cell in row]))

        mainBlocks = []
        if self.mainPiece:
            for tiles in self.mainPiece.tiles:
                x, y = tiles.position+self.piecePos
                if y < 20:
                    replacement = out[y][:x] + '1' + out[y][x+1:]
                    out[y] = replacement
        out.reverse()
        return '\n'.join(out)
    
    def get_piece_type(self, n):
        pieces = [
            pc.IPiece(),
            pc.JPiece(),
            pc.LPiece(),
            pc.OPiece(),
            pc.SPiece(),
            pc.TPiece(),
            pc.ZPiece()
        ]
        return pieces[n]

    def _spawn_piece(self):
        "Refills bag if necessary and sets next piece in bag as main piece"
        
        # Append next bag if current bag is under 7
        if len(self.bag) < 7:  # check to see if list is empty
            self._fill_bag()

        self.mainPiece = self.get_piece_type(self.bag.pop(0)) # get current piece
        self.piecePos = self._spawn_height()    

        self.canStore = True
        self.reseted = True
    
    def _spawn_height(self, height = np.array([4,18])):
        spawn_pos = np.copy(height)
        if not self._can_spawn_piece(spawn_pos):
            spawn_pos[1] += 1
            if not self._can_spawn_piece(spawn_pos):
                spawn_pos[1] += 1
                if not self._can_spawn_piece(spawn_pos):
                    self.gameOver = True
        return spawn_pos

    def _fill_bag(self):
        "Refills bag with a random order"
        pieceIndex = [
            0,
            1,
            2,
            3,
            4,
            5,
            6
        ]

        rnd.shuffle(pieceIndex)  # shuffle list
        self.bag.extend(pieceIndex)  # add new pieces

    def swap_piece(self):
        "stores main piece and draws out the stored one or a new one"
        if not self.storedPiece:
            self.mainPiece.reset_rotation()
            self.storedPiece = self.mainPiece
            self._spawn_piece()
            self.canStore = False
        elif self.canStore:
            self.mainPiece.reset_rotation()
            aux = self.storedPiece
            self.storedPiece = self.mainPiece
            self.mainPiece = aux
            self.canStore = False
            self.piecePos = self._spawn_height()
            self.reseted = True
            

    def rotate_piece(self, clockwise, shouldOffset):
        "Rotates piece by 90º"
        oldRotation = self.mainPiece.rotationIndex
        self.mainPiece.rotate(clockwise)
        newRotation = self.mainPiece.rotationIndex

        movePossible = True
        if shouldOffset:
            movePossible = self._offset_piece(oldRotation, newRotation)
        if not movePossible:
            self.mainPiece.rotate(not clockwise)
        
    def _offset_piece(self,oldRotation, newRotation):
        "Checks if the piece can be offsetted following the rules of the SRS"
        for offset in self.mainPiece.offset_list:
            offsetVal1 = offset[oldRotation]
            offsetVal2 = offset[newRotation]
            endOffset = offsetVal1 - offsetVal2
            if (self.move_piece(endOffset, True)):
                return True
        return False
    
    def move_piece(self, movement, isOffseting = False):
        "Checks if all tiles can be moved to the position and does so"
        canMove = True
        for tile in self.mainPiece.tiles:
            globalTilePos = self.piecePos + tile.position # center position + tile displacement
            newGlobalTilePos = globalTilePos + movement # add movement
            if not self._is_in_bounds(newGlobalTilePos) or not self._is_cell_empty(newGlobalTilePos):
                canMove = False
                break

        if not canMove:
            if movement[0] == 0 and movement[1] == -1 and not isOffseting: # Lock piece if can't move down
                self._lock_piece()
            return False 
        self.piecePos += movement
        return True

    def _lock_piece(self):
        "Locks the piece in place if it reaches the bottom or collides with another"       
        for tile in self.mainPiece.tiles:
            globalTilePos = self.piecePos + tile.position
            x, y = globalTilePos

            if y >= self.killHeight:
                self.gameOver = True
                return
            
            self.grid[y][x] = tile.color

        self._spawn_piece()
        self._check_line_clears()
        
        
    def drop_piece(self):
        "Drops the piece in a straight direction to the lowest position it can"
        canDrop = True
        down = np.array([0,-1])
        while canDrop:
            canDrop = self.move_piece(down)
    def _is_in_bounds(self, pos, ):
        "Checks to see if the coordinate is within the tetris board bounds"
        x, y = pos
        if x < 0 or x >= self.gridSizeX or y < 0:
            return False
        else:
            return True

    def _is_cell_empty(self, pos):
        "Checks to see if the coordinates are occupied by a block"
        x, y = pos
        if self.grid[y][x]:
            return False
        else:
            return True

    def _can_spawn_piece(self, pos):
        "Checks the spawn position is free"
        for tile in self.mainPiece.tiles:
            globalTilePos = pos + tile.position # center position + tile displacement
            if not self._is_in_bounds(globalTilePos) or not self._is_cell_empty(globalTilePos):
                return False
        return True

    def _clear_line(self, line):
        if line < 0 or line > self.gridSizeY:
            print("line out of bounds")
            return
        
        for x in range(self.gridSizeX):
            self.grid[line][x] = None
        for lineToDrop in range(line+1, self.gridSizeY):
                for x in range(self.gridSizeX):
                    color = self.grid[lineToDrop][x]     
                    if color:
                        self.grid[lineToDrop-1][x] = color
                        self.grid[lineToDrop][x]  = None


    def _check_line_clears(self):
        # linesToClear = []
        consecutiveLineClears = 0

        for y in range(self.gridSizeY-1, -1, -1): #loop from top to bottom
            lineClear = True
            for x in range(self.gridSizeX):
                if not self.grid[y][x]:
                    lineClear = False
                    # consecutiveLineClears = 0
                    break
                
            if lineClear:
                # linesToClear.append(y)
                consecutiveLineClears += 1
                if consecutiveLineClears == 4:
                    # print TETRIS! and add points
                    print("TETRIS!")
                self._clear_line(y)
        self.score += consecutiveLineClears**2
            # self.score = len(linesToClear)*2
        # linesToClear.reverse()

        # Drop lines above lines cleared in inverse order
        # Some lines will drop more than once depending on the lines cleared
        # if len(linesToClear) > 0:
        #     for i in range(len(linesToClear)):
        #         # for lineToDrop in range(linesToClear[i] + 1 - i, self.gridSizeY):
        #         for lineToDrop in range(linesToClear[i] , self.gridSizeY):
        #             print(lineToDrop)
        #             for x in range(self.gridSizeX):
        #                 cell = self.grid[lineToDrop][x]     
        #                 if cell.isOccupied:
            
        #                     self.grid[lineToDrop-1][x].block = cell.block
        #                     self.grid[lineToDrop-1][x].isOccupied = cell.isOccupied
        #                     cell.block = None
        #                     cell.isOccupied = False

    # Returns a matrix containing the colors of the cells
    def grid_colors(self):
        gridColors = [[None for col in range(self.gridSizeX)] for row in range(self.gridSizeY)]
        for y in range(self.gridSizeY-4): # don't show info on placed pieces out of grid
            for x in range(0, self.gridSizeX):
                if self.grid[y][x]:
                    gridColors[y][x] = self.grid[y][x]
                else:
                    gridColors[y][x] = (0, 0, 0)

        for tile in self.mainPiece.tiles:
            x, y = self.piecePos + tile.position
            if x >= 0 and x < self.gridSizeX: # Checks only pieces within grid
                gridColors[y][x] = self.mainPiece.color
        gridColors.reverse()
        return gridColors

# class GridCell:
#     def __init__(self):
#         # self.location = vector(x,y)
#         self.isOccupied = False
#         self.block = None

#     def __str__(self):
#         return str(1 if self.isOccupied else 0)