import pymssql
import pandas as pd
import random
import numpy as np
import copy
import os
import scipy.stats as stats
from tqdm import trange

class player(object):

    def __init__(self, name, ace, fin, fser, df, sser, bs, aace, fret, sret, bc, elo):
        self.name = name
        self.ace = ace
        self.firstin = fin
        self.firstserve = fser
        self.doublefault = df
        self.secondserve = sser
        self.breaksave = bs
        self.aace = aace
        self.firstreturn = fret
        self.secondreturn = sret
        self.breakconvert = bc
        self.elo = elo

def stochastic(x):

    if x == 1:
        return 0.03
    elif x == 2:
        return -0.01
    elif x == 3:
        return -0.02
    elif x == 4:
        return -0.04
    elif x == 5:
        return 0

def game(player1, player2, g1, g2, order, num):
    p1 = 0
    p2 = 0
    if g1 == 6 and g2 == 6:
        i = 1
        while max(p1, p2) <= 6 or abs(p1-p2) < 2:
            if int(i/2) % 2 == 1:
                list = playseven(player1, player2, p1, p2, i)
                p1 = list[0]
                p2 = list[1]
                i = list[2]
            else:
                list = playseven(player2, player1, p2, p1, i)
                p2 = list[0]
                p1 = list[1]
                i = list[2]
        #print(p1," ",p2)
        if p1 > p2:
            g1 = 7
        else:
            g2 = 7
    else:
        while max(p1, p2) < 4 or abs(p1-p2) < 2:
            if (order > 0):
                list = play(player1, player2, g1, g2, p1, p2, num)
                p1 = list[0]
                p2 = list[1]
            else:
                list = play(player2, player1, g2, g1, p2, p1, num)
                p2 = list[0]
                p1 = list[1]
        if p1 > p2:
            g1 = g1+1
        else:
            g2 = g2+1
    return [g1, g2, p1, p2]

def play(player1, player2, g1, g2, p1, p2, num):
    p = random.random()
    weigh = player1.elo/(player1.elo+player2.elo)
    if (p2 == 3 and p1 <= 2) or (p2 >= 4 and p2-p1 == 1):
        #prob=player1.breaksave*(100-player2.breakconvert)/(player1.breaksave*(100-player2.breakconvert)+(100-player1.breaksave)*player2.breakconvert)
        prob = max(player1.breaksave/100, 1-player2.breakconvert/100)*weigh+min(player1.breaksave/100, 1-player2.breakconvert/100)*(1-weigh)
        #print("break point for ", player2.name)
        if p > prob:
            p2 = p2+1
            #print(g1, " ", g2," " , player2.name,p1,"break!")
        else:
            p1 = p1+1
            #print(g1," ",g2,player1.name,"save!")
    else:
        if p <= player1.ace/100+random.uniform(stochastic(num)-0.01, stochastic(num)+0.01):
        #if p <= player1.ace / 100:
            p1 = p1+1
            #print(g1, " ", g2, " ", player1.name, p1, "ace!")
        else:
            if p > player1.firstin/100+random.uniform(stochastic(num)-0.03, stochastic(num)+0.03):
            #if p > player1.firstin / 100:
                if p > 1-player1.doublefault/100:
                    p2 = p2+1
                    #print(g1, " ", g2," " , player1.name,p1,"df!")
                else:
                    pr2 = random.random()
                    #prob=player1.secondserve*(100-player2.secondreturn)/(player1.secondserve*(100-player2.secondreturn)+(100-player1.secondserve)*player2.secondreturn)
                    #prob = max(player1.secondserve/100,1-player2.secondreturn/100)*weigh+min(player1.secondserve/100,1-player2.secondreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.02,stochastic(num)+0.02)
                    prob = player1.secondserve / 100 + random.uniform(stochastic(num)-0.02,stochastic(num)+0.02)
                    #prob = player1.secondserve / 100 * weigh + (1 - player2.secondreturn / 100) * (1 - weigh)
                    #print(player1.name,prob)
                    if pr2 > prob:
                        p2 = p2+1
                    else:
                        p1 = p1+1
            else:
                pr1 = random.random()
                #prob=player1.firstserve*(100-player1.firstreturn)/(player1.firstserve*(100-player2.firstreturn)+(100-player1.firstserve)*player2.firstreturn)
                #prob = max(player1.firstserve/100,1-player2.firstreturn/100)*weigh+min(player1.firstserve/100,1-player2.firstreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.02,stochastic(num)+0.02)
                prob = player1.firstserve / 100 + random.uniform(stochastic(num)-0.02,stochastic(num)+0.02)
                #prob = player1.firstserve / 100 * weigh + (1 - player2.firstreturn / 100) * (1 - weigh)
                if pr1 > prob:
                    p2 = p2+1
                else:
                    p1 = p1+1
    return [p1, p2, g1, g2]

