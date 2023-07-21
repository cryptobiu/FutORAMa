from Cryptodome.Cipher import AES
from real_oram.RAM.local_RAM import local_RAM
from real_oram.config import config


class ByteOperations:
    def __init__(self,key, conf:config) -> None:
        self.conf = conf
        self.key_length = len(key)
        self.cipher = AES.new(key, AES.MODE_ECB, use_aesni=True)
        self.empty_value = b'\x00'*conf.BALL_STATUS_POSITION

    
    def isBitOn(self, number, bit_num):
        return (number & (2**bit_num)) > 0


    def getCapacity(self, capacity_ball):
        if capacity_ball[: self.conf.BALL_STATUS_POSITION] != self.empty_value or capacity_ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] != self.conf.DUMMY_STATUS:
            return 0
        else:
            return int.from_bytes(capacity_ball, 'big', signed=False)
        
    
    def constructCapacityThresholdBall(self, capacity, threshold):
        capacity_bytes = capacity.to_bytes(int((self.conf.BALL_SIZE - self.conf.BALL_STATUS_POSITION)/2 + 1), 'big')
        threshold_bytes = threshold.to_bytes(int((self.conf.BALL_SIZE - self.conf.BALL_STATUS_POSITION)/2 + 1), 'big')
        length = len(capacity_bytes) + len(threshold_bytes)
        return self.conf.DUMMY_STATUS*(self.conf.BALL_SIZE - length) + capacity_bytes + threshold_bytes
    
    def deconstructCapacityThresholdBall(self, ball):
        length = int((self.conf.BALL_SIZE - self.conf.BALL_STATUS_POSITION)/2 + 1)
        threshold = int.from_bytes(ball[self.conf.BALL_STATUS_POSITION + length:], 'big', signed=False)
        capacity = int.from_bytes(ball[:self.conf.BALL_SIZE - length], 'big', signed=False)
        return capacity, threshold
        
    def ballToPseudoRandomNumber(self, ball,limit = -1):
        ball_key = ball[self.conf.BALL_STATUS_POSITION + 1:]
        return self.keyToPseudoRandomNumber(ball_key, limit)
        
    def keyToPseudoRandomNumber(self, key,limit=-1):
        if len(key) % self.key_length != 0:
            key += b'\x00'*(self.key_length - len(key) % self.key_length)
        enc = self.cipher.encrypt(key)
        if limit == -1:
            return int.from_bytes(enc, 'big', signed=False)
        return int.from_bytes(enc, 'big', signed=False) % limit
    
    def writeTransposed(self, ram: local_RAM, balls, offset, start):
        chunks = []
        for i in range(len(balls)):
            chunks.append((start + i*offset*self.conf.BALL_SIZE, start + i*offset*self.conf.BALL_SIZE + self.conf.BALL_SIZE))
        ram.writeChunks(chunks, balls)

    def readTransposed(self, ram: local_RAM, offset, start, readLength):
        chunks = []
        for i in range(readLength):
            chunks.append((start + i*offset*self.conf.BALL_SIZE, start + i*offset*self.conf.BALL_SIZE + self.conf.BALL_SIZE))
        return ram.readChunks(chunks)
    
    def readTransposedGetMixedStripeIndexes(self, ram: local_RAM, offset, start, readLength, mixed_start, mixed_end):
        chunks = []
        mixed_indexes = []
        for i in range(readLength):
            if start + i*offset*self.conf.BALL_SIZE >= mixed_start and start + i*offset*self.conf.BALL_SIZE + self.conf.BALL_SIZE <= mixed_end:
                mixed_indexes.append(i)
            chunks.append((start + i*offset*self.conf.BALL_SIZE, start + i*offset*self.conf.BALL_SIZE + self.conf.BALL_SIZE))
        balls = ram.readChunks(chunks)
        return balls, mixed_indexes

    def readTransposedAndShifted(self, ram: local_RAM, offset, start, readLength, shift_position):
        chunks = []
        shift = 0
        for i in range(readLength):
            if start + i*offset*self.conf.BALL_SIZE < shift_position:
                shift += 1
            chunks.append((start + i*offset*self.conf.BALL_SIZE, start + i*offset*self.conf.BALL_SIZE + self.conf.BALL_SIZE))
        balls = ram.readChunks(chunks)
        
        return balls[-shift:] + balls[:-shift]
   
    def obliviousShiftData(self, ram, number_of_bins, shift_position):
        for i in range(number_of_bins):
            balls = self.readTransposedAndShifted(ram, number_of_bins, i*self.conf.BALL_SIZE, 2*self.conf.MU, shift_position)
            self.writeTransposed(ram, balls, number_of_bins, i*self.conf.BALL_SIZE)
     
    def changeBallsStatus(self, balls, status):
        return [self.changeBallStatus(ball, status) for ball in balls]
    
    def changeBallStatus(self, ball, status):
        return ball[:self.conf.BALL_STATUS_POSITION] + status + ball[1 + self.conf.BALL_STATUS_POSITION:]
    
    def ballsToDictionary(self, balls):
        dic = {}
        for ball in balls:
            dic[ball[1 + self.conf.BALL_STATUS_POSITION:]] = ball
        return dic
            
            
            
