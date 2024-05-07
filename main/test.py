import timeit

def function():
    sum = 0
    for i in range(31):
        sum += i

N = 1000000
print(timeit.Timer(function).timeit(number=N)/N)