def playseven(player1, player2, p1, p2, i):
    weigh = player1.elo / (player1.elo + player2.elo)
    p = random.random()
    if p <= player1.ace/100:
        p1 = p1 + 1
    else:
        if p > player1.firstin/100:
            if p > 1 - player1.doublefault / 100:
                p2 = p2 + 1
            else:
                pr2 = random.random()
                #prob = max(player1.secondserve / 100,1-player2.secondreturn/100) * weigh + min(player1.secondserve / 100,1-player2.secondreturn/100) * (1 - weigh)
                prob = player1.secondserve / 100
                if pr2 > prob:
                    p2 = p2 + 1
                else:
                    p1 = p1 + 1
        else:
            pr1 = random.random()
            #prob = max(player1.firstserve/100,1-player2.firstreturn/100)*weigh+min(player1.firstserve/100,1-player2.firstreturn/100)*(1-weigh)
            prob = player1.firstserve / 100
            if pr1 > prob:
                p2 = p2 + 1
            else:
                p1 = p1 + 1
    i=i+1
    return [p1,p2,i]

def ace_relationfit(p1, p2, var, mv, r, type):
    if type == 'Grass' or 'Hard':
        list = [3,6,15]
    elif type == 'Clay':
        list = [3,5,10]
    else:
        list = [3,6,13]
    real_ace = p1
    if p1 <= list[0]:
        real_ace = real_ace+np.random.normal(loc=0.0, scale=var)
    elif p1 <= list[1]:
        if r > 0:
            rand = random.random()
            standard = r*0.15+0.5
            rand_var = np.random.normal(loc=0.0,scale=var)
            if rand <= standard:
                if p2 >= mv+2.5:
                    rand_var=abs(rand_var)
                elif p2<=mv-2.5:
                    rand_var=-abs(rand_var)
        else:
            rand_var=np.random.normal(loc=0.0,scale=var)
        real_ace=real_ace * 0.7 + p2 * 0.3 + rand_var * 0.7
    elif p1<=list[2]:
        if r>0:
            rand=random.random()
            standard = r * 0.17 + 0.5
            rand_var = abs(np.random.normal(loc=0.0, scale=var))
            if rand <= standard:
                if p2 >= mv+2.5:
                    rand_var = abs(rand_var)
                elif p2 <= mv-2.5:
                    rand_var = -abs(rand_var)
            else:
                rand_var = np.random.normal(loc=0.0, scale=var)
        else:
            rand_var = np.random.normal(loc=0.0, scale=var)
        real_ace = real_ace * 0.6 + p2 * 0.4 + rand_var * 0.6
    else:
        rand_var = np.random.normal(loc=0.0, scale=var)
        if r>0:
            rand=random.random()
            standard = r * 0.2 + 0.5
            if rand <= standard:
                if p2 > mv + 2.5:
                    rand_var = abs(rand_var)
                elif p2 < mv - 2.5:
                    rand_var = -abs(rand_var)
        real_ace = real_ace * 0.7 + p2 * 0.3 + rand_var * 0.7
        #print(real_ace)
    return real_ace

