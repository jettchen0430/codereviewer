import sys


# data = sys.stdin.read().strip().split("\n")
def luckyor():
    data = """
    2
    10
    1111111110
    10
    1000000001
    """
    data = data.strip().split("\n")
    sets = int(data[0])
    for i in range(1,2*sets+1,2):
        length = int(data[i])
        judge(i,data,length)

def judge(i,data,length):
    count = 0
    flag = 0
    for j in range(length):
        data[i+1] = data[i+1].strip()
        if data [i+1][j] == "1":
            count += 1
            if count == 9:
                flag += 1
            if count > 9 :
                flag = 0
                break
        else:
            count = 0
    if flag == 1:
        print("lucky")
    else:
        print("unlucky")

if __name__ == "__main__":
    luckyor()



