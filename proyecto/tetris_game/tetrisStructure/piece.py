import numpy as np
import tetrisStructure.tile as tc
from abc import ABCMeta, abstractmethod

# __all__ = ['ZPiece', 'IPiece', 'OPiece', 'SPiece', 'TPiece', 'JPiece', 'LPiece']

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

    # def __str__(self):
    #     return super().__str__()
    
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

class SPiece(Piece):
    color = (0, 255, 0)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([1,1])
        self.tiles[3].position = np.array([0,1])

class ZPiece(Piece):
    color = (255, 0, 0)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([0,1])
        self.tiles[2].position = np.array([-1,1])
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
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([1,0]) * 2
        self.tiles[3].position = np.array([1,0])

class OPiece(Piece):
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
        self.tiles[3].position = np.array([0,1])

class LPiece(Piece):
    color = (255, 165, 0)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([1,1])
        self.tiles[3].position = np.array([1,0])

class JPiece(Piece):
    color = (0, 0, 255)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([-1,1])
        self.tiles[3].position = np.array([1,0])

class TPiece(Piece):
    color = (128, 0, 128)

    def _make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([0,1])
        self.tiles[3].position = np.array([1,0])
