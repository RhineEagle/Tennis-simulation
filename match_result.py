import pymssql
import pandas as pd
import random
import numpy as np
import copy
import os
from tqdm import trange

class player(object):
    def __init__(self,name,ace,fin,fser,df,sser,bs,aace,fret,sret,bc,elo):
        self.name=name
        self.ace=ace
        self.firstin=fin
        self.firstserve=fser
        self.doublefault=df
        self.secondserve=sser
        self.breaksave=bs
        self.aace = aace
        self.firstreturn=fret
        self.secondreturn=sret
        self.breakconvert=bc
        self.elo=elo

def stochastic(x):
    if x==1:
        return 0.03
    elif x==2:
        return -0.01
    elif x==3:
        return -0.02
    elif x==4:
        return -0.04
    elif x==5:
        return 0

def game(player1,player2,g1,g2,order,num):
    p1=0
    p2=0
    if g1==6 and g2==6:
        i=1
        while max(p1,p2)<=6 or abs(p1-p2)<2:
            if int(i/2)%2==1:
                list=playseven(player1,player2,p1,p2,i)
                p1=list[0]
                p2=list[1]
                i=list[2]
            else:
                list = playseven(player2, player1, p2, p1, i)
                p2 = list[0]
                p1 = list[1]
                i = list[2]
        #print(p1," ",p2)
        if p1>p2:
            g1=7
        else:
            g2=7
    else:
        while max(p1,p2)<4 or abs(p1-p2)<2:
            if(order>0):
                list=play(player1,player2,g1,g2,p1,p2,num)
                p1=list[0]
                p2=list[1]
            else:
                list=play(player2,player1,g2,g1,p2,p1,num)
                p2 = list[0]
                p1 = list[1]
        if p1>p2:
            g1=g1+1
        else:
            g2=g2+1
    return [g1,g2,p1,p2]

def play(player1,player2,g1,g2,p1,p2,num):
    p=random.random()
    weigh=player1.elo/(player1.elo+player2.elo)
    if (p2==3 and p1<=2) or (p2>=4 and p2-p1==1):
        #prob=player1.breaksave*(100-player2.breakconvert)/(player1.breaksave*(100-player2.breakconvert)+(100-player1.breaksave)*player2.breakconvert)
        prob = max(player1.breaksave/100,1-player2.breakconvert/100)*weigh+min(player1.breaksave/100,1-player2.breakconvert/100)*(1-weigh)
        if p>prob:
            p2=p2+1
            #print(g1, " ", g2," " , player2.name,p1,"break!")
        else:
            p1=p1+1
            #print(g1," ",g2,player1.name,"save!")
    else:
        real_ace = weigh * max(player1.ace / 100, player2.aace / 100) + (1 - weigh) * min(player1.ace / 100,
                                                                                          player2.aace / 100)
        if real_ace > 2.5 * player1.ace / 100 or real_ace-player1.ace/100>=0.035:
            real_ace = min(2.5 * player1.ace / 100, player1.ace/100+0.035)
        if real_ace <= 0.7 * player1.ace / 100 or real_ace-player1.ace/100<=-0.045:
            real_ace = max(0.7 * player1.ace / 100, player1.ace/100-0.045)
        if p<=real_ace+random.uniform(stochastic(num)-0.01,stochastic(num)+0.01):
        #if p <= player1.ace / 100:
            p1=p1+1
            #print(g1, " ", g2, " ", player1.name, p1, "ace!")
        else:
            if p>player1.firstin/100+random.uniform(stochastic(num)-0.03,stochastic(num)+0.03):
            #if p > player1.firstin / 100:
                if p>1-player1.doublefault/100:
                    p2=p2+1
                    #print(g1, " ", g2," " , player1.name,p1,"df!")
                else:
                    pr2=random.random()
                    #prob=player1.secondserve*(100-player2.secondreturn)/(player1.secondserve*(100-player2.secondreturn)+(100-player1.secondserve)*player2.secondreturn)
                    prob=max(player1.secondserve/100,1-player2.secondreturn/100)*weigh+min(player1.secondserve/100,1-player2.secondreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.02,stochastic(num)+0.02)
                    #prob = player1.secondserve / 100 * weigh + (1 - player2.secondreturn / 100) * (1 - weigh)
                    #print(player1.name,prob)
                    if pr2>prob:
                        p2=p2+1
                    else:
                        p1=p1+1
            else:
                pr1=random.random()
                #prob=player1.firstserve*(100-player1.firstreturn)/(player1.firstserve*(100-player2.firstreturn)+(100-player1.firstserve)*player2.firstreturn)
                prob=max(player1.firstserve/100,1-player2.firstreturn/100)*weigh+min(player1.firstserve/100,1-player2.firstreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.02,stochastic(num)+0.02)
                #prob = player1.firstserve / 100 * weigh + (1 - player2.firstreturn / 100) * (1 - weigh)
                if pr1>prob:
                    p2=p2+1
                else:
                    p1=p1+1
    return [p1,p2,g1,g2]