def firserve_relationfit(p1,p2,var,mv,r):
    list = [58, 72]
    real_ser = p1
    if p1 <= list[0]:
        real_ser = real_ser + np.random.normal(loc=0.0, scale=var)
    elif p1 <= list[1]:
        if r > 0:
            rand = random.random()
            standard = r * 0.2 + 0.5
            rand_var = np.random.normal(loc=0.0, scale=var)
            if rand <= standard:
                if p2 >= mv + 3.5:
                    rand_var = -abs(rand_var)
                elif p2 <= mv - 3.5:
                    rand_var = abs(rand_var)
        else:
            rand_var = np.random.normal(loc=0.0, scale=var)
        real_ser = real_ser * 0.62 + (100-p2) * 0.38 + rand_var*0.62
    else:
        rand_var = np.random.normal(loc=0.0, scale=var)
        real_ser = real_ser * 0.68 + (100-p2) * 0.32 + rand_var*0.68

    return real_ser

def secserve_relationfit(p1,p2,var,mv,r):
    list = [48, 64]
    real_ser = p1
    if p1 <= list[0]:
        real_ser = real_ser + np.random.normal(loc=0.0, scale=var)
    elif p1 <= list[1]:
        if r > 0:
            rand = random.random()
            standard = r * 0.23 + 0.5
            rand_var = np.random.normal(loc=0.0, scale=var)
            if rand <= standard:
                if p2 >= mv + 3.5:
                    rand_var = -abs(rand_var)
                elif p2 <= mv - 3.5:
                    rand_var = abs(rand_var)
        else:
            rand_var = np.random.normal(loc=0.0, scale=var)
        real_ser = real_ser * 0.55 + (100-p2) * 0.45 + rand_var*0.55
    else:
        rand_var = np.random.normal(loc=0.0, scale=var)
        real_ser = real_ser * 0.6 + (100-p2) * 0.4 + rand_var*0.6

    return real_ser

def change(player1,player2,var,mv,r,type):
    player1.ace=ace_relationfit(player1.ace,player2.aace,var[0],mv[0],r[0],type)
    #print(player1.name,player1.ace,mv,r)
    player1.doublefault = player1.doublefault + np.random.normal(loc=0.0, scale=var[1])
    player1.firstreturn = player1.firstreturn + np.random.normal(loc=0.0, scale=var[8])
    player1.secondreturn = player1.secondreturn + np.random.normal(loc=0.0, scale=var[9])
    player1.firstin = player1.firstin+np.random.normal(loc=0.0, scale=var[2])
    #player1.firstserve=player1.firstserve+np.random.normal(loc=0.0, scale=var[3])
    player1.firstserve = firserve_relationfit(player1.firstserve, player2.firstreturn, var[3], mv[1], r[1])
    #player1.secondserve = player1.secondserve + np.random.normal(loc=0.0, scale=var[4])
    player1.secondserve = secserve_relationfit(player1.secondserve,player2.secondreturn,var[4],mv[2],r[2])
    #print(player1.name,player1.secondserve,mv[1],r[1])
    player1.breaksave=player1.breaksave+np.random.uniform(low=-20,high=20, size=1)
    player1.breakconvert=player1.breakconvert+np.random.uniform(low=-20,high=20,size=1)
    # player1.breaksave=player1.breaksave+np.random.normal(loc=0.0, scale=var[5])
    # player1.breakconvert = player1.breakconvert + np.random.normal(loc=0.0, scale=var[10])
    # print_obj(player1)
    return player1

def playset(player1,player2,var1,var2,r1,r2,mv,type,setmode):
    setpoint1 = 0
    setpoint2 = 0
    order = 1
    player11=copy.deepcopy(player1)
    player22=copy.deepcopy(player2)
    player11=change(player11,player22,var1,mv[0:3],r1,type)
    # print(player1==player11)
    player22=change(player22,player11,var2,mv[3:6],r2,type)
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

def match(playername1,playername2,playerid1,playerid2,stats1,stats2,var1,var2,elo1,elo2,r1,r2,mv,type,setmode,N):
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
        list = playset(player1, player2, var1, var2, r1, r2, mv, type, setmode)
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


