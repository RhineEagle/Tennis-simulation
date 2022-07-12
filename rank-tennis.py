import re
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import pymssql
import time
import xlrd

def getplayerinfo(name1,name2,cursor):
    lan1 = "select top 1 [C-Name],ID from Player Where [R-ID]=%s"
    lan2 = "select top 1 [C-Name],ID from Player Where [R-ID]=%s"

    cursor.execute(lan1,name1)
    info1 = cursor.fetchone()
    if info1==None:
        getabnormalplayer(name1,cursor)
        cursor.execute(lan1, name1)
        info1 = cursor.fetchone()
    cursor.execute(lan2,name2)
    info2 = cursor.fetchone()
    if info2==None:
        getabnormalplayer(name2,cursor)
        cursor.execute(lan2, name2)
        info2 = cursor.fetchone()
    return info1,info2

def getabnormalplayer(playername,cursor):
    # use player's name to get id
    file = "Rank_tennis.xls"
    workbook = xlrd.open_workbook(file)
    pat = re.compile(playername)
    Table = workbook.sheet_by_name("Sheet1")
    length = Table.nrows
    Name = None
    for i in range(length):
        row = Table.row_values(i)
        if pat.search(row[2]) != None:
            Name = row[0]
            break
    Player=Name.replace(" ","+")
    url = "https://www.ultimatetennisstatistics.com/playerProfile?name=" + Player + "&tab=profile"
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400"
    }
    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    info = bs.select("a[id='profilePill']", limit=1)[0]
    pat = re.compile('playerId=(\d+)')
    id = re.findall(pat, str(info))[0]
    time.sleep(1)

    # get player's id
    url = "https://www.ultimatetennisstatistics.com/playerProfileTab?playerId=" + str(id)
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400"
    }
    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    info1 = bs.select('table[class = "table table-condensed text-nowrap"]', limit=1)
    info2 = bs.select('table[class = "table table-condensed text-nowrap"]', limit=2)[1]
    pat = re.compile('(\d+)\s')
    age, country, height = None, None, None
    for sample in info1:
        list = sample.find_all('tr')
        for item in list:
            if item.find("th").text == "Age":
                age = re.findall(pat, item.find("td").text)[0]
            if item.find("th").text == "Country":
                country = item.find("span").text
            if item.find("th").text == "Height":
                height = re.findall(pat, item.find("td").text)[0]
    list = info2.find_all('tr')
    rank = None
    for item in list:
        if item.find("th") and item.find("th").text == "Current Rank":
            rank = re.findall(pat, item.find("td").text)[0]
            break

    Cname, Rid = getplayerrankinfo(Name)
    # insert new information
    cursor.execute("INSERT Player Values(%s,%s,%s,%s,%s,%s,%s,%s)",(id,Name,height,age,rank,country,Rid,Cname))
    print("Successfully insert "+Name)
    #connect.commit()

def getplayerrankinfo(playername):
    file = "Rank_tennis.xls"
    workbook = xlrd.open_workbook(file)
    pat=re.compile(playername)
    Table = workbook.sheet_by_name("Sheet1")
    length = Table.nrows
    id=None
    CName=None
    for i in range(length):
        row = Table.row_values(i)
        if pat.search(row[0])!=None:
            id=row[2]
            CName=row[1]
            break
    return CName,id

