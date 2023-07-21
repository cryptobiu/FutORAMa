import random
import string


def flatten(l):
    return [item for sublist in l for item in sublist]

def get_random_string(length, BALL_STATUS_POSITION=None, status=None):
    # With combination of lower and upper case
    result_str = ''.join(random.choice(string.printable) for i in range(length))
    if status is not None:
        result = bytes(result_str,'utf-8')
        return result[:BALL_STATUS_POSITION] + status + result[1 + BALL_STATUS_POSITION:]
        
    # return random string
    return bytes(result_str,'utf-8')