def simulation(cursor,name1,name2,elo1,elo2,speed1,speed2,type,N,s1,s2,time1,time2,time3,time4,qf,setmode):
    lan1 = "select top 1 ID from player where Name Like '%" + name1 + "%'"
    cursor.execute(lan1)
    id1 = cursor.fetchone()[0]
    lan2 = "select top 1 ID from player where Name Like '%" + name2 + "%'"
    cursor.execute(lan2)
    id2 = cursor.fetchone()[0]

    if s1=='t':
        cursor.execute("select * from dbo.player_statistics(%s,%s,%s,%s,%s)", (id1, type, time1, time2, qf))
    else:
        cursor.execute("select * from dbo.player_fastcourt_statistics(%s,%s,%s,%s,%s,%s,%s)",(id1,speed1,speed2,time1,time2,qf,type))
    mean_stat1 = cursor.fetchone()

    if s2 == 't':
        cursor.execute("select * from dbo.player_statistics(%s,%s,%s,%s,%s)", (id2, type, time3, time4, qf))
    else:
        cursor.execute("select * from dbo.player_fastcourt_statistics(%s,%s,%s,%s,%s,%s,%s)",(id2,speed1,speed2,time3,time4,qf,type))
    mean_stat2 = cursor.fetchone()

    if s1 == 't':
        cursor.execute("select * from dbo.player_statistics_single(%s,%s,%s,%s,%s)", (id1, type, time1, time2, qf))
    else:
        cursor.execute("select * from dbo.player_fastcourt_single(%s,%s,%s,%s,%s,%s,%s)",(id1,speed1,speed2,time1,time2,qf,type))
    row = cursor.fetchone()
    stats_1 = []
    lst_1=[]
    while row:
        stats_1.append(row)
        row = cursor.fetchone()
    temp_1 = np.zeros((len(stats_1), 11), dtype=float)
    for i in range(len(stats_1)):
        for j in range(11):
            temp_1[i][j] = stats_1[i][j]
        lst_1.append(stats_1[i][11])

    if s2 == 't':
        cursor.execute("select * from dbo.player_statistics_single(%s,%s,%s,%s,%s)", (id2, type, time3, time4, qf))
    else:
        cursor.execute("select * from dbo.player_fastcourt_single(%s,%s,%s,%s,%s,%s,%s)",(id2,speed1,speed2,time3,time4,qf,type))
    row = cursor.fetchone()
    stats_2 = []
    lst_2=[]
    while row:
        stats_2.append(row)
        row = cursor.fetchone()
    temp_2 = np.zeros((len(stats_2), 11), dtype=float)
    for i in range(len(stats_2)):
        for j in range(11):
            temp_2[i][j] = stats_2[i][j]
        lst_2.append(stats_2[i][11])

    print(len(stats_1), len(stats_2))
    if (len(stats_1)<5 and len(stats_2)>=7) or (len(stats_2)<5 and len(stats_1)>=7):
        if len(stats_1)==0 or len(stats_2)==0:
            return -2,[]
        else:
            flag=-1
    elif len(stats_1)<3 or len(stats_2)<3:
        if s1=='t' or (s1!='t' and (len(stats_1)==1 or len(stats_2)==1)):
            return -2, []
        else:
            if len(stats_1)==0 or len(stats_2)==0:
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

    relation_1=[]
    stats_31=[]
    stats_32=[]
    stats_33=[]

    if s1 == 't':
        for item in lst_1:
            cursor.execute("select a_ace,fir_ret,sec_ret from dbo.player_statistics(%s,%s,%s,%s,%s)", (item, type, min(202200,time1), time2, qf))
            row = cursor.fetchone()
            while row:
                stats_31.append(row[0])
                stats_32.append(row[1])
                stats_33.append(row[2])
                row = cursor.fetchone()
    else:
        for item in lst_1:
            cursor.execute("select a_ace,fir_ret,sec_ret from dbo.player_fastcourt_statistics(%s,%s,%s,%s,%s,%s,%s)", (item, speed1, speed2, min(202200,time1), time2, qf,type))
            row = cursor.fetchone()
            while row:
                stats_31.append(row[0])
                stats_32.append(row[1])
                stats_33.append(row[2])
                row = cursor.fetchone()
    temp_31 = np.zeros((len(stats_31), 1), dtype=float)
    temp_32 = np.zeros((len(stats_32), 1), dtype=float)
    temp_33 = np.zeros((len(stats_33), 1), dtype=float)

    for i in range(0,len(stats_31)):
        temp_31[i][0]=stats_31[i]
        temp_32[i][0]=100-stats_32[i]
        temp_33[i][0]=100-stats_33[i]

    if len(stats_1)>=3:
        relation1,p_val=stats.spearmanr(temp_1[:,0],temp_31[:,0])
        if p_val>=0.1:
            relation_1.append(0)
        else:
            relation_1.append(relation1)
        relation1, p_val = stats.spearmanr(temp_1[:, 3], temp_32[:, 0])
        if p_val >= 0.1:
            relation_1.append(0)
        else:
            relation_1.append(relation1)
        relation1, p_val = stats.spearmanr(temp_1[:, 4], temp_33[:, 0])
        if p_val >= 0.1:
            relation_1.append(0)
        else:
            relation_1.append(relation1)
    else:
        relation_1 = [0, 0, 0]

    relation_2 = []
    stats_41=[]
    stats_42=[]
    stats_43=[]
    if s1 == 't':
        for item in lst_2:
            cursor.execute("select a_ace,fir_ret,sec_ret from dbo.player_statistics(%s,%s,%s,%s,%s)", (item, type, min(202200,time3), time4, qf))
            row = cursor.fetchone()
            while row:
                stats_41.append(row[0])
                stats_42.append(row[1])
                stats_43.append(row[2])
                row = cursor.fetchone()
    else:
        for item in lst_2:
            cursor.execute("select a_ace,fir_ret,sec_ret from dbo.player_fastcourt_statistics(%s,%s,%s,%s,%s,%s,%s)", (item, speed1, speed2, min(202200,time3), time4, qf, type))
            row = cursor.fetchone()
            while row:
                stats_41.append(row[0])
                stats_42.append(row[1])
                stats_43.append(row[2])
                row = cursor.fetchone()
    temp_41 = np.zeros((len(stats_41), 1), dtype=float)
    temp_42 = np.zeros((len(stats_42), 1), dtype=float)
    temp_43 = np.zeros((len(stats_43), 1), dtype=float)
    for i in range(0,len(stats_41)):
        temp_41[i][0]=stats_41[i]
        temp_42[i][0]=100-stats_42[i]
        temp_43[i][0]=100-stats_43[i]

    if len(stats_2)>=3:
        relation2,p_val=stats.spearmanr(temp_2[:,0],temp_41[:,0])
        if p_val>=0.1:
            relation_2.append(0)
        else:
            relation_2.append(relation2)
        relation2, p_val = stats.spearmanr(temp_2[:, 3], temp_42[:, 0])
        if p_val >= 0.1:
            relation_2.append(0)
        else:
            relation_2.append(relation2)
        relation2, p_val = stats.spearmanr(temp_2[:, 4], temp_43[:, 0])
        if p_val >= 0.1:
            relation_2.append(0)
        else:
            relation_2.append(relation2)
    else:
        relation_2 = [0, 0, 0]

    mean_val=[np.mean(stats_31),np.mean(stats_32),np.mean(stats_33),np.mean(stats_41),np.mean(stats_42),np.mean(stats_43)]
    print(relation_1,relation_2,mean_val)
    # relation_1=[0,0,0]
    # relation_2=relation_1
    resultlist = match(name1, name2, id1, id2, mean_stat1, mean_stat2, sigma_1, sigma_2, elo1, elo2, relation_1, relation_2, mean_val, type, setmode, N)
    return flag, resultlist

