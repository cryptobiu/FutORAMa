from real_oram.config import config
import numpy as np

class ThresholdGenerator:
    def __init__(self, conf:config) -> None:
        self.conf = conf
        self.reset()
        pass
    
    def reset(self):
        self.b = self.conf.NUMBER_OF_BINS
        self.nPrime = self.conf.N - int(self.conf.N*self.conf.EPSILON)
    
    def generate(self):
        sample = np.random.binomial(self.nPrime, 1/self.b)
        self.b -= 1
        self.nPrime -= sample
        return sample
    
    def regenerate(self, prevThreshold):
        self.nPrime += prevThreshold
        self.b += 1
        return self.generate()