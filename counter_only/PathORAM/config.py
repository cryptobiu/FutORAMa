

import math
from counter_only.config import baseConfig


class config(baseConfig):


    def __init__(self, BLOCK_SIZE, N, is_map=False):

        self.N = N
        self.Z = 4

        # if the block size is too small it'll cause division by zero
        if BLOCK_SIZE < 128:
            self.X = 4
        else:
            self.X = int(BLOCK_SIZE/math.ceil(math.log(N,2)))
        self.KEY_SIZE = math.ceil(math.ceil(math.log(N,2))/8)
        if not is_map:
            self.BALL_DATA_SIZE = BLOCK_SIZE
            # the balls structure:  KEY || LEAF || DATA
            self.BALL_SIZE = 2*self.KEY_SIZE + self.BALL_DATA_SIZE
        else:
            self.UPPER_LAYER_KEY_SIZE = math.ceil(math.ceil(math.log(N*self.X,2))/8)
            self.BALL_DATA_SIZE = 2*self.UPPER_LAYER_KEY_SIZE*self.X
            # the balls structure:  KEY || LEAF || [ LEAF' ]*X
            self.BALL_SIZE = 2*self.KEY_SIZE + self.BALL_DATA_SIZE
            # raise "not implemented yet"
        
        self.LOCAL_MEMORY_SIZE = 131_220*self.BALL_DATA_SIZE#3*2*30*(9**3)*16
        self.LOCAL_MEMORY_SIZE_IN_BALLS = int(self.LOCAL_MEMORY_SIZE/self.BALL_SIZE)
        self.DATA_SIZE = N*self.BALL_SIZE*2*self.Z
        self.BUCKET_SIZE = self.Z*self.BALL_SIZE
        self.NUMBER_OF_LEVELS = int(math.ceil(math.log(N,2))) + 1