from counter_only.PathORAM.config import config
import random

class CruchORAM:
    def __init__(self, block_size, number_of_blocks) -> None:
        self.number_of_blocks = number_of_blocks
        self.conf = config(block_size, number_of_blocks)
        self.dic = {}
    
    def number_of_levels(self):
        return 0
        
    def number_of_blocks_per_access(self):
        return 0

    def number_of_bytes_per_access(self):
        return 0

    def position_map_access(self, key):
        old_leaf = random.randint(0,self.number_of_blocks*self.conf.X-1) if key not in self.dic else self.dic[key]
        self.dic[key] = random.randint(0,self.number_of_blocks*self.conf.X-1)
        return old_leaf, self.dic[key]
