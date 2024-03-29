import urllib.request
import datetime
from bs4 import BeautifulSoup
import re
import pymssql

def process_result(score_str, sgn):
    pat = re.compile('(\d)[(\d+)]*-(\d)[(\d+)]*')
    res = re.findall(pat, score_str)
    set_1, set_2 = 0, 0
    for item in res:
        if item[0] > item[1]:
            if (item[0] == '6' and item[1] <= '4') or item[0] == '7':
                set_1 = set_1 + 1
        elif item[0] < item[1]:
            if (item[1] == '6' and item[0] <= '4') or item[1] == '7':
                set_2 = set_2 + 1
    flag = set_1 - set_2
    if sgn == 1:
        result = str(set_2) + ":" + str(set_1)
    else:
        result = str(set_1) + ":" + str(set_2)
    if flag <= 0:
        if sgn == 0:
            result = result + ' (RET)'
        else:
            result = "(RET) " + result

    return result

def convert_id(eid):
    if eid=='AO':
        return '580'
    elif eid=='RG':
        return '520'
    elif eid=='WC':
        return '540'
    elif eid=='UO':
        return '560'
    else:
        return eid


def update_record(eid, content, season):
    now = datetime.datetime.now() + datetime.timedelta(days=global_days)
    date_str = now.strftime('%Y-%m-%d')
    url = "https://www.live-tennis.cn/zh/result/" + date_str

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
            if 'A' < eid and eid < 'Z':
                str(item).index('cResultTour' + eid)
            else:
                str(item).index('cResultTour2' + eid)
            tbs = item
            break
        except:
            continue
        # bs = bs.find_all('div', attrs={'class': 'cResultTour', 'data-eid': tourid})[0]
    if tbs == []:
        return content
    a = tbs.find_all('div', class_='cResultMatch')
    pat = re.compile(r'Q\d')
    pattern = re.compile("cResultPlayer(\w+)")

    b = []
    for item in a:
        if item.select("div[class='cResultMatchGender']")[0].text == "男单" and re.match(pat, item.select("div[class='cResultMatchRound']")[0].text) == None:
            b.append(item)

    id = []
    for item in b:
        u_name = re.findall(pattern, str(item))[0:2]
        if len(u_name) != 2:
            continue
        id.append(u_name[0])
        id.append(u_name[1])
    print(id)

    connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    eid = convert_id(eid)
    print(eid)


    for i in range(0, len(id), 2):
        cursor.execute("select Name, ID from Player where [R-id]=%s",id[i])
        player1 = cursor.fetchone()
        player1_id = player1[1]
        player1 = player1[0].strip()
        cursor.execute("select Name, ID from Player where [R-id]=%s", id[i+1])
        player2 = cursor.fetchone()
        #print(player1,player2)
        player2_id = player2[1]
        player2 = player2[0].strip()

        print((player1_id,player2_id,player1_id,player2_id,season))
        cursor.execute("select p1_id, result from result where ((p1_id=%s and p2_id=%s) or (p2_id=%s and p1_id=%s)) and tournament_id=%s and [year]=%s", (player1_id,player2_id,player1_id,player2_id,eid,season))
        result = cursor.fetchone()
        # print(result)
        if result == None:
            continue

        if result[0] == player1_id:
            winner = 0
        else:
            winner = 1

        cursor.execute(
            "Update user_choice set correct = %s where correct is NULL and match_id is not NULL and ((winner=%s and loser=%s) or (loser=%s and winner=%s))",
            (result[0], player1_id, player2_id, player1_id, player2_id))

        odd_pat = re.compile('(\d+.\d+)\s+(\d+.\d+)')
        pro_pat = re.compile('(0[.]\d+)')

        if result[1] != 'W/O':
            result = process_result(result[1].strip(),winner)
        else:
            result = result[1]

        for i in range(len(content)):
            if content[i] == (player1+"  vs  "+player2+'\n'):
                info_ = player1 + "  " + result + "  " + player2
                odd = re.findall(odd_pat,content[i+2])
                if odd != []:
                    s1 = float(odd[0][0])
                    s2 = float(odd[0][1])
                    if s1 == s2:
                        info_ = info_ + "    ➖"
                    elif (s1 > s2) != winner:
                        info_ = info_ + "    ❗"
                if content[i+5] == '\n':
                    info_ = info_
                else:
                    k = 4
                    while content[i+k] != '\n':
                        k = k+1
                    pro_1, pro_2 = 0, 0
                    if k == 8:
                        pro_1 = float(re.findall(pro_pat,content[i+4])[0])+float(re.findall(pro_pat,content[i+5])[0])
                        pro_2 = float(re.findall(pro_pat,content[i+6])[0])+float(re.findall(pro_pat,content[i+7])[0])
                    elif k == 10:
                        pro_1 = float(re.findall(pro_pat, content[i + 4])[0]) + float(
                            re.findall(pro_pat, content[i + 5])[0]) + float(
                            re.findall(pro_pat, content[i + 6])[0])
                        pro_2 = float(re.findall(pro_pat, content[i + 7])[0]) + float(
                            re.findall(pro_pat, content[i + 8])[0]) + float(
                            re.findall(pro_pat, content[i + 9])[0])

                    if abs(pro_1-pro_2)<0.001:
                        info_ = info_ + "    ❓"
                    elif (pro_1 > pro_2) == winner:
                        info_ = info_ + "    ❌"
                    else:
                        info_ = info_ + "    ✔"

                content[i] = info_+'\n'

                break
    connect.commit()
    connect.close()
    return content

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