def getdata(id1,id2,player1,player2,eid,matchid,year,ID1,ID2,tournament_id,mid,winner,KO):
    url = 'https://www.rank-tennis.com/zh/stat/query'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'
    }

    data = {
        'id1': id1,
        'id2': id2,
        'p1': player1,
        'p2': player2,
        'eid': eid,
        'type': 'atp',
        'matchid': matchid,
        'year': year
    }

    print(id1,id2,matchid,player1.encode('latin1').decode('gbk'),player2.encode('latin1').decode('gbk'))
    # post请求的参数需要编码，因为post请求中不能出现字符串，必须是字节
    data = urllib.parse.urlencode(data).encode('utf-8')

    request = urllib.request.Request(url = url, data = data, headers = headers)
    response = urllib.request.urlopen(request)

    #获取响应的数据
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    #print(bs)
    p=bs.select("td")

    win_mark=bs.select("div[id='iStatHeads']")
    if win_mark==[]:
        return -1

    pat3 = re.compile("StatusFlag Statuswinner")
    pat4 = re.compile("StatusFlag Statusloser")
    win = re.search(pat3, str(win_mark)).span()[1]
    lose = re.search(pat4, str(win_mark)).span()[1]
    if win > lose:
        win_inner = 2
    else:
        win_inner = 1
    score_mark = bs.find_all('div', id='iStatScoreDiv')[0].select("td")
    score=[]

    t=win_mark[0]
    pinfo=[]
    p1=[]
    p2=[]
    for item in p:
        if item.text.strip():
            pinfo.append(item.text.strip())

    pat1=re.compile("/(\d+)[)]")
    pat2=re.compile(("[(](\d+)/"))

    for item in score_mark:
        if item.text.strip():
            score.append(item.text.strip())
    if score==[] or (score[0] == '0' and score[1] == '0'):
        score_str = "W/O"
        getmatchresult(ID1,ID2,winner,mid,tournamentid,score_str,KO,cursor)
        return 0

    score_str=processscore(score,win_inner)
    getmatchresult(ID1,ID2,winner,mid,tournamentid,score_str,KO,cursor)

    id=pinfo.index("ACE")
    p1.append(int(pinfo[id-1]))
    p2.append(int(pinfo[id+1]))
    id=pinfo.index("双误")
    p1.append(int(pinfo[id-1]))
    p2.append(int(pinfo[id+1]))
    id=pinfo.index("一发成功率")
    p1.append(int(re.findall(pat1,pinfo[id-1])[0]))
    p2.append(int(re.findall(pat1,pinfo[id+1])[0]))
    p1.append(int(re.findall(pat1,pinfo[id-1])[0])-int(re.findall(pat2,pinfo[id-1])[0]))
    p2.append(int(re.findall(pat1,pinfo[id+1])[0])-int(re.findall(pat2,pinfo[id+1])[0]))
    id=pinfo.index("一发得分率")
    p1.append(int(re.findall(pat2,pinfo[id-1])[0]))
    p2.append(int(re.findall(pat2,pinfo[id+1])[0]))
    id=pinfo.index("二发得分率")
    p1.append(int(re.findall(pat2,pinfo[id-1])[0]))
    p2.append(int(re.findall(pat2,pinfo[id+1])[0]))
    id=pinfo.index("破发点转化率")
    p1.append(int(re.findall(pat1,pinfo[id-1])[0]))
    p2.append(int(re.findall(pat1,pinfo[id+1])[0]))
    p1.append(int(re.findall(pat1,pinfo[id-1])[0])-int(re.findall(pat2,pinfo[id-1])[0]))
    p2.append(int(re.findall(pat1,pinfo[id+1])[0])-int(re.findall(pat2,pinfo[id+1])[0]))
    id=pinfo.index("总得分")
    p1.append(int(pinfo[id-1]))
    p2.append(int(pinfo[id+1]))
    if "制胜分" in pinfo:
        id=pinfo.index("制胜分")
        p1.append(int(pinfo[id-1]))
        p2.append(int(pinfo[id+1]))
        id=pinfo.index("非受迫性失误")
        p1.append(int(pinfo[id-1]))
        p2.append(int(pinfo[id+1]))
        p1.append(-1)
        p2.append(-1)
    if "平均一发速度" in pinfo:
        id=pinfo.index("平均一发速度")
        if pinfo[id-1][0] == '1' or '2':
            p1.append(int(pinfo[id-1][0:3]))
        else:
            p1.append(int(pinfo[id-1][0:2]))
        if pinfo[id+1][0] == '1' or '2':
            p2.append(int(pinfo[id+1][0:3]))
        else:
            p2.append(int(pinfo[id+1][0:2]))
        id = pinfo.index("平均二发速度")
        if pinfo[id-1][0] == '1' or '2':
            p1.append(int(pinfo[id-1][0:3]))
        else:
            p1.append(int(pinfo[id-1][0:2]))
        if pinfo[id+1][0] == '1' or '2':
            p2.append(int(pinfo[id + 1][0:3]))
        else:
            p2.append(int(pinfo[id + 1][0:2]))
    if winner==2:
        ID1,ID2=ID2,ID1
    if win_inner==2:
        p1,p2=p2,p1

    stats=process(p1,p2,ID1,ID2)
    stats.insert(0, tournament_id)
    stats.insert(1, KO-mid)
    print(stats)
    cursor.execute(
        "INSERT Match_stats VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        tuple(stats))

def getmatchresult(id1,id2,winner,mid,tournamentid,score_str,KO,cursor):
    if winner==2:
        id1,id2=id2,id1
    tourid=tournamentid//100
    year=2000+tournamentid%100
    cursor.execute("Insert result VALUES(%s,%s,%s,%s,%s,%s)",(id1,id2,KO-mid,score_str,tourid,year))
    print([id1,id2,KO-mid,score_str,tourid,year])

def process(data1,data2,id1,id2):
    stats = [-1 for _ in range(0,30)]
    if len(data1) != 14:
        data1[len(data1):14] = [-1 for _ in range(len(data1),14)]
    if len(data2) != 14:
        data2[len(data2):14] = [-1 for _ in range(len(data2),14)]
    stats[0] = int(id1)
    stats[1] = int(data1[0])
    stats[2] = int(data1[1])
    stats[3] = int(data1[2])
    stats[4] = int(data1[3])
    stats[5] = int(data1[4])
    stats[6] = int(data1[5])
    stats[7] = int(data1[6])
    stats[8] = int(data1[7])
    stats[9] = int(id2)
    stats[10] = int(data2[0])
    stats[11] = int(data2[1])
    stats[12] = int(data2[2])
    stats[13] = int(data2[3])
    stats[14] = int(data2[4])
    stats[15] = int(data2[5])
    stats[16] = int(data2[6])
    stats[17] = int(data2[7])
    stats[18] = int(data1[8])
    stats[19] = int(data1[9])
    stats[20] = int(data1[10])
    stats[21] = int(data1[11])
    stats[22] = int(data1[12])
    stats[23] = int(data1[13])
    stats[24] = int(data2[8])
    stats[25] = int(data2[9])
    stats[26] = int(data2[10])
    stats[27] = int(data2[11])
    stats[28] = int(data2[12])
    stats[29] = int(data2[13])

    for i in range(0,len(stats)):
        if stats[i] == -1:
            stats[i] = None

    return stats

def processscore(score,winner):
    score_str=""
    if winner==2:
        for i in range(0,len(score),2):
            score[i],score[i+1]=score[i+1],score[i]
    for i in range(0,len(score)):
        if int(score[i])>59:
            temp=""
            if len(score[i])==2:
                temp=score[i][0]+"("+score[i][1]+")"
            elif len(score[i])==4:
                temp = score[i][0:1] + "(" + score[i][2:3] + ")"
            elif len(score[i])==3 and int(score[i][0])==1:
                temp = score[i][0:1] + "(" + score[i][2] + ")"
            else:
                temp = score[i][0] + "(" + score[i][1:3] + ")"
            if i%2==0:
                score_str=score_str+temp+"-"
            elif i==len(score)-1:
                score_str=score_str+temp
            else:
                score_str=score_str+temp+" "
        else:
            if i%2==0:
                score_str=score_str+score[i]+"-"
            elif i==len(score)-1:
                score_str=score_str+score[i]
            else:
                score_str=score_str+score[i]+" "
        time.sleep(0.3)
    return score_str

def getmatchinfo(name,matchid,mid,eid,year,tournamentid,winner):
    info1,info2=getplayerinfo(name[0],name[1],cursor)

    if getdata(name[0],name[1],info1[0],info2[0],eid,matchid,year,info1[1],info2[1],tournamentid,mid,winner,KO)==-1:
        return -1

eid='WC'
tournamentid=54022
year=2022
tournament="Wimbledon"
type="Grass"
level="Grand Slam"
KO=128
seq=40
speed=65
status='Finish'
constraint_stop_num=KO

mode='date'
#mode='tour'
url="https://www.rank-tennis.com/zh/result/2022-07-10"
#url="https://www.rank-tennis.com/zh/schedule/"+ eid +"/"+str(year)
head={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
    'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'

}
req=urllib.request.Request(url,headers=head)
response=urllib.request.urlopen(req)
html=response.read().decode('utf-8')
bs=BeautifulSoup(html,"html.parser")
if mode == 'date':
    bs=bs.find_all('div',attrs={'class':'cResultTour','data-eid':eid})[0]
a=bs.find_all('div',class_='cResultMatch')
pat=re.compile(r'Q\d')
pattern=re.compile("cResultPlayer(\w+)")
patro=re.compile('match-id="(\w+)"')

connect=pymssql.connect(server='LAPTOP-BBQ77BE4',user='sa', password='123456', database='tennis',charset='utf8')
cursor=connect.cursor()

cursor.execute("Insert Tournament Values(%s,%s,%s,%s,%s,%s,%s,%s,%s)", (tournamentid//100, year, tournament, level, type, tournamentid, None, seq,speed))

num=0
for item in a:
    if item.select("div[class='cResultMatchGender']")[0].text=="男单" and re.match(pat,item.select("div[class='cResultMatchRound']")[0].text)==None:
        pat3 = re.compile('cResultMatchMidTableRow"')
        pat4 = re.compile("cResultMatchMidTableRowWinner")
        win = re.search(pat4, str(item)).span()[1]
        lose = re.search(pat3, str(item)).span()[1]
        if win > lose:
            winner = 2
        else:
            winner = 1
        num=num+1
        name=re.findall(pattern,str(item))
        match=re.findall(patro,str(item))[0]
        round_=item.select("div[class='cResultMatchRound']")[0].text
        print(round_)
        if level=='Grand Slam':
            mid=int(match[-2:])-1+2**(7-int(match[-3]))
        else:
            mid=num
        if getmatchinfo(name,match,mid,eid,year,tournamentid,winner)==-1:
            if status=='Completing':
                print("The match hasn't started.")
                continue
            else:
                info1,info2=getplayerinfo(name[0],name[1],cursor)
                if winner==2:
                    info1,info2=info2,info1
                tourid = tournamentid // 100
                print([info1[1],info2[1], KO - mid, 'W/O', tourid, year])
                cursor.execute("Insert result VALUES(%s,%s,%s,%s,%s,%s)", (info1[1],info2[1], KO - mid, 'W/O', tourid, year))

        if num+1==constraint_stop_num:
            break
print("there are "+str(num)+" matches be selected.")

connect.commit()