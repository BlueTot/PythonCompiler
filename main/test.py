import timeit

def function():
    N = 1000
    prime = [None] * 1001
    for i in range(0, N+1, 1):
        prime[i] = 1
    for p in range(2, N+1, 1):
        if prime[p] == 1:
            for j in range(p*p, N+1, p):
                prime[j] = 0
    sum = 0
    for p in range(2, N+1, 1):
        if prime[p] == 1:
            sum += 1
    # print(sum)

N = 100000
print(timeit.Timer(function).timeit(number=N)/N)