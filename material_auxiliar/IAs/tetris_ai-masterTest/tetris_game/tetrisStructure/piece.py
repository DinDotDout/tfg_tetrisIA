import numpy as np
from . import tile as tc
from abc import ABCMeta, abstractmethod

# __all__ = ['ZPiece', 'IPiece', 'OPiece', 'SPiece', 'TPiece', 'JPiece', 'LPiece']

def get_piece_type(n):
    pieces = [
        SPiece(),
        ZPiece(),
        IPiece(),
        TPiece(),
        JPiece(),
        LPiece(),
        OPiece()
    ]
    return pieces[n]

def get_piece_number(piece):
    # isinstance(obj, a)
    pieceType = type(piece)
    if isinstance(piece, type(SPiece())):
        return 0
    elif isinstance(piece, type(ZPiece())):
        return 1
    elif isinstance(piece, type(IPiece())):
        return 2
    elif isinstance(piece, type(TPiece())):
        return 3
    elif isinstance(piece, type(JPiece())):
        return 4
    elif isinstance(piece, type(LPiece())):
        return 5
    elif isinstance(piece, type(OPiece())):
        return 6
    else: 
        return 7 # None


class Piece(object, metaclass=ABCMeta):

    offset_list = np.array(
        [
            [
                [0, 0],
                [0, 0],
                [0, 0],
                [0, 0]
            ],
            [
                [0, 0],
                [1, 0],
                [0, 0],
                [-1, 0]
            ],
            [
                [0, 0],
                [1, -1],
                [0, 0],
                [-1, -1]
            ],
            [
                [0, 0],
                [0, 2],
                [0, 0],
                [0, 2]
            ],
            [
                [0, 0],
                [1, 2],
                [0, 0],
                [-1, 2]
            ]
        ]
    )
    
    def __init__(self):
        self.rotationIndex = 0
        self.tiles = [tc.Tile() for i in range(4)]
        self._make_shape()
    
    @abstractmethod
    def _make_shape(self):
        "Creates the corresponding piece shape"
        raise NotImplementedError

    def rotate(self, clockwise):
        oldRotationIndex = self.rotationIndex
        self.rotationIndex += 1 if clockwise else -1
        self.rotationIndex %= 4
        for i in range(len(self.tiles)):
            self.tiles[i].rotate_tile(self.tiles[0].position, clockwise)

    def reset_rotation(self):
        self._make_shape()
        
    @property
    def color(self):
        raise NotImplementedError

    @property
    def tiles(self):
        return self._tiles

    @tiles.setter
    def tiles(self, tiles):
        self._tiles = tiles

    @property
    def rotationIndex(self):
        return self._rotationIndex

    @rotationIndex.setter
    def rotationIndex(self, rotationIndex):
        self._rotationIndex = rotationIndex

class SPiece(Piece): # 
    color = (0, 255, 0)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([1,1])
        self.tiles[3].position = np.array([0,1]) # primera deteccion

class ZPiece(Piece):
    color = (255, 0, 0)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([0,1])
        self.tiles[2].position = np.array([-1,1]) # primera deteccion
        self.tiles[3].position = np.array([1,0])

class IPiece(Piece):
    color = (0, 255, 255)

    offset_list = np.array(
        [
            [
                [0, 0],
                [-1, 0],
                [-1, 1],
                [0, 1]
            ],
            [
                [-1, 0],
                [0, 0],
                [1, 1],
                [0, 1]
            ],
            [
                [2, 0],
                [0, 0],
                [-2, 1],
                [0, 1]
            ],
            [
                [-1, 0],
                [0, 1],
                [1, 0],
                [0, -1]
            ],
            [
                [2, 0],
                [0, -2],
                [-2, 0],
                [0, 2]
            ]
        ]
    )

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0]) # primera deteccion
        self.tiles[2].position = np.array([1,0]) * 2
        self.tiles[3].position = np.array([1,0])

class OPiece(Piece): # 2,2
    color = (255, 255, 0)
    offset_list = np.array(
        [
            [
                [0, 0],
                [0, -1],
                [-1, -1],
                [-1, 0]
            ]
        ]
    )

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([1,0])
        self.tiles[2].position = np.array([1,1]) 
        self.tiles[3].position = np.array([0,1]) # primera deteccion

class LPiece(Piece):
    color = (255, 165, 0)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([1,1]) # primera deteccion
        self.tiles[3].position = np.array([1,0])

class JPiece(Piece): #  -1,1
    color = (0, 0, 255)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([-1,1]) # primera deteccion
        self.tiles[3].position = np.array([1,0])

class TPiece(Piece): # 0,1
    color = (128, 0, 128)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([0,1]) # primera deteccion
        self.tiles[3].position = np.array([1,0])
