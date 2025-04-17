

import sys 

def cal_ticket():
    data ="""
    3
    3 300 100
    36 96 6
    73 176 22
    """
    data = data.strip().split("\n")
    for i in range(1,int(data[0])):
        count = 0
        data[i] = data[i].strip().split(' ')
        if int(data[i][2]) % 2 == 0:
            zero_ticket = int(data[i][2]) // 2 - 1
            one_ticket = int(data[i][2]) *1.5 -1
        else:
            zero_ticket = int(data[i][2]) // 2 
            one_ticket = int(int(data[i][2]) *1.5)
        res = int(data[i][1]) - zero_ticket * int(data[i][0])
        count += int(data[i][0])
        if res <= 0 :
            print("0") 
        else:
            if res%(one_ticket-zero_ticket) != 0:
                count = res // (one_ticket-zero_ticket) + 1
            else:
                count = res // (one_ticket-zero_ticket)

            print(count)

if __name__ == "__main__":
    cal_ticket()






