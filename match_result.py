import pymssql
import pandas as pd
import random
import numpy as np
import copy

class player(object):
    def __init__(self,name,ace,fin,fser,df,sser,bs,fret,sret,bc,elo):
        self.name=name
        self.ace=ace
        self.firstin=fin
        self.firstserve=fser
        self.doublefault=df
        self.secondserve=sser
        self.breaksave=bs
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
    weigh=(player1.elo-1600)/(player1.elo+player2.elo-3200)
    if (p2==3 and p1<=2) or (p2>=4 and p2-p1==1):
        #prob=player1.breaksave*(100-player2.breakconvert)/(player1.breaksave*(100-player2.breakconvert)+(100-player1.breaksave)*player2.breakconvert)
        prob = player1.breaksave/100*weigh+(1-player2.breakconvert/100)*(1-weigh)
        if p>prob:
            p2=p2+1
            #print(g1, " ", g2," " , player2.name,p1,"break!")
        else:
            p1=p1+1
            #print(g1," ",g2,player1.name,"save!")
    else:
        if p<=player1.ace/100+random.uniform(stochastic(num)-0.01,stochastic(num)+0.01):
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
                    prob=player1.secondserve/100*weigh+(1-player2.secondreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.02,stochastic(num)+0.02)
                    #prob = player1.secondserve / 100 * weigh + (1 - player2.secondreturn / 100) * (1 - weigh)
                    #print(player1.name,prob)
                    if pr2>prob:
                        p2=p2+1
                    else:
                        p1=p1+1
            else:
                pr1=random.random()
                #prob=player1.firstserve*(100-player1.firstreturn)/(player1.firstserve*(100-player2.firstreturn)+(100-player1.firstserve)*player2.firstreturn)
                prob=player1.firstserve/100*weigh+(1-player2.firstreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.02,stochastic(num)+0.02)
                #prob = player1.firstserve / 100 * weigh + (1 - player2.firstreturn / 100) * (1 - weigh)
                if pr1>prob:
                    p2=p2+1
                else:
                    p1=p1+1
    return [p1,p2,g1,g2]

def playseven(player1,player2,p1,p2,i):
    weigh = (player1.elo - 1600) / (player1.elo + player2.elo - 3200)
    p=random.random()
    if p <= player1.ace / 100:
        p1 = p1 + 1
    else:
        if p > player1.firstin/100:
            if p > 1 - player1.doublefault / 100:
                p2 = p2 + 1
            else:
                pr2 = random.random()
                prob = player1.secondserve / 100 * weigh + (1-player2.secondreturn/100) * (1 - weigh)
                if pr2 > prob:
                    p2 = p2 + 1
                else:
                    p1 = p1 + 1
        else:
            pr1 = random.random()
            prob=player1.firstserve/100*weigh+(1-player2.firstreturn/100)*(1-weigh)
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
    print (['%s:%s' % item for item in obj.__dict__.items()])

def match(playername1,playername2,playerid1,playerid2,stats1,stats2,var1,var2,elo1,elo2,setmode,N):
    if playerid2 == "-1" or playerid1 == "-1":
        exit(1)

    player1 = player(playername1, stats1[0], stats1[2], stats1[3], stats1[1], stats1[4], stats1[5], stats1[8],
                     stats1[9], stats1[10], elo1)
    print_obj(player1)
    player2 = player(playername2, stats2[0], stats2[2], stats2[3], stats2[1], stats2[4], stats2[5], stats2[8],
                     stats2[9],
                     stats2[10], elo2)
    print_obj(player2)

    list1 = []
    list2 = []
    list3 = []
    print("start to simulate...")
    for i in range(0, N):
        list = playset(player1, player2, var1, var2, setmode)
        list1.append(list[0])
        list2.append(list[1])
        list3.append(list[2])

    if setmode==2:
        sum20 = 0
        sum21 = 0
        sum12 = 0
        sum02 = 0
        for i in range(0, N):
            if list1[i] == 2 and list2[i] == 0:
                sum20 += 1
            elif list1[i] == 2 and list2[i] == 1:
                sum21 += 1
            elif list1[i] == 1 and list2[i] == 2:
                sum12 += 1
            else:
                sum02 += 1

        print(player1.name, "2:0", player2.name, sum20 / N)
        print(player1.name, "2:1", player2.name, sum21 / N)
        print(player1.name, "1:2", player2.name, sum12 / N)
        print(player1.name, "0:2", player2.name, sum02 / N)

    else:
        sum30 = 0
        sum31 = 0
        sum32 = 0
        sum23 = 0
        sum13 = 0
        sum03 = 0

        for i in range(0, N):
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

        print(player1.name,"3:0",player2.name, sum30 / N)
        print(player1.name,"3:1",player2.name, sum31 / N)
        print(player1.name,"3:2",player2.name, sum32 / N)
        print(player1.name,"2:3",player2.name, sum23 / N)
        print(player1.name,"1:3",player2.name, sum13 / N)
        print(player1.name,"0:3",player2.name, sum03 / N)

    lenlist=pd.DataFrame(list3)
    lenlist[1]=1
    len=lenlist.groupby(0).count()/N
    print(len)


name1="Rune"
name2="Ruud"
elo1=1975
elo2=2153
seq1=0
seq2=0

connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='tennis')
cursor = connect.cursor()
cursor.execute("select top 1 ID from player where Name Like '%Rune%'")
id1=cursor.fetchone()[0]
cursor.execute("select top 1 ID from player where Name Like '%Ruud%'")
id2=cursor.fetchone()[0]

cursor.execute("select * from dbo.player_statistics(%s,%s,%s)",(id1,'Clay',seq1))
mean_stat1=cursor.fetchone()
cursor.execute("select * from dbo.player_statistics(%s,%s,%s)",(id2,'Clay',seq2))
mean_stat2=cursor.fetchone()

cursor.execute("select * from dbo.player_statistics_single(%s,%s,%s)",(id1,'Clay',seq1))
row=cursor.fetchone()
stats_1=[]
while row:
    stats_1.append(row)
    row=cursor.fetchone()
temp_1 = np.zeros((len(stats_1), 11), dtype=float)
for i in range(len(stats_1)):
    for j in range(11):
        temp_1[i][j]=stats_1[i][j]
cursor.execute("select * from dbo.player_statistics_single(%s,%s,%s)",(id2,'Clay',seq2))
row=cursor.fetchone()
stats_2=[]
while row:
    stats_2.append(row)
    row=cursor.fetchone()
temp_2 = np.zeros((len(stats_2), 11), dtype=float)
for i in range(len(stats_2)):
    for j in range(11):
        temp_2[i][j]=stats_2[i][j]
sigma_1=[]
for i in range(11):
    sigma_1.append(pd.DataFrame(temp_1[:, i]).std(ddof=0))
sigma_2=[]
for i in range(11):
    sigma_2.append(pd.DataFrame(temp_2[:, i]).std(ddof=0))
# print(sigma_1,sigma_2)

match(name1,name2,id1,id2,mean_stat1,mean_stat2,sigma_1,sigma_2,elo1,elo2,3,10000)
connect.close()
