import re
import urllib.request
from bs4 import BeautifulSoup
import time
import pymssql
import json
import xlrd

# find player_id
def getplayerinfo(playername, cursor):
    cursor.execute("select ID from Player where Name=%s",playername)
    row = cursor.fetchone()
    id = -2
    if row != None:
        id = row[0]
    return id

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

# collect some infamous player
def getabnormalplayer(playerlist,cursor):

    # use player's name to get id
    id_list = []
    for num in range(len(playerlist)):
        playername=playerlist[num]
        idx=playerlist.index(playername)
        if idx!=num:
            id_list.append(id_list[idx])
            continue
        player = playername.replace(" ", "+")
        url = "https://www.ultimatetennisstatistics.com/playerProfile?name=" + player + "&tab=profile"
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

        Cname, Rid = getplayerrankinfo(playername)
        # insert new information
        cursor.execute("INSERT Player Values(%s,%s,%s,%s,%s,%s,%s,%s)",(id,playername,height,age,rank,country,Rid,Cname))
        print("Successfully insert "+playername)
        id_list.append(id)
        #connect.commit()

    return id_list

# get match statistics
def get_info(matchid1,matchid2,tournament_id,cursor):
    baseurl = "https://www.ultimatetennisstatistics.com/matchStats?matchId="
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
        "cookie": "__gads=ID=8e510b6285947c86-22a5e49889ce005f:T=1635837717:RT=1635837717:S=ALNI_MYHHyBt72nSwwUYVynb7diYpo4OeQ; _ga=GA1.1.1685613760.1635837706; __gpi=UID=000005475acc8079:T=1652331765:RT=1652755969:S=ALNI_MbnMD6tcYySoi-JM9pc5kvfZVGnHQ; _ga_8WG53NL8PJ=GS1.1.1652755967.5.1.1652755988.0"
    }
    #match=[]
    abnormal_player = []
    match_id_list = []
    local = []
    for i in range(matchid2,matchid1,-1):
        url = baseurl+str(i)
        req = urllib.request.Request(url, headers=head)
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        bs = BeautifulSoup(html, "html.parser")

        # skip W/O
        if bs.select("div[class='col-xs-5 text-left']")==[]:
            print("match "+str(matchid2 - i + 1)+" is absent!")
            continue

        # player's name
        player1 = bs.select("div[class='col-xs-5 text-left']")[0].text
        player2 = bs.select("div[class='col-xs-5 text-right']")[0].text

        player1_data = []
        player2_data = []
        pat = re.compile('(\d+)\s')
        pat_1 = re.compile('\s(\d+)')
        serve1 = bs.select("th[class='raw-data text-left']",limit=7)
        for item in serve1:
            if re.findall(pat, item.text):
                serve_data = re.findall(pat, item.text)
                player2_data = player2_data+serve_data
            if re.findall(pat_1, item.text):
                serve_data = re.findall(pat_1, item.text)
                player2_data = player2_data+serve_data
        serve2 = bs.select("th[class='raw-data text-right']",limit=7)
        for item in serve2:
            if re.findall(pat, item.text):
                serve_data = re.findall(pat, item.text)
                player1_data = player1_data+serve_data
            if re.findall(pat_1, item.text):
                serve_data = re.findall(pat_1, item.text)
                player1_data = player1_data+serve_data
        other = bs.select("div[id='matchStats-"+str(i)+"Other']")
        for item in other:
            if re.findall(pat, item.text):
                other_data = re.findall(pat, item.text)
                player1_data = player1_data+other_data[0:2]+other_data[4:6]+other_data[8:10]+other_data[34:35]+other_data[36:37]
                player2_data = player2_data+other_data[2:4]+other_data[6:8]+other_data[10:12]+other_data[35:36]+other_data[38:39]

        player1_data.insert(0, player1)
        player2_data.insert(0, player2)
        match_stat=process(player1_data, player2_data, cursor)

        # deal with player not famous
        if match_stat[0] == -2:
            abnormal_player.append(player1)
            print(player1+" is absent")
            match_id_list.append(matchid2 - i + 1)
            local.append("l")
        if match_stat[9] == -2:
            abnormal_player.append(player2)
            print(player2+" is absent")
            match_id_list.append(matchid2 - i + 1)
            local.append("r")

        match_stat.insert(0, tournament_id)
        match_stat.insert(1, matchid2-i+1)
        print(player1 + " vs " + player2 + " been selected")
        time.sleep(0.5)

        cursor.execute("INSERT Match_stats VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", tuple(match_stat))
        #connect.commit()

    return abnormal_player, match_id_list, local