def playseven(player1,player2,p1,p2,i):
    weigh = player1.elo / (player1.elo + player2.elo)
    p=random.random()
    real_ace=0.5*max(player1.ace/100,player2.aace/100)+0.5*min(player1.ace/100,player2.aace/100)
    if real_ace > 2.5 * player1.ace / 100 or real_ace - player1.ace / 100 >= 0.035:
        real_ace = min(2.5 * player1.ace / 100, player1.ace / 100 + 0.035)
    if real_ace <= 0.7 * player1.ace / 100 or real_ace - player1.ace / 100 <= -0.045:
        real_ace = max(0.7 * player1.ace / 100, player1.ace / 100 - 0.045)
    if p <= real_ace:
        p1 = p1 + 1
    else:
        if p > player1.firstin/100:
            if p > 1 - player1.doublefault / 100:
                p2 = p2 + 1
            else:
                pr2 = random.random()
                prob = max(player1.secondserve / 100,1-player2.secondreturn/100) * weigh + min(player1.secondserve / 100,1-player2.secondreturn/100) * (1 - weigh)
                if pr2 > prob:
                    p2 = p2 + 1
                else:
                    p1 = p1 + 1
        else:
            pr1 = random.random()
            prob=max(player1.firstserve/100,1-player2.firstreturn/100)*weigh+min(player1.firstserve/100,1-player2.firstreturn/100)*(1-weigh)
            if pr1 > prob:
                p2 = p2 + 1
            else:
                p1 = p1 + 1
    i=i+1
    return [p1,p2,i]

def change(player,var):
    #print_obj(player)

    player.ace=player.ace+np.random.normal(loc =0.0 , scale= var[0])
    player.doublefault = player.doublefault + np.random.normal(loc=0.0, scale=var[1])
    player.firstin=player.firstin+np.random.normal(loc=0.0, scale=var[2])
    player.firstserve=player.firstserve+np.random.normal(loc=0.0, scale=var[3])
    player.secondserve=player.secondserve+np.random.normal(loc=0.0, scale=var[4])
    player.breaksave=player.breaksave+np.random.uniform(low=-15,high=15, size=1)
    player.firstreturn=player.firstreturn+np.random.normal(loc=0.0, scale=var[8])
    player.secondreturn=player.secondreturn+np.random.normal(loc=0.0, scale=var[9])
    player.breakconvert=player.breakconvert+np.random.uniform(low=-15,high=15,size=1)

    return player

def playset(player1,player2,var1,var2,setmode):
    setpoint1 = 0
    setpoint2 = 0
    order = 1
    player11=copy.deepcopy(player1)
    player22=copy.deepcopy(player2)
    player11=change(player11,var1)
    #print(player1==player11)
    player22=change(player22, var2)
    # print_obj(player11)
    # print_obj(player22)
    lengame = 0
    while setpoint1 != setmode and setpoint2 != setmode:
        gamepoint1 = 0
        gamepoint2 = 0

        while max(gamepoint1, gamepoint2) < 6 or (
                max(gamepoint1, gamepoint2) == 6 and min(gamepoint1, gamepoint2) >= 5):
            list = game(player11, player22, gamepoint1, gamepoint2, order, setpoint1 + setpoint2 + 1)
            gamepoint1 = list[0]
            gamepoint2 = list[1]
            order = -1 * order

        if gamepoint1 > gamepoint2:
            setpoint1 = setpoint1 + 1
        else:
            setpoint2 = setpoint2 + 1
        lengame=lengame+gamepoint1-gamepoint2
    #     if (gamepoint1 == 6 and gamepoint2 == 7) or (gamepoint2 == 6 and gamepoint1 == 7):
    #         print(gamepoint1, "vs", gamepoint2,"(",min(list[2],list[3]),")")
    #     else:
    #         print(gamepoint1, "vs", gamepoint2)
    #
    # print(setpoint1,":",setpoint2)
    return [setpoint1,setpoint2,lengame]