def get_file(line,date_now):
    type_list = []
    eid_list = []
    tournament_list = []
    ahead_check = 0
    index = 0
    loc = -1
    for item in line:
        info = tuple(eval(item))
        index = index + 1
        if info[3] != 'Qualify':
            date_start = info[7]
            date_start = datetime.date(int(date_start[0:4]), int(date_start[5:7]), int(date_start[8:10]))
            date_end = info[8]
            date_end = datetime.date(int(date_end[0:4]), int(date_end[5:7]), int(date_end[8:10]))
            if tournament_list == []:
                tar_end = date_end
                tar_start = date_start

            if date_now > date_end + datetime.timedelta(days=1):
                continue

            if date_now >= min(tar_start, date_start) - datetime.timedelta(days=1):
                if date_now == min(tar_start, date_start) - datetime.timedelta(days=1) and ahead_check == 0:
                    ahead_check = 1
                elif date_now > min(tar_start, date_start) - datetime.timedelta(days=1):
                    ahead_check = 2

                if abs((date_end - tar_end).days) <= 1 and date_now <= max(tar_end, date_end):

                    type_list.append(info[4])
                    eid_list.append(convert_GS(str(int(info[0]) // 100)))
                    tour_name = info[2]
                    if info[3] == 'ATP1000':
                        if info[2][-7:] != 'Masters':
                            tour_name = info[2] + ' Masters'
                    tournament_list.append(tour_name)
                    loc = index

    if ahead_check == 1:
        tournament_list = []

    file_name = ""
    if tournament_list == []:
        return 'success', tournament_list, type_list, eid_list, loc
    for item in tournament_list:
        file_name = file_name + item + " & "

    title = file_name[:-3]
    file_name = "D:/learnskill/Forecast Result/" + title + ".md"

    return file_name, tournament_list, type_list, eid_list, loc

def comment_result(file_name,tournament_list,eid_list,season):
    with open(file_name, "r", encoding="utf-8") as f:
        content = f.readlines()

    for i in range(0, len(tournament_list)):
        print(tournament_list[i])
        content = update_record(eid_list[i], content, season)

        if i == len(tournament_list)-1:
            pat_GT = re.compile('✔')
            pat_GF = re.compile('❌')
            pat_GN = re.compile('❓')
            pat_GL = re.compile('lack')
            pat_BF = re.compile('❗')
            pat_BN = re.compile('➖')
            pat_TN = re.compile('[a-z]\s+❗\s+✔')
            pat_FP = re.compile('[a-z]\s+❌')
            GT = len(re.findall(pat_GT, str(content)))
            GF = len(re.findall(pat_GF, str(content)))
            GN = len(re.findall(pat_GN, str(content)))
            GL = len(re.findall(pat_GL, str(content)))
            BF = len(re.findall(pat_BF, str(content)))
            BN = len(re.findall(pat_BN, str(content)))
            TN = len(re.findall(pat_TN, str(content)))
            FP = len(re.findall(pat_FP, str(content)))

            total_match = GT + GF + GN + GL
            G_rate = GT / (GT + GF if GT+GF != 0 else 0.1)
            B_rate = 1 - BF / (total_match - BN)
            G_rate = round(G_rate * 100, 2)
            B_rate = round(B_rate * 100, 2)

            iloc = 0
            profit = 0
            for _ in range(TN):
                for z in range(iloc,len(content)):
                    if re.search(pat_TN,content[z]):
                        iloc = z + 1

                        bet = content[iloc+1].split(' ')
                        bet_1, bet_2 = bet[0].strip(), bet[-1][:-1].strip()
                        bet_1, bet_2 = float(bet_1), float(bet_2)
                        profit = profit + max(bet_1,bet_2)-1
                        break

            if TN + FP == 0:
                profit = 0.00
            else:
                profit = round((profit - FP)/(TN + FP)*100,2)

            summary = str(TN)+':'+str(FP)+'    accuracy: '+str(G_rate)+'%    base: '+str(B_rate)+'%    profit: '+ str(profit)+'%\n'
            content.append(summary)

        with open(file_name, "w", encoding="utf-8") as f:
            for item in content:
                f.write(item)
            f.close()


def main():
    global global_days
    global_days = -1
    with open("tour_list_a.txt", 'r', encoding='utf-8') as f:
        line = f.readlines()
        f.close()
    date_now = datetime.datetime.now() + datetime.timedelta(days=global_days)
    date_now = datetime.date(date_now.year, date_now.month, date_now.day)
    season = eval(line[0])[1]

    index = 0
    loc = 0
    while loc != -1:
        file_name,tournament_list,type_list,eid_list,loc = get_file(line[index:],date_now)
        if file_name == 'success':
            connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='atp-tennis',
                                      charset='utf8')
            cursor = connect.cursor()
            date = date_now.strftime('%Y-%m-%d')
            cursor.execute(
                "select user_id, Count(*) from user_choice where convert(varchar(100), date, 23)=%s and winner=correct group by user_id",
                date)

            correct = cursor.fetchall()
            print(correct)
            cursor.execute("update user_info set DayScore = 0")
            if correct:
                for item in correct:
                    cursor.execute("update user_info set DayScore=%s where Id=%s", (item[1], item[0]))
                    cursor.execute("update user_info set YearScore=YearScore+%s where Id=%s", (item[1], item[0]))
                    if date_now.weekday() != 0:
                        cursor.execute("update user_info set WeekScore=WeekScore+%s where Id=%s", (item[1], item[0]))
                    else:
                        cursor.execute("update user_info set WeekScore=%s where Id=%s", (item[1], item[0]))
            connect.commit()
            return file_name
        index = index + loc
        if loc == -1:
            break
        comment_result(file_name,tournament_list,eid_list,season)

    return 'success'


if __name__ == '__main__':
    main()
