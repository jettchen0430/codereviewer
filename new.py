[0,1,1,2,3]

def fbi(n):
    arr = []
    arr.append(0)
    arr.append(1)
    for i in range(2,n):
        arr.append(arr[i-1]+ arr[i-2])
    return arr[-1]


print(fbi(5))