def print_obj(obj):
    num=0
    str=[]
    for item in obj.__dict__.items():
        if num==0:
            str.append('%s:%s' % item)
        else:
            str.append('%s:%.3f' % item)
        num=num+1
        if num==11:
            break
    print (str)

def match(playername1,playername2,playerid1,playerid2,stats1,stats2,var1,var2,elo1,elo2,setmode,N):
    if playerid2 == "-1" or playerid1 == "-1":
        exit(1)

    player1 = player(playername1, stats1[0], stats1[2], stats1[3], stats1[1], stats1[4], stats1[5], stats1[6], stats1[8],
                     stats1[9], stats1[10], elo1)
    print_obj(player1)
    player2 = player(playername2, stats2[0], stats2[2], stats2[3], stats2[1], stats2[4], stats2[5], stats2[6], stats2[8],
                     stats2[9],
                     stats2[10], elo2)
    print_obj(player2)

    list1 = []
    list2 = []
    list3 = []
    print("start to simulate... please wait for a while")
    for _ in trange(0, N):
        list = playset(player1, player2, var1, var2, setmode)
        list1.append(list[0])
        list2.append(list[1])
        list3.append(list[2])

    if setmode==2:
        sum20 = 0
        sum21 = 0
        sum12 = 0
        sum02 = 0
        for i in range(N):
            if list1[i] == 2 and list2[i] == 0:
                sum20 += 1
            elif list1[i] == 2 and list2[i] == 1:
                sum21 += 1
            elif list1[i] == 1 and list2[i] == 2:
                sum12 += 1
            else:
                sum02 += 1

        return np.array([sum20, sum21, sum12, sum02])

    else:
        sum30 = 0
        sum31 = 0
        sum32 = 0
        sum23 = 0
        sum13 = 0
        sum03 = 0

        for i in range(N):
            if list1[i] == 3 and list2[i] == 0:
                sum30 += 1
            elif list1[i] == 3 and list2[i] == 1:
                sum31 += 1
            elif list1[i] == 3 and list2[i] == 2:
                sum32 += 1
            elif list1[i] == 2 and list2[i] == 3:
                sum23 += 1
            elif list1[i] == 1 and list2[i] == 3:
                sum13 += 1
            else:
                sum03 += 1

        return np.array([sum30,sum31,sum32,sum23,sum13,sum03])

    # lenlist=pd.DataFrame(list3)
    # lenlist[1]=1
    # len=lenlist.groupby(0).count()/N
    # print(len)

def printresult(player1,player2,list,N):
    if len(list)==4:
        print(player1, "2:0", player2, list[0] / N)
        print(player1, "2:1", player2, list[1] / N)
        print(player1, "1:2", player2, list[2] / N)
        print(player1, "0:2", player2, list[3] / N)
    else:
        print(player1, "3:0", player2, list[0] / N)
        print(player1, "3:1", player2, list[1] / N)
        print(player1, "3:2", player2, list[2] / N)
        print(player1, "2:3", player2, list[3] / N)
        print(player1, "1:3", player2, list[4] / N)
        print(player1, "0:3", player2, list[5] / N)


