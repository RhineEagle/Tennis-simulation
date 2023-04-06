import pandas as pd
import pymssql
import re
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import time
import datetime
import xlrd
from xlutils.copy import copy
import pycountry as pc
import json
import numpy as np
import warnings
from retrying import retry
warnings.filterwarnings('ignore')

def getplayerinfo(name1,name2,cursor,add_info):
    lan1 = "select top 1 ID from Player Where Name = %s"
    lan2 = "select top 1 ID from Player Where Name = %s"

    if name1=='Evgenii Tiurnev':
        name1='Evgenii Tyurnev'
    if name2=='Evgenii Tiurnev':
        name2='Evgenii Tyurnev'

    cursor.execute(lan1,name1)
    info1 = cursor.fetchone()
    if info1==None:
        lan1 = "select top 1 ID from Player Where Name like %s"
        name_1 = name1.replace(" ","%")
        name_1 = name_1.replace("-", "%")
        name_1 = name_1+"%"
        cursor.execute(lan1, name_1)
        info1 = cursor.fetchone()

    if info1==None:
        add_info_1 = add_info[0:3]
        id = getabnormalplayer(name1,cursor,add_info_1)
        cursor.execute(lan1, name1)
        info1 = cursor.fetchone()
        if info1 == None:
            print("just name error")
            info1 = [id]
            cursor.execute("Update Player set Name=%s where ID=%s",(name1,id))

    cursor.execute(lan2,name2)
    info2 = cursor.fetchone()
    if info2==None:
        lan2 = "select top 1 ID from Player Where Name like %s"
        name_2 = name2.replace(" ","%")
        name_2 = name_2.replace("-", "%")
        name_2 = name_2+"%"
        cursor.execute(lan2, name_2)
        info2 = cursor.fetchone()

    if info2==None:
        add_info_2 = add_info[3:6]
        id = getabnormalplayer(name2, cursor, add_info_2)
        cursor.execute(lan2, name2)
        info2 = cursor.fetchone()
        if info2 == None:
            print("just name error")
            info2 = [id]
            cursor.execute("Update Player set Name=%s where ID=%s", (name2, id))

    return info1[0],info2[0]

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

@retry(stop_max_attempt_number=3, wait_fixed=3000)
def getabnormalplayer(playername,cursor,add_info):
    print("search for "+playername)
    # use player's name to get id
    file = "Rank_tennis.xls"
    workbook = xlrd.open_workbook(file)
    pat = re.compile(playername)
    Table = workbook.sheet_by_name("Sheet1")
    length = Table.nrows
    Name = None
    for i in range(length):
        row = Table.row_values(i)
        if pat.search(row[1]) != None:
            Name = row[0]
            r_id = row[2]
            break
    if Name==None:
        Name=playername
        r_id = None
        time.sleep(2)
        newbook=copy(workbook)
        newsheet=newbook.get_sheet(0)
        newsheet.write(length,0,Name)
        newsheet.write(length,1,Name)
        newsheet.write(length,2,r_id)
        newbook.save(file)

    Player=Name.replace(" ","+")
    url = "https://www.ultimatetennisstatistics.com/playerProfile?name=" + Player + "&tab=profile"
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400"
    }
    req = urllib.request.Request(url, headers=head)
    try:
        response = urllib.request.urlopen(req)
    except:
        cursor.execute("select max(ID) from Player")
        id=cursor.fetchone()[0]
        if id >=80000:
            id=id+1
        else:
            id=80000
        cursor.execute("INSERT Player Values(%s,%s,%s,%s,%s,%s,%s)", (id, Name, add_info[0], add_info[2], pc.countries.get(alpha_3=add_info[1]).official_name, r_id, playername))
        print("Success to artificially insert " + Name)
        return id
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

    Cname, Rid = getplayerrankinfo(Name)
    # insert new information
    cursor.execute("INSERT Player Values(%s,%s,%s,%s,%s,%s,%s)",(id,Name,height,age,country,Rid,Cname))
    print("Successfully insert " + Name)
    #connect.commit()
    return id

def levelconvert(level):
    if level=='ATP-250-2019':
        return 'ATP250'
    elif level=='ATP-500-2019':
        return 'ATP500'
    elif level=='ATP-1000-2019':
        return 'ATP1000'
    elif level[0:2]=='GS':
        return 'Grand Slam'
    else:
        return level

def convert(id):
    if id=='AO':
        return 580
    elif id=='RG':
        return 520
    elif id=='WC':
        return 540
    elif id=='UO':
        return 560
    else:
        return int(id)

