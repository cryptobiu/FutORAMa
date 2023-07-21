import math
from real_oram.PathORAM.config import config
from real_oram.PathORAM.cruch_oram import CruchORAM
from real_oram.RAM.local_RAM import local_RAM
import random

class PathORAM:

    def __init__(self, number_of_blocks, allocate=False, is_map=False) -> None:
        self.number_of_blocks = 2**math.ceil(math.log(number_of_blocks,2))
        self.conf = config(self.number_of_blocks, is_map)
        self.ram = local_RAM('path_oram_data/{}'.format(math.log(number_of_blocks,2)), self.conf)
        self.local_stash = []
        self.dummy = b'\x00'*self.conf.BALL_SIZE
        # to change
        if (self.conf.N/self.conf.X)*self.conf.BALL_SIZE  < self.conf.LOCAL_MEMORY_SIZE:
            self.position_map = CruchORAM(int(number_of_blocks/self.conf.X))
        else:
            self.position_map = PathORAM(int(number_of_blocks/self.conf.X), allocate, True)
        if allocate:
            self.allocate_memory()
    
    def allocate_memory(self):
        current_write = 0
        empty_memory = [self.dummy]*self.conf.LOCAL_MEMORY_SIZE_IN_BALLS
        while current_write < self.conf.DATA_SIZE:
            self.ram.writeChunks(
                [(current_write, current_write + self.conf.LOCAL_MEMORY_SIZE_IN_BALLS*self.conf.BALL_SIZE)], empty_memory)
            current_write += self.conf.LOCAL_MEMORY_SIZE
    
    def access(self, op, key, data = None):
        old_leaf, new_leaf = self.position_map.position_map_access(key)
        chunks = self.generate_path_chunks(old_leaf)
        result = None
        path = self.ram.readChunks(chunks)
        self.local_stash.extend(filter(lambda a: a != self.dummy, path))
        for i, ball in enumerate(self.local_stash):
            if ball != self.dummy and self.check_key(ball, key):
                ball = self.set_leaf(ball, new_leaf)
                result = self.get_ball_data(ball)
                if op == 'write':
                    ball = self.change_ball_data(ball, data)
                self.local_stash[i] = ball
                break
        if op == 'write' and result == None:
            self.local_stash.append(self.create_ball(key, data, new_leaf))
        write_back = []
        local_stash_and_leafs = [(self.get_leaf(ball), ball) for ball in self.local_stash]
        for i in range(self.conf.NUMBER_OF_LEVELS):
            bucket = []
            for leaf,ball in local_stash_and_leafs:
                if int(leaf/(2**i)) == int(old_leaf/(2**i)):
                    bucket.append(ball)
                    self.local_stash.remove(ball)
                    local_stash_and_leafs.remove((leaf, ball))
                    if len(bucket) == self.conf.Z:
                        break
            write_back.extend(self.complete_bucket(bucket))

        self.ram.writeChunks(chunks, write_back)
        return result

    def position_map_access(self, upper_level_key):
        key = int(upper_level_key/self.conf.X)
        old_leaf, new_leaf = self.position_map.position_map_access(key)
        chunks = self.generate_path_chunks(old_leaf)
        upper_old_leaf = None
        upper_new_leaf = None
        path = self.ram.readChunks(chunks)
        self.local_stash.extend(filter(lambda a: a != self.dummy, path))
        for i, ball in enumerate(self.local_stash):
            if ball != self.dummy and self.check_key(ball, key):
                ball = self.set_leaf(ball, new_leaf)
                upper_old_leaf = self.get_upper_leaf(ball, upper_level_key)
                upper_new_leaf = self.generate_random_upper_leaf()
                ball = self.set_upper_leaf(ball, upper_new_leaf, upper_level_key)
                self.local_stash[i] = ball
        
        if upper_old_leaf == None:
            upper_old_leaf = self.generate_random_upper_leaf()
            upper_new_leaf, ball = self.create_random_map_ball(key, new_leaf, upper_level_key)
            self.local_stash.append(ball)

        write_back = []
        local_stash_and_leafs = [(self.get_leaf(ball), ball) for ball in self.local_stash]
        for i in range(self.conf.NUMBER_OF_LEVELS):
            bucket = []
            for leaf, ball in local_stash_and_leafs:
                if int(leaf/(2**i)) == int(old_leaf/(2**i)):
                    bucket.append(ball)
                    self.local_stash.remove(ball)
                    local_stash_and_leafs.remove((leaf, ball))
                    if len(bucket) == self.conf.Z:
                        break
            write_back.extend(self.complete_bucket(bucket))
        self.ram.writeChunks(chunks, write_back)
        return upper_old_leaf, upper_new_leaf
    
    def set_upper_leaf(self, ball, upper_leaf, upper_level_key):
        index = upper_level_key % self.conf.X
        return ball[:2*self.conf.KEY_SIZE + index*self.conf.UPPER_LAYER_KEY_SIZE] + upper_leaf.to_bytes(self.conf.UPPER_LAYER_KEY_SIZE, 'big') + ball[2*self.conf.KEY_SIZE + (index+1)*self.conf.UPPER_LAYER_KEY_SIZE:]

    def generate_random_upper_leaf(self):
        return random.randint(0,self.number_of_blocks*self.conf.X-1)
    
    def get_upper_leaf(self, ball, upper_level_key):
        data = self.get_ball_data(ball)
        index = upper_level_key % self.conf.X
        return self.bytes_to_int(data[index*self.conf.UPPER_LAYER_KEY_SIZE: (index +1)*self.conf.UPPER_LAYER_KEY_SIZE])

    def create_random_map_ball(self, key, leaf, upper_level_key):
        ###########################################
        data = [self.generate_random_upper_leaf().to_bytes(self.conf.UPPER_LAYER_KEY_SIZE, 'big') for _ in range(self.conf.X*2)]
        data = b''.join(data)
        ball = self.create_ball(key, data, leaf)
        return self.get_upper_leaf(ball, upper_level_key), ball

    def create_ball(self, key, data, leaf):
        ball = key.to_bytes(self.conf.KEY_SIZE, 'big') + leaf.to_bytes(self.conf.KEY_SIZE, 'big')+ data #preformance
        return ball
  
    def get_ball_data(self, ball):
        return ball[self.conf.KEY_SIZE*2:]

    def complete_bucket(self, bucket):
        bucket.extend([self.dummy]*(self.conf.Z - len(bucket)))
        return bucket

    def get_leaf(self, ball):
        return self.bytes_to_int(ball[self.conf.KEY_SIZE:2*self.conf.KEY_SIZE])

    def change_ball_data(self, ball, data):
        return ball[:self.conf.KEY_SIZE*2] + data
    
    def set_leaf(self, ball, leaf):
        return ball[:self.conf.KEY_SIZE] + leaf.to_bytes(self.conf.KEY_SIZE, 'big') + ball[self.conf.KEY_SIZE*2:]
    
    def bytes_to_int(self, _bytes):
        return int.from_bytes(_bytes, 'big', signed=False)

    def check_key(self, ball, key):
        byte_key = ball[:self.conf.KEY_SIZE]
        return self.bytes_to_int(byte_key) == key

    def generate_path_chunks(self, leaf):
        chunks = []
        starting_point = 0
        advance = self.conf.N
        while advance >= 1:
            chunks.append((starting_point + leaf*self.conf.BUCKET_SIZE, starting_point + leaf*self.conf.BUCKET_SIZE + self.conf.BUCKET_SIZE))
            starting_point += int(advance*self.conf.BUCKET_SIZE)
            advance /= 2
            leaf = int(leaf/2)
        return chunks


    
    