def simulation(name1,name2,elo1,elo2,speed1,speed2,type,N,s1,s2,time1,time2,setmode):
    connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='tennis')
    cursor = connect.cursor()
    lan1 = "select top 1 ID from player where Name Like '%" + name1 + "%'"
    cursor.execute(lan1)
    id1 = cursor.fetchone()[0]
    lan2 = "select top 1 ID from player where Name Like '%" + name2 + "%'"
    cursor.execute(lan2)
    id2 = cursor.fetchone()[0]

    if s1=='t':
        cursor.execute("select * from dbo.player_statistics(%s,%s,%s,%s)", (id1, type, time1, time2))
    else:
        cursor.execute("select * from dbo.player_fastcourt_statistics(%s,%s,%s,%s,%s)",(id1,speed1,speed2,time1,time2))
    mean_stat1 = cursor.fetchone()

    if s2 == 't':
        cursor.execute("select * from dbo.player_statistics(%s,%s,%s,%s)", (id2, type, time1, time2))
    else:
        cursor.execute("select * from dbo.player_fastcourt_statistics(%s,%s,%s,%s,%s)",(id2,speed1,speed2,time1,time2))
    mean_stat2 = cursor.fetchone()

    if s1 == 't':
        cursor.execute("select * from dbo.player_statistics_single(%s,%s,%s,%s)", (id1, type, time1, time2))
    else:
        cursor.execute("select * from dbo.player_fastcourt_single(%s,%s,%s,%s,%s)",(id1,speed1,speed2,time1,time2))
    row = cursor.fetchone()
    stats_1 = []
    while row:
        stats_1.append(row)
        row = cursor.fetchone()
    temp_1 = np.zeros((len(stats_1), 11), dtype=float)
    for i in range(len(stats_1)):
        for j in range(11):
            temp_1[i][j] = stats_1[i][j]

    if s2 == 't':
        cursor.execute("select * from dbo.player_statistics_single(%s,%s,%s,%s)", (id2, type, time1, time2))
    else:
        cursor.execute("select * from dbo.player_fastcourt_single(%s,%s,%s,%s,%s)",(id2,speed1,speed2,time1,time2))
    row = cursor.fetchone()
    stats_2 = []
    while row:
        stats_2.append(row)
        row = cursor.fetchone()
    temp_2 = np.zeros((len(stats_2), 11), dtype=float)
    for i in range(len(stats_2)):
        for j in range(11):
            temp_2[i][j] = stats_2[i][j]

    print(len(stats_1), len(stats_2))
    if (len(stats_1)<=5 and len(stats_2)>=7) or (len(stats_2)<=5 and len(stats_1)>=7):
        flag=-1
    elif len(stats_1)<3 or len(stats_2)<3:
        if s1=='t' or (s1!='t' and (len(stats_1)==1 or len(stats_2)==1)):
            connect.close()
            return -2, []
        else:
            flag=0
    else:
        flag=0

    sigma_1 = []
    for i in range(11):
        sigma_1.append(pd.DataFrame(temp_1[:, i]).std(ddof=0))
    sigma_2 = []
    for i in range(11):
        sigma_2.append(pd.DataFrame(temp_2[:, i]).std(ddof=0))
    # print(sigma_1,sigma_2)

    resultlist=match(name1, name2, id1, id2, mean_stat1, mean_stat2, sigma_1, sigma_2, elo1, elo2, setmode, N)
    connect.close()
    return flag,resultlist

def courtspeed(speed):
    if speed=='FAST':
        return 80,100
    elif speed=='Fast':
        return 65,85
    elif speed=='Medium Fast':
        return 50,65
    elif speed=='Medium Slow':
        return 35,50
    elif speed=='Slow':
        return 0,40
    else:
        return 0,100

def start():
    name1 = input("Input player's name: ")
    name2 = input("Input player's name: ")
    elo1 = 2000
    elo2 = 2000
    type = ''
    setmode=2
    s = input('Player1 use what type of statistics: type/speed ? ')
    if s == 't':
        type = input('Input court type: Grass/Hard/Clay ')
    time1 = input('Use statistics starting from when ? ')
    time2 = input('Use statistics ending in when ? ')
    speed = input('Input court speed: FAST/Fast/Medium Fast/Medium Slow/Slow ')
    speed1,speed2 = courtspeed(speed)
    N = int(input('How many times to simulate ? '))
    flag, resultlist = simulation(name1, name2, elo1, elo2, speed1, speed2, type, N, s, s,time1, time2, setmode)
    if flag==-1:
        flag, resultlist_add = simulation(name1, name2, elo1, elo2, speed1, speed2, type, N, 's', 's', time1, time2,setmode)
        resultlist = resultlist+resultlist_add
        printresult(name1,name2,resultlist,2*N)
    elif flag==-2:
        flag, resultlist = simulation(name1, name2, elo1, elo2, speed1, speed2, type, N, 's', 's', time1, time2,setmode)
        if flag==-2:
            print("Satistics less than limitation. ")
        else:
            printresult(name1,name2,resultlist,N)
    else:
        printresult(name1,name2,resultlist,N)

if __name__ == '__main__':
    q='N'
    while q!='q':
        start()
        q = input('quit by entering q ')
        i = os.system("cls")