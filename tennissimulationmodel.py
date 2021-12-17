import random
import re
import urllib.request
from bs4 import BeautifulSoup
import json
import xlrd
import time
import numpy as np
import copy
import pandas as pd

def getplayerinfo(playername):
    file = "UTS_playerinfo.xls"
    workbook = xlrd.open_workbook(file)
    pat=re.compile(playername)
    Table = workbook.sheet_by_name("sheet1")
    length = Table.nrows
    id=-1
    for i in range(length):
        row = Table.row_values(i)
        if pat.search(row[0])!=None:
            id=row[1]
            break
    return id

def get_elo(playerid,surface):
    baseurl="https://www.ultimatetennisstatistics.com/playerRankings?playerId="
    url=baseurl+playerid
    head={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400"
    }
    req=urllib.request.Request(url,headers=head)
    response=urllib.request.urlopen(req)
    html=response.read().decode('utf-8')
    bs=BeautifulSoup(html,"html.parser")
    type1="tr[class='bg-surface-"
    type2="']"
    list=bs.select(type1+surface+type2)
    pat=re.compile('\d+\s.(\d+).')
    elo=[]
    for item in list:
        if re.findall(pat,item.text):
            elo=re.findall(pat,item.text)
    if int(elo[0])<=1600:
        elo[0]="1600"
    return elo[0]

def getvariance(playerid,surface,opponent):
    url = "https://www.ultimatetennisstatistics.com/matchesTable?playerId="+playerid+"&current=1&rowCount=15&sort%5Bdate%5D=desc&searchPhrase=&season=&fromDate=&toDate=&level=&bestOf=&surface="+surface+"&indoor=&speed=&round=&result=&opponent=&tournamentId=&tournamentEventId=&outcome=&score=&countryId=&bigWin=false&_="
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
        #"sec-ch-ua": '"Chromium";v ="92","Not A;Brand";v="99","Google Chrome";v="92"',
        #"Cookie": "_ga = GA1.2.324355889.1621857694;__gads=ID=8cfa7d12bbca2f6d-22ba21761bc80082:T=1621857691:RT = 1621857691:S=ALNI_MYJRBxeLS0iZna4gzE_F2cbdf8ZDA;gid = GA1.2.1014988429.1630369661"
    }
    req = urllib.request.Request(url, headers=head)
    print("1")
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    print("1")
    conlist = json.loads(html)
    matchlist = []
    wollist = []
    stats = np.zeros((8, 10), dtype=float)
    for i in range(0, 10):
        matchlist.append(conlist["rows"][i]["id"])
        wollist.append((conlist["rows"][i]["winner"]["id"] == int(playerid)))
        #print(conlist["rows"][i]["id"])
        # print(wollist[i])
    s = 0
    i = 0
    sigma = []
    while s < 8:
        j = 0
        time.sleep(0.2)
        url = "https://www.ultimatetennisstatistics.com/matchStats?matchId=" + str(matchlist[i])
        req = urllib.request.Request(url, headers=head)
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        bs = BeautifulSoup(html, "html.parser")
        if wollist[i] == True:
            list = bs.select("th[class='text-" + "right" + " pct-data']", limit=10)
        else:
            list = bs.select("th[class='text-" + "left" + " pct-data']", limit=10)
        print(list)
        if list == []:
            i = i + 1
            continue
        for m in list:
            # print(m.text)
            if m.text:
                value = float(m.text.strip("%"))
                stats[s][j] = value
                j = j + 1
            else:
                value = np.NaN
                stats[s][j] = value
                j = j + 1
        i = i + 1
        s = s + 1
    for i in range(0, 10):
        sigma.append(pd.DataFrame(stats[:, i]).std(ddof=0))
    return sigma

