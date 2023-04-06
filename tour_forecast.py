import match_result
import urllib.request
import datetime
from bs4 import BeautifulSoup
import re
import pymssql
import json


def update_tour(eid,tour,type,file_name):

    now = datetime.datetime.now()+datetime.timedelta(days=0)
    date_str = now.strftime('%Y-%m-%d')
    url = "https://www.rank-tennis.com/zh/result/" + date_str

    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'

    }
    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")

    temp = bs.find_all('div', attrs={'class': 'cResultTour'})
    print(eid)
    tbs = []
    for item in temp:
        try:
            str(item).index('cResultTour'+eid)
            tbs = item
            break
        except:
            continue
        # bs = bs.find_all('div', attrs={'class': 'cResultTour', 'data-eid': tourid})[0]
    if tbs==[]:
        return [],""

    a = tbs.find_all('div', class_='cResultMatch')
    pat = re.compile(r'Q\d')
    pattern = re.compile("cResultPlayer(\w+)")
    oddpat = re.compile('data-odds="(\d+.\d+)-(\d+.\d+)"')

    b = []
    for item in a:
        if item.select("div[class='cResultMatchGender']")[0].text == "男单" and re.match(pat, item.select(
                "div[class='cResultMatchRound']")[0].text) == None:
            b.append(item)

    id = []
    odd_list = []

    for item in b:
        u_name = re.findall(pattern, str(item))[0:2]
        if len(u_name)!=2:
            continue
        id.append(u_name[0])
        id.append(u_name[1])
        try:
            odd = re.findall(oddpat,str(item))[0]
        except:
            odd = ('N/A', 'N/A')
        odd_list.append(odd[0])
        odd_list.append(odd[1])
    print(id)


    connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='atp-tennis', charset='utf8')
    cursor = connect.cursor()
    #print(id)

    url = "https://www.ultimatetennisstatistics.com/inProgressEventsTable?current=1&rowCount=-1&searchPhrase=&_=1665210077043"

    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    # bs = BeautifulSoup(html, "html.parser")

    info = json.loads(html)['rows']
    tournament_speed=-1
    for item in info:
        if item['name']==tour:
            try:
                tournament_speed=item['speed']
            except:
                tournament_speed=-1
            break

    if tournament_speed!=-1:
        cursor.execute("select speed from Tournament where Tournament=%s and [year]=%s", (eid,now.year))
        temp_speed = cursor.fetchone()
        if temp_speed != None:
            temp_speed = temp_speed[0]
        else:
            temp_speed = tournament_speed
        if temp_speed != tournament_speed:
            if abs(temp_speed-tournament_speed)>=3:
                tournament_speed = 0.5 * temp_speed + tournament_speed * 0.5
                cursor.execute("update Tournament set speed=%s where Tournament=%s and [year]=%s", (tournament_speed,eid,now.year))
                cursor.execute("update Tournament set speed=%s where Tournament=%s and [year]=%s",
                               (tournament_speed, (99*10**(len(str(int(eid)))))+int(eid), now.year))
                print("change tournament speed from %s to %s",(temp_speed, tournament_speed))

    player_name=[]
    odd_renew_list=[]
    l_mark=0
    for i in range(0,len(id)):
        cursor.execute("select Name from Player where [R-id]=%s",id[i])
        #print(id[i])
        try:
            name = cursor.fetchone()[0].strip()
        except:
            name = None
        if name and l_mark==0:
            player_name.append(name)
            odd_renew_list.append(odd_list.pop(0))
        else:
            if i%2==0:
                l_mark=1
                odd_list.pop(0)
                odd_list.pop(0)
            else:
                if l_mark==0:
                    player_name.pop()
                    odd_renew_list.pop()
        if i%2==1:
            l_mark=0

    speed=0
    sum=0
    cursor.execute("select speed,[year] from Tournament where Tournament=%s order by [year] desc",eid)
    tour_info=cursor.fetchall()
    count = 0
    if tour_info==[]:
        speed=input("input the speed")
    else:
        for item in tour_info:
            if item[1]==now.year:
                speed=item[0]
            else:
                if count>=3:
                    break
                else:
                    sum = sum + item[0]
                    count = count + 1
        if speed==0:
            speed=sum/count
    matchresult = ""

    connect.commit()
    connect.close()
    print(speed)
    for i in range(0, len(player_name), 2):
        print(player_name[i], ' vs ', player_name[i + 1])
        wp,result_str = match_result.start(player_name[i], player_name[i + 1], type, speed, 2, None, None, 0)
        idx = result_str.index("\n")
        matchresult = matchresult + result_str[0:idx+1]+ "\n" +odd_renew_list[i]+"    "+odd_renew_list[i+1]+ "\n" + result_str[idx+1:] + "\n\n\n"


    with open(file_name, 'r', encoding="utf-8") as f:
        content = f.readlines()

    if content:
        con = content[3]
    else:
        con = ""
    if matchresult != "":
        con = con + ("**" + tour + "**\n\n")
    con = con + matchresult

    return id,con