def courtspeed(speed):
    if speed=='1' or speed=='FAST':
        return 80,100
    elif speed=='Fast' or speed=='2':
        return 65,85
    elif speed=='Medium Fast' or speed=='3':
        return 50,70
    elif speed=='Medium Slow' or speed=='4':
        return 35,50
    elif speed=='Slow' or speed=='5':
        return 0,40
    else:
        return 0,100

def outputprocess(cursor, name1, name2, elo1, elo2, speed1, speed2, type, N, s, time1, time2, time3, time4, time5, time6, qf, setmode):
    flag, resultlist = simulation(cursor, name1, name2, elo1, elo2, speed1, speed2, type, N, s, s, time1, time2, time3, time4,qf,
                                  setmode)
    if flag == -1:
        flag, resultlist_add = simulation(cursor, name1, name2, elo1, elo2, speed1, speed2, type, N, 's', 's', time5,
                                          time2, time6, time4, qf, setmode)
        if flag == -2:
            printresult(name1, name2, resultlist, N)
        else:
            resultlist = resultlist + resultlist_add
            printresult(name1, name2, resultlist, 2 * N)
    elif flag == -2:
        flag, resultlist = simulation(cursor, name1, name2, elo1, elo2, speed1, speed2, type, N, 's', 's', time1, time2,
                                      time3, time4, qf,setmode)
        if flag == -2:
            print("Satistics less than limitation. ")
        else:
            printresult(name1, name2, resultlist, N)
    else:
        wval = sum(resultlist[0:int(len(resultlist) / 2)]) / N
        printresult(name1, name2, resultlist, N)
        print("start to check by speed...")
        flag, resultlist_check = simulation(cursor, name1, name2, elo1, elo2, speed1, speed2, type, N, 's', 's', time5,
                                            time2, time6, time4, qf,
                                            setmode)
        if flag == -2:
            printresult(name1, name2, resultlist, N)
        else:
            w_val = sum(resultlist_check[0:int(len(resultlist_check) / 2)]) / N
            if (w_val - 0.5) * (wval - 0.5) < 0:
                print("check!")
                resultlist = resultlist + resultlist_check
                printresult(name1, name2, resultlist, 2 * N)
            else:
                print("have confidence.")


