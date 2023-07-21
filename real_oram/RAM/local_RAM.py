import math
from real_oram.config import baseConfig

class local_RAM:
    BALL_READ = 0
    BALL_WRITE = 0
    RT_READ = 0
    RT_WRITE = 0
    
    def __init__(self, file_path, conf:baseConfig) -> None:
        self.conf = conf
        self.file_path = file_path
        self.memory = []


    def readBall(self, location):
        local_RAM.BALL_READ += 1
        return self.memory[int(location/self.conf.BALL_SIZE)]


    def writeBall(self, location, ball):
        local_RAM.BALL_WRITE += 1
        self.memory[int(location/self.conf.BALL_SIZE)] = ball
    
    def readChunk(self, chunk):
        start, end = chunk
        balls_num = int((end-start)/self.conf.BALL_SIZE)
        local_RAM.BALL_READ += balls_num
        return self.memory[int(start/self.conf.BALL_SIZE):int(end/self.conf.BALL_SIZE)]
    
    def writeChunk(self, chunk, balls):
        start, end = chunk
        balls_num = int((end-start)/self.conf.BALL_SIZE)
        local_RAM.BALL_WRITE += balls_num
        ball_start = int(start/self.conf.BALL_SIZE)
        if ball_start >= len(self.memory):
            self.memory.extend(balls)
        else:
            self.memory[ball_start:ball_start + len(balls)] = balls
        
        

    def readChunks(self, chunks):
        local_RAM.RT_READ += 1
        balls = []
        for chunk in chunks:
            chunk_balls = self.readChunk(chunk)
            balls.extend(chunk_balls)
        return balls

    def writeChunks(self, chunks, balls):
        local_RAM.RT_WRITE += 1
        i = 0
        for chunk in chunks:
            start, end = chunk
            balls_num = math.ceil((end-start)/self.conf.BALL_SIZE)
            self.writeChunk(chunk, balls[i:i+balls_num])
            i += balls_num
        return balls

    def readBalls(self, locations):
        local_RAM.RT_READ += 1
        return [self.readBall(location) for location in locations]
    
    def writeBalls(self, locations, balls):
        local_RAM.RT_WRITE += 1
        return [self.writeBall(location, ball) for location,ball in zip(locations,balls)]

    def getSize(self):
        if self.conf.FINAL:
            return 2*self.conf.DATA_SIZE
        return self.conf.DATA_SIZE

    def generate_empty_ball_with_key(self, key):
        return self.empty_data + self.conf.DATA_STATUS + key.to_bytes(self.conf.KEY_SIZE, 'big')

    def generate_random_memory(self, number_of_balls):
        self.empty_data = self.conf.BALL_DATA_SIZE*self.conf.DUMMY_STATUS
        self.memory = [self.generate_empty_ball_with_key(i) for i in range(number_of_balls)]

def reset_counters():
    local_RAM.BALL_READ = 0
    local_RAM.BALL_WRITE = 0
    local_RAM.RT_READ = 0
    local_RAM.RT_WRITE = 0