# process statistics
def process(data1,data2,cursor):
    stats = [-1 for _ in range(0,30)]
    if len(data1) != 21:
        data1[len(data1):21] = [-1 for _ in range(len(data1),21)]
    if len(data2) != 21:
        data2[len(data2):21] = [-1 for _ in range(len(data2),21)]
    stats[0] = int(getplayerinfo(data1[0],cursor))
    stats[1] = int(data1[1])
    stats[2] = int(data1[3])
    stats[3] = int(data1[2])
    stats[4] = int(data1[10])
    stats[5] = int(data1[7])
    stats[6] = int(data1[9])
    stats[7] = int(data2[12])
    stats[8] = int(data2[11])
    stats[9] = int(getplayerinfo(data2[0], cursor))
    stats[10] = int(data2[1])
    stats[11] = int(data2[3])
    stats[12] = int(data2[2])
    stats[13] = int(data2[10])
    stats[14] = int(data2[7])
    stats[15] = int(data2[9])
    stats[16] = int(data1[12])
    stats[17] = int(data1[11])
    stats[18] = int(data1[14])
    stats[19] = int(data1[13])
    stats[20] = int(data1[15])
    stats[21] = int(data1[17])
    stats[22] = int(data1[19])
    stats[23] = int(data1[20])
    stats[24] = int(data2[14])
    stats[25] = int(data2[13])
    stats[26] = int(data2[15])
    stats[27] = int(data2[17])
    stats[28] = int(data2[19])
    stats[29] = int(data2[20])

    for i in range(0,len(stats)):
        if stats[i] == -1:
            stats[i] = None

    return stats

# get match result
def get_result(player,tournament_id,tournament_name,match,KO,year):
    for playerid in player:
        url = "https://www.ultimatetennisstatistics.com/matchesTable?playerId=" + str(int(playerid)) + "&current=1&rowCount=200&sort%5Bdate%5D=desc&searchPhrase=&season=&fromDate=&toDate=&level=&bestOf=&surface=&indoor=&speed=&round=&result=&opponent=&tournamentId=&tournamentEventId=&outcome=&score=&countryId=&bigWin=false&_="
        head = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
            # "sec-ch-ua": '"Chromium";v ="92","Not A;Brand";v="99","Google Chrome";v="92"',
            "Cookie": "_ga = GA1.2.324355889.1621857694;__gads=ID=8cfa7d12bbca2f6d-22ba21761bc80082:T=1621857691:RT = 1621857691:S=ALNI_MYJRBxeLS0iZna4gzE_F2cbdf8ZDA;gid = GA1.2.1014988429.1630369661"
        }
        req = urllib.request.Request(url, headers=head)
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        list = json.loads(html)["rows"]
        bo = False
        ot=0
        for item in list:
            if item["tournament"] == tournament_name:
                if item["winner"]["id"] == int(playerid):
                    if match-item["id"]<=0:
                        continue
                    if match-item["id"]>KO:
                        break
                    single = [int(playerid), item["loser"]["id"], match-item["id"], item["score"],tournament_id,year]
                    if item["score"] == "W/O":
                        print(str(item["id"]) + " should be kicked out!")
                    cursor.execute(
                        "INSERT result VALUES(%s,%s,%s,%s,%s,%s)", tuple(single))
                    print(str(match-item["id"])+" has been finished")
                    #connect.commit()
                else:
                    continue
                bo = True
            else:
                if bo == True:
                    break
        time.sleep(0.5)

# main
tournament_id = 41421
tournament = 414
tournament_name = "Hamburg"
start_id = 183008
end_id = 183034
seq = 38
year = 2021
level='ATP500'
court_type='Clay'
speed=44
KO=28

connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='tennis')
cursor = connect.cursor()
cursor.execute("Insert Tournament Values(%s,%s,%s,%s,%s,%s,%s,%s,%s)", (tournament, year, tournament_name, level, court_type, tournament_id, start_id, seq, speed))
abnormal = get_info(start_id-1,end_id,tournament_id, cursor)
if abnormal != []:
    abnormal_player = abnormal[0]
    match_id = abnormal[1]
    loc = abnormal[2]
    id_list = getabnormalplayer(abnormal_player, cursor)

    # deal with formal id_information with absence
    for i in range(len(loc)):
        if loc[i] == "l":
            cursor.execute("Update Match_stats SET p1_id=%s where match_id=%s and tournament_id=%s", (id_list[i], match_id[i], tournament_id))
            #connect.commit()
        if loc[i] == "r":
            cursor.execute("Update Match_stats SET p2_id=%s where match_id=%s and tournament_id=%s", (id_list[i], match_id[i], tournament_id))
            #connect.commit()

# select players who at least won a match in the tournament
cursor.execute("Select distinct p1_id from Match_stats where tournament_id=%s Union Select distinct p2_id from Match_stats b where tournament_id =%s and NOT EXISTS(select 1 from Match_stats a where tournament_id = %s and b.p2_id=a.p1_id)",(tournament_id, tournament_id, tournament_id))
row=cursor.fetchone()
player_list = []
# actually we have updated the id_information, so what below is not necessary
while row:
    if row[0] != -2:
        player_list.append(row[0])
    row=cursor.fetchone()
get_result(player_list, tournament, tournament_name, end_id+1,KO,year)
connect.commit()
connect.close()