def forecast(id,speed,type):
    while len(id)>1:
        nid = []
        for i in range(0,len(id),2):
            print(id[i],' vs ', id[i + 1])
            result=match_result.start(id[i],id[i+1],type,speed,3, None, None,0)
            if result == -1:
                result = match_result.start(id[i], id[i+1], type, speed, 3, None, None, 1)
                print(result)
                winner = input("select one ")
                nid.append(id[i+int(winner)])
                print(id[i+int(winner)]+'\n')
            else:
                print(result)
                winner = input("select one ")
                nid.append(id[i+int(winner)])
                print(id[i + int(winner)]+'\n')
        id = nid

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


if __name__ == '__main__':
    with open("tour_list_a.txt",'r',encoding='utf-8') as f:
        line=f.readlines()
        f.close()
    date_now = datetime.datetime.now()+datetime.timedelta(days=0)
    date_now = datetime.date(date_now.year, date_now.month, date_now.day)

    type_list = []
    eid_list = []
    tournament_list = []
    ahead_check = 0

    for item in line:
        info = tuple(eval(item))
        if info[3]!='Qualify':
            date_start = info[7]
            date_start = datetime.date(int(date_start[0:4]),int(date_start[5:7]),int(date_start[8:10]))
            date_end = info[8]
            date_end = datetime.date(int(date_end[0:4]), int(date_end[5:7]), int(date_end[8:10]))
            if tournament_list == []:
                tar_end = date_end
                tar_start = date_start
            #print(tournament_list)

            if date_now>date_end+datetime.timedelta(days=1):
                continue

            if date_now>=min(tar_start,date_start)-datetime.timedelta(days=1):
                if date_now==min(tar_start,date_start)-datetime.timedelta(days=1) and ahead_check==0:
                    ahead_check = 1
                elif date_now>min(tar_start,date_start)-datetime.timedelta(days=1):
                    ahead_check = 2

                if abs((date_end-tar_end).days)<=1 and date_now<=max(tar_end,date_end):

                    type_list.append(info[4])
                    eid_list.append(convert_GS(str(int(info[0])//100)))
                    tour_name = info[2]
                    if info[3]=='ATP1000':
                        if info[2][-7:]!='Masters':
                            tour_name = info[2]+' Masters'
                    tournament_list.append(tour_name)

    if ahead_check==1:
        tournament_list = []

    file_name = ""
    if tournament_list == None:
        exit(0)
    for item in tournament_list:
        file_name = file_name + item + " & "

    title = file_name[:-3]
    #file_name = "C:/Users/math_conservatism/Documents/"+title+".md"
    file_name = "D:/Git/learnskill/Forecast Result/"+title+".md"
    print(file_name)

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            content = f.readlines()
    except:
        with open(file_name, "w", encoding="utf-8") as f:
            content = []
    Day = 0
    if content:
        pat_day = re.compile("Day (\d+)")
        Day = re.findall(pat_day, content[2])[0]

    fore_res = '# ' + title + "\n\n" + "#### Day " + str(int(Day) + 1) + "\n\n"

    for i in range(0,len(tournament_list)):
        print(tournament_list[i])
        id, con = update_tour(eid_list[i], tournament_list[i], type_list[i], file_name)
        fore_res = fore_res + con
    for item in content[1:]:
        fore_res = fore_res + item

    with open(file_name, "w", encoding="utf-8") as f:
        for item in fore_res:
            f.write(item)
        f.close()