def getstats(playerid,surface,opponent,type):
    baseurl1="https://www.ultimatetennisstatistics.com/matchesStats?playerId="
    baseurl2="&season=&fromDate=01-07-2021&toDate=&level="
    baseurl3="&bestOf=&surface="
    baseurl4="&indoor=&speed=&round=&result=&opponent="
    baseurl5="&tournamentId=&tournamentEventId=&outcome=&score=&countryId=&bigWin=false&searchPhrase="
    url=baseurl1+playerid+baseurl2+type+baseurl3+surface+baseurl4+opponent+baseurl5
    head={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400"
    }
    req=urllib.request.Request(url,headers=head)
    response=urllib.request.urlopen(req)
    html=response.read().decode('utf-8')
    bs=BeautifulSoup(html,"html.parser")

    list=bs.select("th[class='text-right pct-data']",limit=13)
    stats=[]
    for m in list:
        if m.text:
            value=float(m.text.strip("%"))
            stats.append(value)
    return stats

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
        return 0.02
    elif x==2:
        return -0.01
    elif x==3:
        return -0.02
    elif x==4:
        return -0.06
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
                if p>1-player2.doublefault/100:
                    p2=p2+1
                    #print(g1, " ", g2," " , player1.name,p1,"df!")
                else:
                    pr2=random.random()
                    #prob=player1.secondserve*(100-player2.secondreturn)/(player1.secondserve*(100-player2.secondreturn)+(100-player1.secondserve)*player2.secondreturn)
                    prob=player1.secondserve/100*weigh+(1-player2.secondreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.05,stochastic(num)+0.02)
                    #prob = player1.secondserve / 100 * weigh + (1 - player2.secondreturn / 100) * (1 - weigh)
                    #print(player1.name,prob)
                    if pr2>prob:
                        p2=p2+1
                    else:
                        p1=p1+1
            else:
                pr1=random.random()
                #prob=player1.firstserve*(100-player1.firstreturn)/(player1.firstserve*(100-player2.firstreturn)+(100-player1.firstserve)*player2.firstreturn)
                prob=player1.firstserve/100*weigh+(1-player2.firstreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.04,stochastic(num)+0.04)
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
            if p > 1 - player2.doublefault / 100:
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
    player.breaksave=player.breaksave+np.random.normal(loc=0.0, scale=var[5])
    player.firstreturn=player.firstreturn+np.random.normal(loc=0.0, scale=var[7])
    player.secondreturn=player.secondreturn+np.random.normal(loc=0.0, scale=var[8])
    player.breakconvert=player.breakconvert+np.random.normal(loc=0.0, scale=var[9])

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
    #print_obj(player22)
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

def match(playername1,playername2,surface,opponent1,opponent2,type1,type2,setmode,N):
    playerid1 = str(int(getplayerinfo(playername1)))
    playerid2 = str(int(getplayerinfo(playername2)))
    if playerid2 == "-1" or playerid1 == "-1":
        exit(1)
    stats1 = getstats(playerid1, surface, opponent1, type1)
    print("Information 1 has been collected")
    time.sleep(4)

    var1=[7.38,2.97,6.16,8.97,19.03,21.923,10.865,8.9606,10.6145,21.0954]
    #var2 = [4.754, 4.1877, 7.1376, 9.6336, 13.2930, 33.8474, 10.4223, 8.8171, 8.5922, 30.9808]

    player1 = player(playername1, stats1[0], stats1[2], stats1[3], stats1[1], stats1[4], stats1[5], stats1[10],
                     stats1[11],
                     stats1[12], int(get_elo(playerid1, surface)))
    print_obj(player1)
    time.sleep(0.5)
    stats2 = getstats(playerid2, surface, opponent2, type2)
    print("Information 2 has been collected")
    time.sleep(8)
    #var1 = getvariance(playerid1, surface, opponent1)
    print(var1)
    var2 = getvariance(playerid2, surface, opponent2)
    print(var2)
    player2 = player(playername2, stats2[0], stats2[2], stats2[3], stats2[1], stats2[4], stats2[5], stats2[10],
                     stats2[11],
                     stats2[12], int(get_elo(playerid2, surface)))
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

if __name__ == '__main__':

    type1="" #match type
    type2 = ""
    playername1="Djokovic"
    playername2="Medvedev"
    surface = "H"   #court type
    opponent1 = ""
    opponent2 = ""
    setmode=3
    N = 10000
    match(playername1, playername2, surface, opponent1, opponent2, type1, type2, setmode, N)