def convert_GS(eid):
    if eid=='580':
        return 'AO'
    elif eid=='520':
        return 'RG'
    elif eid=='540':
        return 'WC'
    elif eid=='560':
        return 'UO'
    else:
        if len(eid)==3:
            eid='0'+eid
        return eid

@retry(stop_max_attempt_number=3, wait_fixed=3000)
def extend_tour_info(href,data,head):
    req = urllib.request.Request(url=href, data=data, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    return html

def get_tour_list(year_):
    url="https://www.rank-tennis.com/en/calendar/"+str(year_)
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400"
    }
    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    content = bs.select('table[class="cCalendarTable"]')[0].select('tr')
    pat1 = re.compile("/draw/(\w+)/20")
    pat2 = re.compile("/level_logo/(.+).png")
    pat = re.compile("\d+\s([A-Za-z]+)")
    pat_date = re.compile("(\d+-\d+-\d+)\s~\s(\d+-\d+-\d+)")
    pat_country = re.compile("images/flag_svg/(\w+).svg")
    num = 0
    # connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='wta-tennis')
    # cursor = connect.cursor()
    t_num=0
    t_info = []

    for item in content:
        #date = item.text[0:10]
        #print(date)
        tour = item.select('div[class="cCalendarTour cCalendarTourM"]')
        tour += item.select('div[class="cCalendarTour cCalendarTourMW"]')
        for match in tour:
            num = num + 1
            name = match.text.strip()
            href = match['href']
            img = match.select('img[src]')[0]
            try:
                fla = match.select('img[class="cImgPlayerFlag"]')[0]
                country = re.findall(pat_country, str(fla))[0]
            except:
                country = None
            eid = re.findall(pat1, href)[0]
            if eid == 'OL':
                continue
            id = convert(eid)
            if len(eid)==3:
                eid.insert(0,'0')
            level = re.findall(pat2, str(img))[0]
            level = levelconvert(level)
            if level[0:2]=='GS':
                level='Grand Slam'
            #date = datetime.datetime.strptime(date,'%Y-%m-%d')
            head = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
                'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'
            }
            data = {
                'device': 0,
                'screen_width': 1280,
                'screen_height': 800
            }
            data = urllib.parse.urlencode(data).encode('utf-8')
            html = extend_tour_info(href,data,head)
            bs = BeautifulSoup(html, "html.parser")
            type = bs.select('div[id="iDrawTourDate"]')[0]
            date = re.findall(pat_date,str(type))[0]
            date1 = date[0]
            date2 = date[1]
            print(date1,date2)
            type = re.findall(pat,str(type))[0]
            info = (id*100+year_%100,year_,name,level,type,num,None,date1,date2,country)
            print(info)
            # cursor.execute("Insert Tournament Values(%s,%s,%s,%s,%s,%s,%s,%s)",info)
            # select_data('tour', eid, eid, id*100+22, 2022, name, type, level, num, None, 'Finish', date,
            #             128, True)
            fmt = '%Y-%m-%d'
            time_tuple = time.strptime(date1, fmt)
            year, month, day = time_tuple[:3]
            date = datetime.date(year, month, day)
            delta = datetime.timedelta(days=3)
            date1 = date - delta
            date1 = date1.strftime('%Y-%m-%d')
            delta = datetime.timedelta(days=1)
            date2 = date - delta
            date2 = date2.strftime('%Y-%m-%d')
            id_q = 99*10**(len(str(id))+2)+year_%100+id*100
            infoq = (id_q, year_, name+' Q', 'Qualify', type, num, None, date1, date2, country)
            print(infoq)
            # cursor.execute("Insert Tournament Values(%s,%s,%s,%s,%s,%s,%s,%s)", infoq)
            # select_data('tour', eid, eid, id*100+22+9000000, 2022, name+' Q', type, 'Qualify', num, None, 'Finish', date,
            #             128, True)
            # connect.commit()
            # t_num=t_num+1
            # print("have select "+t_num+" tournament")
            t_info+=[infoq,info]
    with open("tour_list_a_"+str(year_)+".txt",'w') as f:
        for item in t_info:
            f.write(str(item)+"\n")
        f.close()

def get_speed(tourid, info):

    tournament_speed = None
    for item in info:
        if item['tournamentExtId'] == str(tourid):
            try:
                tournament_speed = item['speed']
            except:
                tournament_speed = input('input the speed')
            break
    return tournament_speed

