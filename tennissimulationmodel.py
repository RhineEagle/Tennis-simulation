import random

class player(object):
    def __init__(self,ace,fin,fser,df,sser,bs,fret,sret,aace,adf,bc):
        self.ace=ace
        self.firstin=fin
        self.firstserve=fser
        self.doublefault=df
        self.secondserve=sser
        self.breaksave=bs
        self.firstreturn=fret
        self.secondreturn=sret
        self.aceagainst=aace
        self.doublefaultagainst=adf
        self.breakconvert=bc

def game(player1,player2,g1,g2,order):
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
        if p1>p2:
            g1=7
        else:
            g2=7
    else:
        while max(p1,p2)<4 or abs(p1-p2)<2:
            if(order>0):
                list=play(player1,player2,p1,p2)
                p1=list[0]
                p2=list[1]
            else:
                list=play(player2,player1,p2,p1)
                p2 = list[0]
                p1 = list[1]
        if p1>p2:
            g1=g1+1
        else:
            g2=g2+1
    return [g1,g2]

def play(player1,player2,p1,p2):
    p=random.random()
    if (p2==3 and p1<=2) or (p2>=4 and p2-p1==1):
        prob=player1.breaksave*(100-player2.breakconvert)/(player1.breaksave*(100-player2.breakconvert)+(100-player1.breaksave)*player2.breakconvert)
        if p>prob:
            p2=p2+1
        else:
            p1=p1+1
    else:
        if p<=player1.ace/100:
            p1=p1+1
        else:
            if p>player1.firstin:
                if p>1-player2.doublefault/100:
                    p2=p2+1
                else:
                    pr2=random.random()
                    prob=player1.secondserve*(100-player2.secondreturn)/(player1.secondserve*(100-player2.secondreturn)+(100-player1.secondserve)*player2.secondreturn)
                    if pr2>prob:
                        p2=p2+1
                    else:
                        p1=p1+1
            else:
                pr1=random.random()
                prob=player1.firstserve*(100-player1.firstreturn)/(player1.firstserve*(100-player2.firstreturn)+(100-player1.firstserve)*player2.firstreturn)
                if pr1>prob:
                    p2=p2+1
                else:
                    p1=p1+1
    return [p1,p2]

def playseven(player1,player2,p1,p2,i):
    p=random.random()
    if p <= player1.ace / 100:
        p1 = p1 + 1
    else:
        if p > player1.firstin:
            if p > 1 - player2.doublefault / 100:
                p2 = p2 + 1
            else:
                pr2 = random.random()
                prob = player1.secondserve * (100 - player2.secondreturn) / (
                            player1.secondserve * (100 - player2.secondreturn) + (
                                100 - player1.secondserve) * player2.secondreturn)
                if pr2 > prob:
                    p2 = p2 + 1
                else:
                    p1 = p1 + 1
        else:
            pr1 = random.random()
            prob = player1.firstserve * (100 - player1.firstreturn) / (
                        player1.firstserve * (100 - player2.firstreturn) + (
                            100 - player1.firstserve) * player2.firstreturn)
            if pr1 > prob:
                p2 = p2 + 1
            else:
                p1 = p1 + 1
    i=i+1
    return [p1,p2,i]

if __name__ == '__main__':
    player1=player(7.6,64.2,73.6,3.8,52.7,64.7,35.6,55.2,7.2,3.7,41.5)
    player2=player(4.7,64.4,72.6,2.4,52.7,68.1,35.2,56.4,7.2,3.5,48.3)
    setpoint1=0
    setpoint2=0
    order=1
    while setpoint1!=3 and setpoint2!=3:
        gamepoint1 = 0
        gamepoint2 = 0
        while max(gamepoint1,gamepoint2)<6 or (max(gamepoint1,gamepoint2)==6 and min(gamepoint1,gamepoint2)>=5):
            list=game(player1,player2,gamepoint1,gamepoint2,order)
            gamepoint1=list[0]
            gamepoint2=list[1]
            order=-1*order

        if gamepoint1>gamepoint2:
            setpoint1 = setpoint1 + 1
        else:
            setpoint2 = setpoint2 + 1
        print(gamepoint1, "vs", gamepoint2)

    print(setpoint1,"vs",setpoint2)