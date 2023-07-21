from Cryptodome.Cipher import AES
from counter_only.RAM.local_RAM import local_RAM
from counter_only.config import config


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
   
    def obliviousShiftData(self, ram, number_of_bins, shift_position):
        # for i in range(number_of_bins):
            # balls = self.readTransposedAndShifted(ram, number_of_bins, i*self.conf.BALL_SIZE, 2*self.conf.MU, shift_position)
        local_RAM.BALL_READ += number_of_bins*2*self.conf.MU
        local_RAM.RT_READ += 1*number_of_bins
        local_RAM.BALL_WRITE += 2*self.conf.MU*number_of_bins
        local_RAM.RT_WRITE += 1*number_of_bins
            # self.writeTransposed(ram, balls, number_of_bins, i*self.conf.BALL_SIZE)
    
    def removeSecondStatus(self, balls):
        result = []
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] in [self.conf.SECOND_DUMMY_STATUS, self.conf.DUMMY_STATUS] and self.conf.FINAL:
                continue
            elif ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.SECOND_DATA_STATUS:
                result.append(self.changeBallStatus(ball, self.conf.DATA_STATUS))
            elif ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.SECOND_DUMMY_STATUS:
                result.append(self.changeBallStatus(ball, self.conf.DUMMY_STATUS))
            elif ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.STASH_DATA_STATUS:
                result.append(self.changeBallStatus(ball, self.conf.DATA_STATUS))
            elif ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.STASH_DUMMY_STATUS:
                result.append(self.changeBallStatus(ball, self.conf.DUMMY_STATUS))
            else:    
                result.append(ball)
        return result
    
    def switchToSecondStatus(self, ball):
        if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DATA_STATUS:
            return self.changeBallStatus(ball, self.conf.SECOND_DATA_STATUS)
        elif ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DUMMY_STATUS:
            return self.changeBallStatus(ball, self.conf.SECOND_DUMMY_STATUS)
        else:
            return ball
     
    def changeBallsStatus(self, balls, status):
        return [self.changeBallStatus(ball, status) for ball in balls]
    
    def changeBallStatus(self, ball, status):
        return ball[:self.conf.BALL_STATUS_POSITION] + status + ball[1 + self.conf.BALL_STATUS_POSITION:]
    
    def ballsToDictionary(self, balls):
        dic = {}
        for ball in balls:
            dic[ball[1 + self.conf.BALL_STATUS_POSITION:]] = ball
        return dic
            
            
            