def select_info(year_):

    connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()

    with open("tour_list_a_"+str(year_)+".txt",'r') as f:
        content = f.readlines()
        f.close()

    url = "https://www.ultimatetennisstatistics.com/tournamentEventsTable?current=1&rowCount=-1&sort%5Bdate%5D=desc&searchPhrase=&season=" + str(
        year_) + "&level=&surface=&indoor=&speed=&tournamentId=&_=1677723790073"
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'

    }

    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    # bs = BeautifulSoup(html, "html.parser")

    info_ = json.loads(html)['rows']

    for item in content:
        info = tuple(eval(item))
        if info[3] == 'Qualify':
            continue
        Name = info[2]
        if Name == 'Toronto' or Name == 'Montreal':
            Name = 'Canada Masters'
        elif info[3] == 'ATP1000':
            Name = Name+' Masters'
        elif Name == 'French Open':
            Name = 'Roland Garros'
        elif Name == 'Washington DC':
            Name = 'Washington'
        elif Name == "'s-Hertogenbosch":
            Name = 's Hertogenbosch'
        elif Name == 'St Petersburg':
            Name = 'St. Petersburg'
        elif Name == "London / Queen's Club":
            Name = "Queen's Club"
        elif Name == "Vina del Mar":
            Name = 'Santiago'
        elif Name == 'London':
            Name = 'Tour Finals'


        tournamentid = int(info[0])
        type = info[4]
        if Name == 'Tour Finals':
            level = 'Tour Final'
        else:
            level = info[3]
        seq = int(info[5]) - 1
        tourid = tournamentid // 100
        speed = get_speed(tourid, info_)
        date = datetime.datetime.strptime(info[7], '%Y-%m-%d')

        cursor.execute("Insert Tournament Values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                       (tournamentid // 100, year_, Name, level, type, tournamentid, None, seq, speed, date))
        stats = pd.read_csv("C:/Users/math_conservatism/PycharmProjects/pythonProject/project/tennis_atp-master/atp_matches_"+str(year_)+".csv")
        tar_stat = stats[stats['tourney_name']==Name]
        if len(tar_stat) == 0:
            tar_stat = stats[stats['tourney_id']==(str(year_)+"-"+str(tourid))]
        tar_stat['id'] = tar_stat.index - min(tar_stat.index) + 1
        print(Name)

        for item in tar_stat.itertuples():
            add_info = [item.winner_ht,item.winner_ioc,item.winner_age,item.loser_ht,item.loser_ioc,item.loser_age]
            p1_id,p2_id = getplayerinfo(item.winner_name,item.loser_name,cursor,add_info)
            print(item.winner_name,item.loser_name)
            print([p1_id, p2_id, item.id, item.score, tourid, year_, item.round])
            cursor.execute("Insert result VALUES(%s,%s,%s,%s,%s,%s,%s)",
                           (p1_id, p2_id, item.id, item.score, tourid, year_, item.round))
            if item.score == 'W/O':
                continue
            else:
                if np.isnan(item.w_ace):
                    print("ATTENTION! LACK OF DATA! "+str(tournamentid)+" "+str(item.id))
                    continue
                cursor.execute(
                    "INSERT Match_stats VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (tournamentid, item.id, p1_id, item.w_ace, item.w_df, item.w_svpt, item.w_svpt-item.w_1stIn, item.w_1stWon, item.w_2ndWon, item.w_bpFaced, item.l_bpFaced-item.l_bpSaved, p2_id, item.l_ace, item.l_df, item.l_svpt, item.l_svpt-item.l_1stIn, item.l_1stWon, item.l_2ndWon, item.l_bpFaced, item.w_bpFaced-item.w_bpSaved, None, None, None, None, None, None, None, None, None, None, None, None))
                if np.isnan(item.winner_rank) or np.isnan(item.loser_rank):
                    if np.isnan(item.winner_rank):
                        cursor.execute("INSERT participator_list VALUES(%s,%s,%s)", (p1_id, tournamentid, None))
                    elif np.isnan(item.loser_rank):
                        cursor.execute("INSERT participator_list VALUES(%s,%s,%s)", (p2_id, tournamentid, None))
                else:
                    cursor.execute("INSERT participator_list VALUES(%s,%s,%s)", (p1_id, tournamentid, item.winner_rank))
                    cursor.execute("INSERT participator_list VALUES(%s,%s,%s)", (p2_id, tournamentid, item.loser_rank))
        connect.commit()


def select_qualify(year_):
    connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()

    with open("tour_list_a_" + str(year_) + ".txt", 'r') as f:
        content = f.readlines()
        f.close()

    url = "https://www.ultimatetennisstatistics.com/tournamentEventsTable?current=1&rowCount=-1&sort%5Bdate%5D=desc&searchPhrase=&season=" + str(
        year_) + "&level=&surface=&indoor=&speed=&tournamentId=&_=1677723790073"
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'

    }

    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    # bs = BeautifulSoup(html, "html.parser")

    info_ = json.loads(html)['rows']

    for item in content:
        info = tuple(eval(item))
        if info[3] != 'Qualify':
            continue
        Name = info[2][:-2]
        if Name == 'Toronto' or Name == 'Montreal':
            Name = 'Canada Masters'
        elif info[3] == 'ATP1000':
            Name = Name + ' Masters'
        elif Name == 'French Open':
            Name = 'Roland Garros'
        elif Name == 'Washington DC':
            Name = 'Washington'
        elif Name == "'s-Hertogenbosch":
            Name = 's Hertogenbosch'
        elif Name == 'St Petersburg':
            Name = 'St. Petersburg'
        elif Name == "London / Queen's Club":
            Name = "Queen's Club"
        elif Name == "Vina del Mar":
            Name = 'Santiago'
        elif Name == 'London':
            continue

        tournamentid = int(info[0])
        type = info[4]
        if Name == 'Tour Finals':
            level = 'Tour Final'
        else:
            level = info[3]
        seq = int(info[5]) - 1
        tourid = tournamentid // 100
        speed = get_speed((tournamentid - 99 * 10 ** len(str(tournamentid))) // 100, info_)
        date = datetime.datetime.strptime(info[7], '%Y-%m-%d')

        cursor.execute("Insert Tournament Values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                       (tournamentid // 100, year_, Name+' Q', level, type, tournamentid, None, seq, speed, date))
        stats = pd.read_csv(
            "C:/Users/math_conservatism/PycharmProjects/pythonProject/project/tennis_atp-master/atp_matches_qual_chall_" + str(
                year_) + ".csv")
        tar_stat = stats[stats['tourney_name'] == Name]
        if len(tar_stat) == 0:
            tar_stat = stats[stats['tourney_id'] == (str(year_) + "-" + str(tourid)[2:])]
        if len(tar_stat) == 0:
            tar_stat = stats[stats['tourney_name'] == Name+" Masters"]
        tar_stat['id'] = tar_stat.index - min(tar_stat.index) + 1
        print(Name)

        for item in tar_stat.itertuples():
            add_info = [item.winner_ht, item.winner_ioc, item.winner_age, item.loser_ht, item.loser_ioc, item.loser_age]
            p1_id, p2_id = getplayerinfo(item.winner_name, item.loser_name, cursor, add_info)
            print(item.winner_name, item.loser_name)
            print([p1_id, p2_id, item.id, item.score, tourid, year_, item.round])
            if item.score == 'W/O' or pd.isna(item.score):
                cursor.execute("Insert result VALUES(%s,%s,%s,%s,%s,%s,%s)",
                           (p1_id, p2_id, item.id, 'W/O', tourid, year_, item.round))
                continue
            else:
                cursor.execute("Insert result VALUES(%s,%s,%s,%s,%s,%s,%s)",
                               (p1_id, p2_id, item.id, item.score, tourid, year_, item.round))
                if np.isnan(item.w_ace):
                    print("ATTENTION! LACK OF DATA! " + str(tournamentid) + " " + str(item.id))
                    continue
                cursor.execute(
                    "INSERT Match_stats VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (tournamentid, item.id, p1_id, item.w_ace, item.w_df, item.w_svpt, item.w_svpt - item.w_1stIn,
                     item.w_1stWon, item.w_2ndWon, item.w_bpFaced, item.l_bpFaced - item.l_bpSaved, p2_id, item.l_ace,
                     item.l_df, item.l_svpt, item.l_svpt - item.l_1stIn, item.l_1stWon, item.l_2ndWon, item.l_bpFaced,
                     item.w_bpFaced - item.w_bpSaved, None, None, None, None, None, None, None, None, None, None, None,
                     None))
                if np.isnan(item.winner_rank) or np.isnan(item.loser_rank):
                    if np.isnan(item.winner_rank):
                        cursor.execute("INSERT participator_list VALUES(%s,%s,%s)", (p1_id, tournamentid, None))
                    elif np.isnan(item.loser_rank):
                        cursor.execute("INSERT participator_list VALUES(%s,%s,%s)", (p2_id, tournamentid, None))
                else:
                    cursor.execute("INSERT participator_list VALUES(%s,%s,%s)", (p1_id, tournamentid, item.winner_rank))
                    cursor.execute("INSERT participator_list VALUES(%s,%s,%s)", (p2_id, tournamentid, item.loser_rank))
        connect.commit()

#get_tour_list(2021)
select_qualify(2021)
#select_info(2000)

