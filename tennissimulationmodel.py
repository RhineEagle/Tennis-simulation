import random
import re
import urllib.request
from bs4 import BeautifulSoup
import xlrd
import time

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

def getstats(playerid,surface,opponent,type):
    baseurl1="https://www.ultimatetennisstatistics.com/matchesStats?playerId="
    baseurl2="&season=&fromDate=20-06-2020&toDate=07-08-2021&level="
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
    weigh=(player1.elo-1500)/(player1.elo+player2.elo-3000)
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
        if p<=player1.ace/100+random.uniform(stochastic(num)-0.025,stochastic(num)+0.01):
            p1=p1+1
            #print(g1, " ", g2, " ", player1.name, p1, "ace!")
        else:
            if p>player1.firstin/100+random.uniform(stochastic(num)-0.06,stochastic(num)+0.06):
                if p>1-player2.doublefault/100:
                    p2=p2+1
                    #print(g1, " ", g2," " , player1.name,p1,"df!")
                else:
                    pr2=random.random()
                    #prob=player1.secondserve*(100-player2.secondreturn)/(player1.secondserve*(100-player2.secondreturn)+(100-player1.secondserve)*player2.secondreturn)
                    prob=player1.secondserve/100*weigh+(1-player2.secondreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.05,stochastic(num)+0.02)
                    #print(player1.name,prob)
                    if pr2>prob:
                        p2=p2+1
                    else:
                        p1=p1+1
            else:
                pr1=random.random()
                #prob=player1.firstserve*(100-player1.firstreturn)/(player1.firstserve*(100-player2.firstreturn)+(100-player1.firstserve)*player2.firstreturn)
                prob=player1.firstserve/100*weigh+(1-player2.firstreturn/100)*(1-weigh)+random.uniform(stochastic(num)-0.05,stochastic(num)+0.04)
                if pr1>prob:
                    p2=p2+1
                else:
                    p1=p1+1
    return [p1,p2]

def playseven(player1,player2,p1,p2,i):
    weigh = (player1.elo - 1500) / (player1.elo + player2.elo - 3000)
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

def playset(player1,player2):
    setpoint1 = 0
    setpoint2 = 0
    order = 1
    #while setpoint1 != 3 and setpoint2 != 3:
    while setpoint1 != 2 and setpoint2 != 2:
        gamepoint1 = 0
        gamepoint2 = 0
        while max(gamepoint1, gamepoint2) < 6 or (
                max(gamepoint1, gamepoint2) == 6 and min(gamepoint1, gamepoint2) >= 5):
            list = game(player1, player2, gamepoint1, gamepoint2, order, setpoint1 + setpoint2 + 1)
            gamepoint1 = list[0]
            gamepoint2 = list[1]
            order = -1 * order

        if gamepoint1 > gamepoint2:
            setpoint1 = setpoint1 + 1
        else:
            setpoint2 = setpoint2 + 1
    #     if (gamepoint1 == 6 and gamepoint2 == 7) or (gamepoint2 == 6 and gamepoint1 == 7):
    #         print(gamepoint1, "vs", gamepoint2,"(",min(list[2],list[3]),")")
    #     else:
    #         print(gamepoint1, "vs", gamepoint2)
    #
    # print(setpoint1,":",setpoint2)
    return [setpoint1,setpoint2]

def print_obj(obj):
    print (['%s:%s' % item for item in obj.__dict__.items()])

if __name__ == '__main__':

    type="AB"
    playername1="Mcdonald"
    playername2="Sinner"
    surface = "H"
    opponent1 = "TOP_100"
    opponent2 = "TOP_100"

    playerid1 = str(int(getplayerinfo(playername1)))
    playerid2 = str(int(getplayerinfo(playername2)))
    if playerid2=="-1" or playerid1=="-1":
        exit(1)
    stats1=getstats(playerid1,surface,opponent1,type)
    print("Information 1 has been collected")
    time.sleep(2)
    player1 = player(playername1, stats1[0], stats1[2], stats1[3], stats1[1], stats1[4], stats1[5], stats1[10], stats1[11],
                     stats1[12], int(get_elo(playerid1,surface)))
    print_obj(player1)
    time.sleep(2)
    stats2=getstats(playerid2,surface,opponent2,type)
    print("Information 2 has been collected")
    time.sleep(2)
    player2 = player(playername2, stats2[0], stats2[2], stats2[3], stats2[1], stats2[4], stats2[5], stats2[10], stats2[11],
                     stats2[12], int(get_elo(playerid2,surface)))
    print_obj(player2)
    list1 = []
    list2 = []
    sum30 = 0
    sum31 = 0
    sum32 = 0
    sum23 = 0
    sum13 = 0
    sum03 = 0
    sum20 = 0
    sum21 = 0
    sum12 = 0
    sum02 = 0
    N=10000

    print("start to simulate...")
    for i in range(0, N):
        list = playset(player1, player2)
        list1.append(list[0])
        list2.append(list[1])
    for i in range(0, N):
        # if list1[i] == 3 and list2[i] == 0:
        #     sum30 += 1
        # elif list1[i] == 3 and list2[i] == 1:
        #     sum31 += 1
        # elif list1[i] == 3 and list2[i] == 2:
        #     sum32 += 1
        # elif list1[i] == 2 and list2[i] == 3:
        #     sum23 += 1
        # elif list1[i] == 1 and list2[i] == 3:
        #     sum13 += 1
        # else:
        #     sum03 += 1

        if list1[i] == 2 and list2[i] == 0:
            sum20 += 1
        elif list1[i] == 2 and list2[i] == 1:
            sum21 += 1
        elif list1[i] == 1 and list2[i] == 2:
            sum12 += 1
        else:
            sum02 += 1

    # print(player1.name,"3:0",player2.name, sum30 / N)
    # print(player1.name,"3:1",player2.name, sum31 / N)
    # print(player1.name,"3:2",player2.name, sum32 / N)
    # print(player1.name,"2:3",player2.name, sum23 / N)
    # print(player1.name,"1:3",player2.name, sum13 / N)
    # print(player1.name,"0:3",player2.name, sum03 / N)

    print(player1.name, "2:0", player2.name, sum20 / N)
    print(player1.name, "2:1", player2.name, sum21 / N)
    print(player1.name, "1:2", player2.name, sum12 / N)
    print(player1.name, "0:2", player2.name, sum02 / N)