def start():
    name1 = input("Input player's name: ")
    name2 = input("Input player's name: ")
    elo1 = 20
    elo2 = 20
    qf = 0
    setmode = 2
    s = 't'
    type = input('Input court type: Grass/Hard/Clay ')
    speed = input('Input court speed: FAST/Fast/Medium Fast/Medium Slow/Slow ')
    speed1, speed2 = courtspeed(speed)

    connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='tennis')
    cursor = connect.cursor()
    cursor.execute("Exec select_match %s,%s", (name1, 0))
    row = cursor.fetchone()
    num = 0
    num_q = 0
    num_s = 0
    num_sq = 0
    tour_pure = []
    tour_s = []
    tour_sq = []
    tour_q = []
    while row and (num < 10 or num_s < 10):
        if row[3].rstrip() == type or type == 'All':
            num_q = num_q + 1
            if num_q == 10:
                tour_q = (row[0],row[1])
            if row[-1]>=speed1 and row[-1]<=speed2:
                num_sq = num_sq + 1
                if num_sq == 10:
                    tour_sq = (row[0],row[1])
            if row[2].rstrip() != 'Qualify':
                num = num + 1
                if num == 10:
                    tour_pure = (row[0], row[1])
                if row[-1] >= speed1 and row[-1] <= speed2:
                    num_s = num_s + 1
                    if num_s == 10:
                        tour_s = (row[0], row[1])
        row=cursor.fetchone()
    if num == 10:
        print(tour_pure[1], tour_q[1])
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s",(tour_pure[0],tour_pure[1]))
        seq_pure=cursor.fetchone()[0]
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s",(tour_q[0],tour_q[1]))
        seq_q=cursor.fetchone()[0]
        print("type", name1, seq_pure, seq_q)
    elif tour_q:
        print(tour_q[1])
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s", (tour_q[0], tour_q[1]))
        seq_q = cursor.fetchone()[0]
        print("type", name1, seq_q)
    if num_s >= 10:
        print(tour_s[1], tour_sq[1])
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s",
                       (tour_s[0], tour_s[1]))
        seq_pure = cursor.fetchone()[0]
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s", (tour_sq[0], tour_sq[1]))
        seq_q = cursor.fetchone()[0]
        print("speed", name1, seq_pure, seq_q)
    elif tour_sq:
        print(tour_sq[1])
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s", (tour_sq[0], tour_sq[1]))
        seq_q = cursor.fetchone()[0]
        print("speed", name1, seq_q)

    flag_1 = 0
    if num != num_q:
        flag_1 = 1

    cursor.execute("Exec select_match %s,%s", (name2, 0))
    row = cursor.fetchone()
    num = 0
    num_q = 0
    num_s = 0
    num_sq = 0
    tour_pure = []
    tour_s = []
    tour_sq = []
    tour_q = []
    while row and (num < 10 or num_s < 10):
        if row[3].rstrip() == type or type == 'All':
            num_q = num_q + 1
            if num_q == 10:
                tour_q = (row[0], row[1])
            if row[-1] >= speed1 and row[-1] <= speed2:
                num_sq = num_sq + 1
                if num_sq == 10:
                    tour_sq = (row[0], row[1])
            if row[2].rstrip() != 'Qualify':
                num = num + 1
                if num == 10:
                    tour_pure = (row[0], row[1])
                if row[-1] >= speed1 and row[-1] <= speed2:
                    num_s = num_s + 1
                    if num_s == 10:
                        tour_s = (row[0], row[1])
        row = cursor.fetchone()
    if num == 10:
        print(tour_pure[1], tour_q[1])
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s",
                       (tour_pure[0], tour_pure[1]))
        seq_pure = cursor.fetchone()[0]
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s", (tour_q[0], tour_q[1]))
        seq_q = cursor.fetchone()[0]
        print("type", name2, seq_pure, seq_q)
    elif tour_q:
        print(tour_q[1])
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s", (tour_q[0], tour_q[1]))
        seq_q = cursor.fetchone()[0]
        print("type", name2, seq_q)

    if num_s >= 10:
        print(tour_s[1], tour_sq[1])
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s",
                       (tour_s[0], tour_s[1]))
        seq_pure = cursor.fetchone()[0]
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s", (tour_sq[0], tour_sq[1]))
        seq_q = cursor.fetchone()[0]
        print("speed", name2, seq_pure, seq_q)
    elif tour_sq:
        print(tour_sq[1])
        cursor.execute("select top 1 sequence from Tournament where Name=%s and [year]=%s", (tour_sq[0], tour_sq[1]))
        seq_q = cursor.fetchone()[0]
        print("speed", name2, seq_q)

    flag_2 = 0
    if num != num_q:
        flag_2 = 1

    time1 = int(input('Use statistics starting from when for type simulation ? '))+200000
    #time2 = int(input('Use statistics ending in when ? '))+200000
    time2 = 202299
    time3 = int(input('Use statistics starting from when for type simulation ? ')) + 200000
    #time4 = int(input('Use statistics ending in when ? ')) + 200000
    time4 = 202299
    time5 = int(input('Use statistics starting from when for speed simulation ? ')) + 200000
    time6 = int(input('Use statistics starting from when for speed simulation ? ')) + 200000

    #N = int(input('How many times to simulate ? '))
    N = 5000
    outputprocess(cursor, name1, name2, elo1, elo2, speed1, speed2, type, N, s, time1, time2, time3, time4, time5, time6, qf, setmode)

    if flag_1*flag_2==1:
        print("have qualify")
        qf = 1
        time1 = int(input('Use statistics starting from when for type simulation ? ')) + 200000
        #time2 = int(input('Use statistics ending in when ? ')) + 200000
        time3 = int(input('Use statistics starting from when for type simulation ? ')) + 200000
        #time4 = int(input('Use statistics ending in when ? ')) + 200000
        time5 = int(input('Use statistics starting from when for speed simulation ? ')) + 200000
        time6 = int(input('Use statistics starting from when for speed simulation ? ')) + 200000

        outputprocess(cursor, name1, name2, elo1, elo2, speed1, speed2, type, N, s, time1, time2, time3, time4, time5, time6, qf,
                      setmode)
    connect.close()


if __name__ == '__main__':
    q='N'
    while q!='q':
        start()
        q = input('quit by entering q ')
        i = os.system("cls")