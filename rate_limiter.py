import time

def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate

@RateLimited(.5)  # 2 per second at most
def PrintNumber(num):
    print(num)

@RateLimited(.5)  # 2 per second at most
def PrintNumber2(num):
    print('again: ' + str(num))

if __name__ == "__main__":
    print("This should print 1,2,3... at about 2 per second.")
    for i in range(1,100):
        PrintNumber(i)
        PrintNumber2(i)
        PrintNumber2(i)
