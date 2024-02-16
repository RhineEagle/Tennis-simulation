import datetime
import re
import os
import urllib.request
from urllib.request import urlretrieve
import urllib.parse
from bs4 import BeautifulSoup
import pymssql
import random
import time
import json
import math
import pandas as pd
import numpy as np
import requests
from retrying import retry
import pycountry as pc
import pytz

def getplayerinfo(name1,name2,cursor,u_name,start_date):
    lan1 = "select top 1 [C-Name],ID from Player Where [R-ID]=%s"
    lan2 = "select top 1 [C-Name],ID from Player Where [R-ID]=%s"

    cursor.execute(lan1,name1)
    info1 = cursor.fetchone()
    if info1==None:
        getabnormalplayer(name1,cursor,u_name[0],start_date)
        cursor.execute(lan1, name1)
        info1 = cursor.fetchone()
    if isContainChinese(info1[0])==False and isContainChinese(u_name[0])==True:
        cursor.execute("update Player set [C-Name] = %s where ID = %s",(u_name[0],info1[1]))
    cursor.execute(lan2,name2)
    info2 = cursor.fetchone()
    if info2==None:
        getabnormalplayer(name2, cursor, u_name[1],start_date)
        cursor.execute(lan2, name2)
        info2 = cursor.fetchone()
    if isContainChinese(info2[0])==False and isContainChinese(u_name[1])==True:
        cursor.execute("update Player set [C-Name] = %s where ID = %s",(u_name[1],info2[1]))
    return info1,info2

def draw_loc(tour,yy,lev):
    if lev == 'Qualify':
        tour = tour % (10 ** (len(str(tour))-2))
    url = "https://www.atptour.com/en/scores/archive/auckland/{}/{}/draws".format(tour//100,yy)
    if lev == 'Qualify':
        url = url + '?matchType=QualifierSingles'
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
        # "sec-ch-ua": '"Chromium";v ="92","Not A;Brand";v="99","Google Chrome";v="92"',
        # "Cookie": "_ga = GA1.2.324355889.1621857694;__gads=ID=8cfa7d12bbca2f6d-22ba21761bc80082:T=1621857691:RT = 1621857691:S=ALNI_MYJRBxeLS0iZna4gzE_F2cbdf8ZDA;gid = GA1.2.1014988429.1630369661"
    }
    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    bs = bs.find_all('div', class_='draw-round-1')[0]
    rid_list = []
    for item in bs.find_all('div', class_='profile'):
        src = item.find_all('img')[0]['src']
        rid = src[-4:]
        if '/0' in rid:
            rid = 'Bye'
        rid_list.append(rid)
    return rid_list

@retry(stop_max_attempt_number=3, wait_fixed=3000)
def execute_rank(tour,yy,date,cursor,seed,lev):
    cursor.execute(
        "select distinct r.p1_id, p.Name, p.[R-ID] from result r join Player p on r.p1_id = p.ID where tournament_id=%s and [Year]=%s and NOT EXISTS (select 1 from participator_list pl where pl.id=r.p1_id and tour_id=%s) union select distinct r.p2_id, p.Name, p.[R-ID] from result r join Player p on r.p2_id = p.ID where tournament_id=%s and [Year]=%s and NOT EXISTS (select 1 from participator_list pl where pl.id=r.p2_id and tour_id=%s)",
        (tour // 100, yy, tour, tour // 100, yy, tour))
    player_list = pd.DataFrame(columns=['ID','Name', 'RID'])
    row=cursor.fetchall()
    for item in row:
        player_list.loc[len(player_list)] = item
    if len(player_list)==0:
        return []
    player_list = player_list.merge(seed,how='left',on=['RID'])
    loc_tour = ['Qualify', 'ATP250', 'ATP500', 'ATP1000', 'Grand Slam']
    if lev in loc_tour:
        rid_list = draw_loc(tour,yy,lev)

    url = 'https://www.rank-tennis.com/en/history/official/query'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'
    }
    data = {
            'status': 'ok',
            'sd': 's',
            'type': 'atp',
            'date': str(date)
    }
    data = urllib.parse.urlencode(data).encode('utf-8')

    request = urllib.request.Request(url=url, data=data, headers=headers)
    response = urllib.request.urlopen(request,timeout=20)

    # 获取响应的数据
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    content=bs.find_all('table',id='iOfficialDetailTable')[0].select("td")
    rank_info=[]
    abnormal=[]
    player_list = player_list.drop_duplicates()
    print(player_list)
    for item in player_list.values:
        name=item[1].strip()
        name.replace("-"," ")
        pat=re.compile(name,re.I)
        cursor.execute("Update Player set Last_Appearance = %s where ID = %s",(date,item[0]))
        cursor.execute("select [R-ID] from Player where ID = %s",item[0])
        rid = cursor.fetchone()[0]
        if lev in loc_tour:
            loc = rid_list.index(rid)+1
        else:
            loc = None
        print(yy,item[0])
        for i in range(0,len(content)):
            ts=content[i].text.strip()
            ts=ts.replace("-"," ")
            if re.search(pat,ts):
                rank_info.append((item[0],tour,content[i-2].text.strip(),item[3],loc))
                print((item[0],tour,content[i-2].text.strip(),item[3],loc))
                break
            if i==len(content)-1:
                print(str(name) +" need use Chinese Name to be added.")
                abnormal.append((item[0],tour,date,item[3],loc))
    for item in rank_info:
        cursor.execute("Insert participator_list Values(%s,%s,%s,%s,%s,%s)",(item[0],item[1],item[2],item[3],None,item[4]))
    if abnormal!=[]:
        a_abnormal=[]
        for item in abnormal:
            a_abnormal=execute_ch(item,a_abnormal,cursor)
        print(a_abnormal)

def execute_ch(player,abnormal,cursor):
    url = 'https://www.rank-tennis.com/zh/history/official/query'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'
    }

    data = {
            'status': 'ok',
            'sd': 's',
            'type': 'atp',
            'date': str(player[2])
    }
    data = urllib.parse.urlencode(data).encode('utf-8')

    request = urllib.request.Request(url=url, data=data, headers=headers)
    response = urllib.request.urlopen(request)

    # 获取响应的数据
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    content=bs.find_all('table',id='iOfficialDetailTable')[0].select("td")
    cursor.execute("select top 1 [C-Name] from player where ID=%s",(player[0]))
    name=cursor.fetchone()[0].strip().encode('latin1').decode('gbk')
    pat=re.compile(name)
    for i in range(0,len(content)):
        ts=content[i].text.strip()
        if re.search(pat,ts):
            cursor.execute("Insert participator_list Values(%s,%s,%s,%s,%s,%s)", (player[0], player[1], content[i-2].text.strip(), player[3], None, player[4]))
            print((player[0], player[1], content[i-2].text.strip(), player[3], player[4]))
            break
        if i==len(content)-1:
            print(str(name) +" need mannual addition.")
            cursor.execute("Insert participator_list Values(%s,%s,%s,%s,%s,%s)",
                           (player[0], player[1], None, player[3], None, player[4]))
            abnormal.append((str(name), player[0], player[1], player[2]))
    return abnormal

def isContainChinese(s):
    for c in s:
        if ('一' <= c <= '龥'):
            return True
    return False

def download_pic(url, name, path_detail):
    local_path = r'C:/Users/math_conservatism/PycharmProjects/pythonProject/SQL/static/Player_Photo_'+path_detail
    if (not os.path.exists(local_path)):
        # 存储路径不存在优先创建路径
        os.makedirs(local_path)
    save_path = local_path + '/' + name
    print(url)
    print(save_path)
    opener = urllib.request.build_opener()
    # 构建请求头列表每次随机选择一个
    ua_list = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
               'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36 SE 2.X MetaSr 1.0'
               ]
    opener.addheaders = [('User-Agent', random.choice(ua_list))]
    urllib.request.install_opener(opener)
    if os.path.exists(save_path):
        return 0
    try:
        urlretrieve(url, save_path)
        print('{} saved successfully'.format(name))
        time.sleep(0.1)
    except:
        print('{} failed saving'.format(name))

def download_pic_trophy(url, name,
                 local_path=r'C:\Users\math_conservatism\PycharmProjects\pythonProject\SQL\static\trophy'):
    '''
    单个图片下载函数：
    url:图片对应的url链接
    name:图片存储在本地的名称和格式
    default：自动跳转到默认链接的网页内容
    local_path：存储图片的文件夹，默认为程序所在路径
    '''
    if (not os.path.exists(local_path)):
        # 存储路径不存在优先创建路径
        os.makedirs(local_path)
    save_path = local_path + '/' + name
    if os.path.exists(save_path):
        return 0
    # try:
    print(url)
    # if(response.text==default):
    #     #判断是否跳转到默认链接
    #     print('{} jumps to defaut web'.format(url))
    #     #以下可以加入默认链接的处理方式，比如USA的国旗不存在的话用默认国旗代替，或者也可以选择不加
    # else:
    # #urlretrieve直接用于下载目标url的内容
    opener = urllib.request.build_opener()
    # 构建请求头列表每次随机选择一个
    ua_list = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
               'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36 SE 2.X MetaSr 1.0'
               ]
    opener.addheaders = [('User-Agent', random.choice(ua_list))]
    urllib.request.install_opener(opener)
    urlretrieve(url, save_path)
    print('{} saved successfully'.format(name))


def translate(word):
    # 有道词典 api
    url = 'https://aidemo.youdao.com/trans'
    # 传输的参数，其中 i 为需要翻译的内容
    key = {
        'q': word,
        'from': "Auto",
        'to': "Auto"
    }
    # key 这个字典为发送给有道词典服务器的内容
    response = requests.post(url, data=key)
    # 判断服务器是否相应成功
    if response.status_code == 200:
        # 然后相应的结果
        result = json.loads(response.text)
        return result['translation'][0]
    else:
        print(response.status_code)
        # 相应失败就返回空
        return word

def convert_GS(eid):
    if eid=='580':
        return 'AO'
    elif eid=='520':
        return 'RG'
    elif eid=='540':
        return 'WC'
    elif eid=='560':
        return 'UO'
    elif eid=='8359':
        if datetime.datetime.now().month == 2:
            return 'DC-QLS'
        else:
            return 'DC'
    else:
        if len(eid)==3:
            eid='0'+eid
        return eid

def convert_num(eid):
    if eid == 'AO':
        return '580'
    elif eid == 'RG':
        return '520'
    elif eid == 'WC':
        return '540'
    elif eid == 'UO':
        return '560'
    else:
        if eid[0] == '0':
            eid = eid[1:]
    return eid

def process_result(res):
    if res == 'W/O':
        return [0, 0]
    pat = re.compile('(\d)[(\d+)]*-(\d)[(\d+)]*')
    res = re.findall(pat, res)
    set1, set2 = 0, 0
    for item in res:
        if item[0] > item[1]:
            if (item[0] == '6' and item[1] <= '4') or item[0] == '7':
                set1 = set1 + 1
        elif item[0] < item[1]:
            if (item[1] == '6' and item[0] <= '4') or item[1] == '7':
                set2 = set2 + 1
    return [set1, set2]

def process_result_game(score_str):
    if score_str == 'W/O':
        return [0, 0]
    pat = re.compile('(\d)[(\d+)]*-(\d)[(\d+)]*')
    res = re.findall(pat, score_str)
    score_1, score_2 = 0, 0
    num = 0
    for item in res:
        if item[0] > item[1]:
            if (item[0] == '6' and item[1] <= '4') or item[0] == '7':
                score_1 = score_1 + 5
                num = num + 1
            score_1 = score_1 + min(int(item[0]) - 3, 3) - (int(item[0]) + int(item[1])) / 10
            score_2 = score_2 + max(int(item[1]) - 3, 0)
        elif item[0] < item[1]:
            if (item[1] == '6' and item[0] <= '4') or item[1] == '7':
                score_2 = score_2 + 5
                num = num + 1
            score_1 = score_1 + max(int(item[0]) - 3, 0) - (int(item[0]) + int(item[1])) / 10
            score_2 = score_2 + min(int(item[1]) - 3, 3)
    num = max(1, num)
    score_1, score_2 = score_1 / num, score_2 / num
    return [score_1, score_2]

def cal_perf(tour, ID, cursor):
    cursor.execute(
        "select rank,'W' r,match_id,result from Tournament t join result r on t.Tournament=r.tournament_id and t.year=r.year and p1_id = %s join Participator_list p on t.ID = p.tour_id and p.id = r.p2_id where t.ID=%s\
        union\
        select rank,'L' r,match_id,result from Tournament t join result r on t.Tournament=r.tournament_id and t.year=r.year and p2_id = %s join Participator_list p on t.ID = p.tour_id and p.id = r.p1_id where t.ID=%s\
        order by match_id",
        (ID, tour, ID, tour))
    diff = cursor.fetchall()
    diff = pd.DataFrame(diff, columns=['rank', 'Result', 'mid', 'score'])
    W_match = diff[diff['Result'] == 'W']
    L_match = diff[diff['Result'] == 'L']
    W_score = W_match['score'].apply(lambda x: process_result_game(x)[0]) / (W_match['rank'] // 5 + 1)
    L_score = L_match['score'].apply(lambda x: process_result_game(x)[1]) / (L_match['rank'] // 5 + 1)
    perform_ = W_score.sum() + L_score.sum()
    perform_ = round(float(perform_), 2)

    return perform_

def tour_official_player(cursor,playername):

    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'
    }
    new_url = "https://www.atptour.com/en/-/www/players/hero/{}?v=1".format(playername.lower())
    req = urllib.request.Request(new_url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    overview = json.loads(html)

    height = overview['HeightCm']

    birth = overview['BirthDate']
    bd_pat = re.compile('(\d{4}-\d{2}-\d{2})')
    birthday = re.findall(bd_pat, birth)[0]
    birthday = datetime.datetime.strptime(birthday, '%Y-%m-%d')

    try:
        country_code = overview['NatlId']
        country_code = './static/country_flag/' + country_code + '.svg'
        cursor.execute("select top 1 country from country where country_code=%s", country_code)
        country = cursor.fetchone()[0]
    except:
        country = 'Unknown'

    Name = overview['FirstName'] + ' ' + overview['LastName']

    return Name,country,birthday,height

def getabnormalplayer(playername,cursor,u_name,start_date):
    # use player's name to get id
    try:
        Name, country, birthday, height = tour_official_player(cursor, playername)
    except:
        Name = u_name

    rid = playername

    Player=Name.replace(" ","+")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'
    }

    url = "https://www.ultimatetennisstatistics.com/playerProfile?name=" + Player + "&tab=profile"
    req = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(req)
    except:
        cursor.execute("select max(ID) from Player")
        id=cursor.fetchone()[0]
        if id >=80000:
            id=id+1
        else:
            id=80000
        if rid == None:
            cursor.execute("INSERT Player Values(%s,%s,%s,%s,%s,%s,%s,%s,%s)", (id, Name, None, 'Unknown', playername, u_name, start_date, None, start_date))
        else:
            cursor.execute("INSERT Player Values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                           (id, Name, height, country, playername, u_name, start_date, birthday, start_date))
        target_url_f = "https://www.rank-tennis.com/pic/pt/" + str(playername)
        target_url_h = "https://www.rank-tennis.com/pic/hs/" + str(playername)
        path_name = str(id).strip() + '.webp'
        download_pic(target_url_f, path_name, 'full')
        download_pic(target_url_h, path_name, 'head')
        print("Success to artificially insert " + Name)
        return 0

    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    info = bs.select("a[id='profilePill']", limit=1)[0]
    pat = re.compile('playerId=(\d+)')
    id = re.findall(pat, str(info))[0]
    time.sleep(1)

    if rid == None:
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
        birth_pat = re.compile('(\d+[-]\d+[-]\d+)')
        birthday,country, height = None, None, None
        for sample in info1:
            list = sample.find_all('tr')
            for item in list:
                if item.find("th").text == "Country":
                    country = item.find("span").text
                if item.find("th").text == "Height":
                    height = re.findall(pat, item.find("td").text)[0]
                if item.find("th").text == "Age":
                    age = re.findall(birth_pat, item.find("td").text)[0]
                    birthday = datetime.datetime.strptime(age,'%d-%m-%Y')

    # insert new information
    #print(id, Name, height, age, country, Rid, Cname, img, start_date)
    cursor.execute("INSERT Player Values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(id,Name,height,country,playername,u_name,start_date,birthday,start_date))
    target_url_f = "https://www.rank-tennis.com/pic/pt/" + str(playername)
    target_url_h = "https://www.rank-tennis.com/pic/hs/" + str(playername)
    path_name = str(id).strip() + '.webp'
    download_pic(target_url_f, path_name, 'full')
    download_pic(target_url_h, path_name, 'head')
    print("Successfully insert "+Name)
    #connect.commit()
    return 0

def GS_mid_convert(msid):
    mid = msid[2:]
    rd = int(mid[0])
    id = int(mid[1:])
    base = 0
    for i in range(7,rd,-1):
        base = base + 2**(7-i)
    id = str(id + base)
    while len(id)<3:
        id = '0'+id
    return msid[0:2]+id

@retry(stop_max_attempt_number=3, wait_fixed=3000)
def getdata_tour(id1,id2,player1,player2,eid,matchid,year,ID1,ID2,tournament_id,mid,winner,round_,KO,cursor,level,date,score_str):
    eid = convert_num(eid[1:])
    print(eid)
    if level == 'Grand Slam' or (tournament_id%100 in [99580,99520,99560,99540]):
        matchid = GS_mid_convert(matchid)
    if level == 'Davis Cup':
        return 1
    url = 'https://www.atptour.com/-/Hawkeye/MatchStats/Complete/'+str(year)+'/'+str(eid)+'/'+matchid
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'
    }
    req = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(req)
    if response.getcode() == 500:
        return -1

    html = response.read().decode('utf-8')
    text = json.loads(html)["Match"]

    winner = text['Winner']
    print(winner)
    sgn = text['PlayerTeam']['Player']["PlayerId"] == winner
    sgnout = winner == id1

    p1, p2 = [], []

    stats = text['PlayerTeam']['SetScores'][0]['Stats']
    servicestats = stats['ServiceStats']
    returnstats = stats['ReturnStats']
    ace = servicestats['Aces']['Number']
    p1.append(ace)
    df = servicestats['DoubleFaults']['Number']
    p1.append(df)
    fstsvc = servicestats['FirstServe']['Divisor']
    p1.append(fstsvc)
    sndsvc = fstsvc - servicestats['FirstServe']['Dividend']
    p1.append(sndsvc)
    fstw = servicestats['FirstServePointsWon']['Dividend']
    p1.append(fstw)
    sndw = servicestats['SecondServePointsWon']['Dividend']
    p1.append(sndw)
    bp = returnstats['BreakPointsConverted']['Divisor']
    p1.append(bp)
    bpls = bp - returnstats['BreakPointsConverted']['Dividend']
    p1.append(bpls)
    tp = stats['PointStats']['TotalPointsWon']['Dividend']
    p1.append(tp)

    stats = text['OpponentTeam']['SetScores'][0]['Stats']
    servicestats = stats['ServiceStats']
    returnstats = stats['ReturnStats']
    ace = servicestats['Aces']['Number']
    p2.append(ace)
    df = servicestats['DoubleFaults']['Number']
    p2.append(df)
    fstsvc = servicestats['FirstServe']['Divisor']
    p2.append(fstsvc)
    sndsvc = fstsvc - servicestats['FirstServe']['Dividend']
    p2.append(sndsvc)
    fstw = servicestats['FirstServePointsWon']['Dividend']
    p2.append(fstw)
    sndw = servicestats['SecondServePointsWon']['Dividend']
    p2.append(sndw)
    bp = returnstats['BreakPointsConverted']['Divisor']
    p2.append(bp)
    bpls = bp - returnstats['BreakPointsConverted']['Dividend']
    p2.append(bpls)
    tp = stats['PointStats']['TotalPointsWon']['Dividend']
    p2.append(tp)

    if sgn == False:
        p1, p2 = p2, p1
    if sgnout == False:
        ID1, ID2 = ID2, ID1
    getmatchresult(ID1, ID2, winner, mid, tournament_id, score_str, KO, round_, level, cursor)

    stats = process(p1, p2, ID1, ID2)
    stats.insert(0, tournament_id)
    stats.insert(1, KO - mid)
    stats.append(datetime.datetime.now())
    cursor.execute(
        "INSERT Match_stats VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        tuple(stats))
    print(stats)


@retry(stop_max_attempt_number=5, wait_fixed=3000)
def getdata(id1,id2,player1,player2,eid,matchid,year,ID1,ID2,tournament_id,mid,winner,round_,KO,cursor,level,date):
    url = 'https://www.rank-tennis.com/zh/stat/query'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'
    }

    data = {
        'id1': id1,
        'id2': id2,
        'p1': player1.encode('latin1').decode('gbk'),
        'p2': player2.encode('latin1').decode('gbk'),
        'eid': eid,
        'type': 'atp',
        'matchid': matchid,
        'year': year
    }

    print(id1,id2,matchid,player1.encode('latin1').decode('gbk'),player2.encode('latin1').decode('gbk'))
    # post请求的参数需要编码，因为post请求中不能出现字符串，必须是字节
    data = urllib.parse.urlencode(data).encode('utf-8')

    request = urllib.request.Request(url = url, data = data, headers = headers)
    response = urllib.request.urlopen(request,timeout=10)
    if response.getcode() == 500:
        return -1

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
    try:
        win = re.search(pat3, str(win_mark)).span()[1]
        lose = re.search(pat4, str(win_mark)).span()[1]
        if win > lose:
            win_inner = 2
        else:
            win_inner = 1
    except:
        win_inner=winner
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
        getmatchresult(ID1,ID2,winner,mid,tournament_id,score_str,KO,round_,level,cursor)
        return 0

    score_str=processscore(score,win_inner)
    getmatchresult(ID1,ID2,winner,mid,tournament_id,score_str,KO,round_,level,cursor)


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
    stats.append(datetime.datetime.now())
    cursor.execute(
        "INSERT Match_stats VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        tuple(stats))
    print(stats)



def getmatchresult(id1,id2,winner,mid,tournamentid,score_str,KO,round_,level,cursor):
    date = datetime.datetime.now()
    if winner==2:
        id1,id2=id2,id1
    tourid=tournamentid//100
    year=2000+tournamentid%100
    cursor.execute(
        "Update user_choice set match_id=%s where match_id is NULL and ((winner=%s and loser=%s) or (loser=%s and winner=%s))",
        (KO - mid, id1, id2, id1, id2))
    cursor.execute("Insert result VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(id1,id2,KO-mid,score_str,tourid,year,round_,date))

    level_app = {'Grand Slam': 1, 'Tour Final': 1, 'ATP1000': 0.9, 'Olympics': 0.8, 'ATP500': 0.8, 'ATP250': 0.75,
                 'NextGen Finals': 0.6, 'Davis Cup': 0.7, 'Atp Cup': 0.72, 'United Cup': 0.72, 'Laver Cup': 0.6,
                 'Qualify': 0.65}
    round_app = {'F': 1, 'SF': 0.9, 'QF': 0.85, 'R4': 0.8, 'R3': 0.77, 'R2': 0.75, 'R1': 0.75, 'Q3': 0.68, 'Q2': 0.67,
                 'Q1': 0.65, 'CF': 0.87, 'RR': 0.85, 'PO': 0.8, 'ER': 0.75, 'BR': 0.95}
    BO_app = {'-1': 0.5, '-2': 0.2, '0': 0.6, '1': 0.9, '2': 0.95, '3': 1}

    s1, s2 = process_result(score_str)
    date = datetime.date(date.year, date.month, date.day)

    if s1 == 0 and s2 == 0:
        s1, s2 = '0', '-1'
    elif s1 < s2:
        s1, s2 = '-2', '0'
    elif s1 == 1 and s2 <= 1:
        s1, s2 = '1', '1'
    elif s1 == 2:
        s1, s2 = '2', '2'
    else:
        s1, s2 = '3', '3'

    K_a = level_app[level] * round_app[round_]
    K_a1 = K_a * BO_app[s1]
    K_a2 = K_a * BO_app[s2]

    cursor.execute("select Date, elorate from elo_rating where id=%s order by Date DESC, match_id DESC", id1)
    tmp = cursor.fetchone()
    if tmp != None:
        e1, d1 = tmp[1], tmp[0]
    else:
        e1 = None
    cursor.execute("select Date, elorate from elo_rating where id=%s order by Date DESC, match_id DESC", id2)
    tmp = cursor.fetchone()
    if tmp != None:
        e2, d2 = tmp[1], tmp[0]
    else:
        e2 = None

    if e1 == None:
        cursor.execute("select First_Appearance from Player where ID=%s", id1)
        e1 = 1500
        d1 = date
    if e2 == None:
        cursor.execute("select First_Appearance from Player where ID=%s", id2)
        e2 = 1500
        d2 = date

    player1 = Player_rating_Elo(e1)
    player2 = Player_rating_Elo(e2)

    # non-play penalty
    wk = (date - d1).days // 7
    if date.year != d1.year:
        wk = wk - 8
    if date.year >= 2020 and d1.year <= 2020:
        wk = wk - 25
    if wk >= 6:
        player1.nonplay_penalty(wk)
    wk = (date - d2).days // 7
    if date.year != d2.year:
        wk = wk - 8
    if date.year >= 2020 and d2.year <= 2020:
        wk = wk - 25
    if wk >= 6:
        player2.nonplay_penalty(wk)

    # play
    pre_rating_1 = player1.rating
    pre_rating_2 = player2.rating

    player1.param_update(player2, 1, K_a1)
    player2.param_update(player1, 0, K_a2)

    cursor.execute("Insert elo_rating Values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (
        id1, date, player1.rating, tournamentid, KO - mid, pre_rating_1, None, None, None, None, None, None, None,
        None))
    cursor.execute("Insert elo_rating Values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (
        id2, date, player2.rating, tournamentid, KO - mid, pre_rating_2, None, None, None, None, None, None, None,
        None))

    if tourid == 8359:
        print([year, KO - mid, 'Hard', datetime.date.today() - datetime.timedelta(days=global_day)])
        cursor.execute("Insert DavisCup_surface VALUES(%s,%s,%s,%s)",
                       (year, KO - mid, 'Hard', datetime.date.today() - datetime.timedelta(days=global_day)))
    print([id1,id2,KO-mid,score_str,tourid,year,round_])


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

def getmatchinfo(name,matchid,mid,eid,year,tournamentid,winner,round_,u_name,KO,cursor,date_start,level,score_str):
    info1,info2=getplayerinfo(name[0],name[1],cursor,u_name,date_start)
    if info1==-1:
        return 1
    try:
        status_code = getdata(name[0],name[1],info1[0],info2[0],eid,matchid,year,info1[1],info2[1],tournamentid,mid,winner,round_,KO,cursor,level,date_start)
        if status_code==-1:
            return -1
    except:
        status_code = getdata_tour(name[0],name[1],info1[0],info2[0],eid,matchid,year,info1[1],info2[1],tournamentid,mid,winner,round_,KO,cursor,level,date_start,score_str)
        if status_code==-1:
            return -1
        elif status_code==1:
            return 1


def get_KO(tourid,level):
    KO = None
    if level == 'Qualify':
        return None
    elif level == 'Grand Slam':
        return 128
    else:
        url = "https://www.atptour.com/en/-/tournaments/profile/"+str(tourid)+"/overview"
        head = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
            'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'

        }
        req = urllib.request.Request(url, headers=head)
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        # bs = BeautifulSoup(html, "html.parser")
        info = json.loads(html)
        KO = info['SinglesDrawSize']

        if KO == None:
            KO = int(input('input the KO'))
        return KO

def get_matchid_RoundRobin(cursor,tour,year):
    cursor.execute("select Count(*) from result where tournament_id = %s and [Year] = %s",(tour,year))
    a_num = cursor.fetchone()[0]
    mid = 1 + a_num

    return int(mid)


def get_matchid(cursor,tour,year,KO,round_):
    mid = 0
    k = 16
    while k<KO:
        k = 2*k
    bye = k-KO
    pat = re.compile('\d')
    cursor.execute("select Count(*) from result where tournament_id = %s and [Year] = %s and [round] = %s",(tour,year,round_))
    a_num = cursor.fetchone()[0]
    if round_ == 'F':
        mid = KO - 1
    elif round_ == 'SF':
        mid = KO-1-2+a_num
    elif round_ == 'QF':
        mid = KO-1-2-4+a_num
    elif pat.findall(round_) != None:
        r_num = pat.findall(round_)[0]
        if r_num == '1':
            mid = 1 + a_num
        elif r_num == '2':
            mid = k/2-bye + 1 + a_num
        elif r_num == '3':
            mid = k/2-bye + k/4 + 1 +a_num
        elif r_num == '4':
            mid = k/2-bye + k/4 + k/8 + 1 + a_num
    return int(mid)

def cal_part(cursor,tour):
    cursor.execute(
        "select (sum(t.KO-p.rank+1)+(max(t.KO)-Count(*))*0.25)*100.0/((1+max(t.KO))*max(t.KO)/2) from Tournament t join Participator_list p on t.ID = p.tour_id and p.rank <= t.KO where t.ID=%s",
        tour)
    part = cursor.fetchone()[0]
    if part == None:
        part = 1
    part = str(math.floor(part * 10) / 10) + '%'
    return part


def cal_diff(cursor,tour):
    cursor.execute(
        "select q.rank, q.Level, e.preelo winner_elo, e1.preelo loser_elo from (select rank,Level, t.ID, r.match_id, r.p1_id, r.p2_id from Tournament t join result r on t.Tournament=r.tournament_id and t.year=r.year and p1_id = (select top 1 p1_id from result where tournament_id*100+year%100=%s and round = 'F')  join Participator_list p on t.ID = p.tour_id and p.id = r.p2_id where t.ID=%s) q join elo_rating e on q.ID = e.tournament and q.match_id=e.match_id and q.p1_id=e.ID join elo_rating e1 on q.ID = e1.tournament and q.match_id=e1.match_id and q.p2_id=e1.ID order by q.match_id",
        (tour, tour))
    diff = cursor.fetchall()
    diff = pd.DataFrame(diff, columns=['rank', 'level', 'win_elo', 'loss_elo'])
    diff_ = np.sum(6 / (5 + diff['rank']/2.5))
    strg_ = np.sum(1/(0.9+(1500-diff['loss_elo'])/1500)-1/0.9)
    diff_ = (diff_ + strg_/1.5) * 2.5
    if diff.iloc[0, 1] == 'Grand Slam':
        diff_ = 5 / 3 * diff_
    diff_ = round(float(diff_), 3)
    return diff_

class Player_rating_Elo():
    def __init__(self,rating=1500):
        self.rating = rating
        self.K_factor = 1+18/(1+2**((self.rating-1500)/63))

    def calculate_expectation(self,opponent):
        return 1/(1+10**((opponent.rating-self.rating)/400))

    def param_update(self,opponent,s,K_appendix):
        e = self.calculate_expectation(opponent)
        if s-e > 0:
            change = max(round(K_appendix*32*self.K_factor*(s-e),0),1)
        else:
            change = min(round(K_appendix*32*self.K_factor*(s-e),0),-1)
        self.rating = self.rating + change

    def nonplay_penalty(self,t):
        modify_factor = 300/np.log(100)
        if t>= 100:
            self.rating = 1500
        else:
            self.rating = np.maximum(round(self.rating+modify_factor*np.log(-(t-100))-300,0),1500)

def history_speed(cursor,tournamentid):
    cursor.execute("select speed,[year] from Tournament where Tournament=%s order by [year] desc", tournamentid // 100)
    tour_info = cursor.fetchall()
    count = 0
    if not tour_info:
        speed = int(input("input the tournament speed "))
    else:
        sum = 0
        for item in tour_info:
            if item[0] == None:
                continue
            if count >= 3 or abs(item[0] - (sum + item[0]) / (count + 1)) >= 10:
                break
            else:
                sum = sum + item[0]
                count = count + 1
        if sum == 0:
            speed = None
        else:
            speed = sum / count

    return speed

@retry(stop_max_attempt_number=5, wait_fixed=3000)
def select_data(mode, eid, tournamentid, year, tournament, type, level, seq, status, date,
                constraint_stop_num):
    if mode == 'date':
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=global_day)
        date_str = (now-delta).strftime('%Y-%m-%d')
        url = "https://www.rank-tennis.com/zh/result/"+date_str
    else:
        if 'A' < eid and eid < 'Z':
            url = 'https://www.rank-tennis.com/zh/schedule/' + eid + '/' + str(year)
        else:
            url = 'https://www.rank-tennis.com/zh/schedule/2' + eid + '/' + str(year)

    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
        'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'

    }
    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req,timeout=20)
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    bs_ = bs
    if mode == 'date':
        temp = bs.find_all('div', attrs={'class': 'cResultTour'})
        for item in temp:
            try:
                if 'A' < eid and eid < 'Z':
                    str(item).index('cResultTour' + eid)
                else:
                    str(item).index('cResultTour2' + eid)
                bs_ = item
                break
            except:
                continue
        #bs = bs.find_all('div', attrs={'class': 'cResultTour', 'data-eid': tourid})[0]
    if bs_ == bs and mode == 'date':
        return -1

    if level == 'Davis Cup':
        court_tags = bs_.find_all(attrs={"class": "cResultCourt", "court-id": True})
        for tag in court_tags:
            if '世界' in tag['court-id']:
                tag.extract()

    a = bs_.find_all('div', class_='cResultMatch')

    pat = re.compile(r'Q\d')
    pattern = re.compile("cResultPlayer(\w+)")
    patro = re.compile('match-id="(\w+)"')
    patt = re.compile('open_stat[(-)].+, "(\D+)", "(\D+)"[(-)]')

    connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='atp-tennis', charset='utf8')
    cursor = connect.cursor()

    nonexist = 0
    b = []
    if level=='Qualify':
        for item in a:
            if item.select("div[class='cResultMatchGender']")[0].text == "男单" and re.match(pat, item.select(
                    "div[class='cResultMatchRound']")[0].text):
                b.append(item)
    else:
        for item in a:
            if item.select("div[class='cResultMatchGender']")[0].text == "男单" and re.match(pat, item.select(
                    "div[class='cResultMatchRound']")[0].text)==None:
                b.append(item)

    cursor.execute("select max(match_id) from result where tournament_id=%s and [Year]=%s",(tournamentid // 100, year))
    max_id = cursor.fetchone()[0]
    if max_id == None:
        match_have_select = 0
    else:
        match_have_select=int(max_id)

    print("there are "+str(match_have_select)+" matches have been selected.")

    if match_have_select == 0:
        print(eid)
        if level != 'Qualify':
            cursor.execute("select speed from Tournament where Tournament=%s and year=%s",
                           ('99'+str(tournamentid//100),year))
            if cursor.rowcount != 0:
                speed = cursor.fetchone()[0]
            else:
                speed = history_speed(cursor,tournamentid)
        else:
            speed = history_speed(cursor, tournamentid)

        if level == 'ATP1000':
            if tournament[-7:] != 'Masters':
                tournament = tournament + ' Masters'
        player_num = get_KO(tournamentid//100, level)
        cursor.execute("Insert Tournament Values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                   (tournamentid // 100, year, tournament, level, type, tournamentid, seq, speed, date, player_num,None,None))

    # print((tournamentid // 100, year, tournament, level, type, tournamentid, seq, speed, date, player_num))
    print("please check the sequence!")
    time.sleep(3)
    KO = len(b)+match_have_select+1
    print(tournamentid)
    cursor.execute("select KO from Tournament where ID = %s",tournamentid)
    n_KO = cursor.fetchone()[0]
    print(n_KO)
    num = 0
    seed_info = pd.DataFrame(columns=['RID','seed'])

    for item in b:
        round_ = item.select("div[class='cResultMatchRound']")[0].text
        print(round_)
        pat3 = re.compile('cResultMatchMidTableRow"')
        pat4 = re.compile("cResultMatchMidTableRowWinner")
        try:
            win = re.search(pat4, str(item)).span()[1]
            lose = re.search(pat3, str(item)).span()[1]
            if win > lose:
                winner = 2
            else:
                winner = 1
        except:
            num = num + 1
            nonexist = nonexist + 1
            print("The match hasn't started.")
            continue
        num = num + 1
        name = re.findall(pattern, str(item))
        match = re.findall(patro, str(item))[0]
        u_name = re.findall(patt, str(item))[0]
        seed_pat_0 = re.compile(u_name[0]+'<sub>\s+\[(\w+(?:/W)?)\]')
        seed_pat_1 = re.compile(u_name[1]+'<sub>\s+\[(\w+(?:/W)?)\]')
        seed_0 = re.findall(seed_pat_0,str(item))
        seed_1 = re.findall(seed_pat_1,str(item))
        seed_0 = seed_0[0] if len(seed_0)!=0 else ''
        seed_1 = seed_1[0] if len(seed_1)!=0 else ''
        seed_info.loc[len(seed_info)]=[name[0],seed_0]
        seed_info.loc[len(seed_info)]=[name[1],seed_1]

        set_point = []
        sets = item.find_all('tr', class_=lambda value: value and ('cResultMatchMidTableRow' in value))
        for set_tag in sets:
            scores = [score.text.strip() for score in set_tag.find_all('div')[1:] if score.text.strip()]
            set_point.append(scores)

        set_score = []
        for i in range(len(set_point[0])):
            set_score.append(set_point[0][i])
            set_score.append(set_point[1][i])
        score_res = processscore(set_score,winner)

        # print(u_name)
        mid = num
        if level != 'Qualify':
            if level in ['Tour Final', 'NextGen Finals', 'Laver Cup', 'Davis Cup', 'United Cup']:
                s_ = get_matchid_RoundRobin(cursor, tournamentid // 100, year)
                if level == 'Davis Cup' and isContainChinese(round_):
                    if date.month == 2:
                        round_ = 'PO'
                    else:
                        round_ = 'RR'
                if (level == 'Tour Final' or level == 'NextGen Finals' or level == 'United Cup') and len(round_)>6:
                    round_ = 'RR'
            else:
                s_ = get_matchid(cursor,tournamentid//100,year,n_KO,round_)
            mid = KO-s_
        try:
            if 'A'<eid and eid<'Z':
                status_code = getmatchinfo(name, match, mid, eid, year, tournamentid, winner, round_, u_name, KO, cursor, date, level, score_res)
            else:
                status_code = getmatchinfo(name, match, mid, '2'+eid, year, tournamentid, winner, round_, u_name, KO, cursor, date, level, score_res)
        except:
            status_code = 1
        if status_code == 1:
            nonexist = nonexist + 1
            if set_score != []:
                info1, info2 = getplayerinfo(name[0], name[1], cursor, u_name, date)
                if winner == 2:
                    info1, info2 = info2, info1
                tourid = tournamentid // 100
                print([info1[1], info2[1], KO - mid, score_res, tourid, year, round_])
                cursor.execute(
                    "Update user_choice set match_id=%s where match_id is NULL and ((winner=%s and loser=%s) or (loser=%s and winner=%s))",
                    (KO - mid, info1[1], info2[1], info1[1], info2[1]))
                cursor.execute("Insert result VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                               (info1[1], info2[1], KO - mid, score_res, tourid, year, round_, datetime.datetime.now()))
        elif status_code == -1:
            if status == 'Completing':
                print("The match hasn't started.")
                connect.rollback()
                exit(1)
            else:
                info1, info2 = getplayerinfo(name[0], name[1], cursor, u_name, date)
                if winner == 2:
                    info1, info2 = info2, info1
                tourid = tournamentid // 100
                print([info1[1], info2[1], KO - mid, 'W/O', tourid, year, round_])
                cursor.execute("Update user_choice set match_id=%s where match_id is NULL and ((winner=%s and loser=%s) or (loser=%s and winner=%s))",(KO-mid,info1[1],info2[1],info1[1],info2[1]))
                cursor.execute("Insert result VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                               (info1[1], info2[1], KO - mid, 'W/O', tourid, year, round_,datetime.datetime.now()))

                if level == 'Davis Cup':
                    print([year, KO - mid, 'Hard', datetime.date.today() - datetime.timedelta(days=global_day)])
                    cursor.execute("Insert DavisCup_surface VALUES(%s,%s,%s,%s)", (year, KO - mid, 'Hard', datetime.date.today() - datetime.timedelta(days=global_day)))


        if round_ == 'F':
            part = cal_part(cursor,tournamentid)
            diff = cal_diff(cursor,tournamentid)
            cursor.execute('Update Tournament set diff = %s where ID = %s', (diff, tournamentid))
            cursor.execute('Update Tournament set part = %s where ID = %s', (part, tournamentid))

            cursor.execute(
                "select ID from participator_list where tour_id=%s", (tournamentid))
            df = cursor.fetchall()
            for item in df:
                perform = cal_perf(tournamentid, item[0], cursor)
                cursor.execute("update participator_list set score=%s where tour_id=%s and id=%s",
                               (perform, tournamentid, item[0]))

            if 'A'<eid and eid<'Z':
                url = 'https://www.rank-tennis.com/en/draw/ajax/' + eid + '/' + str(year) + '/device/0/horizontal/true'
            else:
                url = 'https://www.rank-tennis.com/en/draw/ajax/2' + eid + '/' + str(year) + '/device/0/horizontal/true'
            head = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
                'Cookie': '__gads=ID=1fac094766b8080d-2298fba0ebcf0090:T=1642325857:RT=1642325857:S=ALNI_MaYn4VacQNXRp_wFbxGMZoK4_W1IQ; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6ImtkTE9zR1A0TlFtVlFpbGNFeExsdGc9PSIsInZhbHVlIjoibERVZGNNSVQwNDg3OEVhc1BVd0ZTc1JUbkRITnFWZ2h2N2F4Zk4rUUdWRnJ3blZEZXNDZTU2XC9iK3ptVW5NUTNjclY4VEViK2lDaXJrMGl4NzdNZVFwSHBYcG9kbWRBM1c4dG04ZlZ1R015YVVNYjhsbDgzWE5RWjZTeWgzZjUzQmJQb1pBU29mSXpLM1VyQzlpZnhKK0ZERkRPTEdFVkIrTG03YXlKaFBGdz0iLCJtYWMiOiI4MTYxYzJkMWVlYjBjYTllODlmYjA2ODhlY2ExNWVmYmJjYzcwNWU4YTJiZDQ2YWE2YzcyNjlkM2IzZmQzODM4In0%3D; Hm_ct_3b995bf0c6a621a743d0cf009eaf5c8a=17*1*%E5%BE%AE%E5%8D%9A!2444*1*28601!2445*1*CORICw5LDjsOZw5HDhcOYw4zDicORw4XDmMONw4fDl8ODw4fDk8OSw5fDicOWw5rDhcOYw43Dl8ORTOP; Hm_up_3b995bf0c6a621a743d0cf009eaf5c8a=%7B%22uid_%22%3A%7B%22value%22%3A%2228601%22%2C%22scope%22%3A1%7D%7D; def_sex=MS; _gid=GA1.2.763224088.1654238270; __gpi=UID=00000599e65e915f:T=1653036198:RT=1654310778:S=ALNI_MacbZDJi_SB-LlD1KJw-qDdUisK3Q; msg_read=1; Hm_lvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654080160,1654238270,1654310767,1654321757; _ga=GA1.2.280913605.1642325840; Hm_lpvt_3b995bf0c6a621a743d0cf009eaf5c8a=1654324771; _ga_7GW8TTD6GW=GS1.1.1654321756.77.1.1654324773.0; _session=eyJpdiI6IkFjN1lqOFRpV0RcLytkRzlobUE3UXZRPT0iLCJ2YWx1ZSI6IllNK08wbVBcL0VcL0QxdVpSV1NTOW9lN1B4eDBQRW0zTGRUNUJHNlBLSDBTTTFBSCtvNk5icVR1MEpqXC9KTWZ2dFciLCJtYWMiOiI2YTljOTVkMzRlM2RlYmJiM2UwNDRhYzQzMGM3ZjMxNzYwM2NmYzI5OWViYjcxMDMzMjVmOTQzYjE5ZmE1ZjU5In0%3D; _gat=1'

            }
            req = urllib.request.Request(url, headers=head)
            # req = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(req)
            html = response.read().decode('utf-8')
            bs = BeautifulSoup(html, "html.parser")

            temp = bs.find_all('div', attrs={'class': 'cDrawInfoBg1'})
            if temp == []:
                temp = bs.find_all('div', attrs={'class': 'cDrawInfoBg2'})
            if temp == []:
                print("skip")
                continue
            st = temp[0]
            pat = re.compile("background-image: url[(]'(https://www.rank-tennis.com/images/trophies/\d+x\d+_\S+)'[)]")
            photo = re.findall(pat,str(st))
            photo = photo[0]
            name = str(tournamentid)+'.jpg'
            download_pic_trophy(photo, name)


        if num + 1 == constraint_stop_num:
            break
    print("there are " + str(num) + " matches be selected with " + str(nonexist) + " not exist.")
    #connect.commit()

    execute_rank(tournamentid, year, date, cursor, seed_info, level)
    connect.commit()

def istimeapp(code,day):
    code_2 = pc.countries.get(alpha_3=code).alpha_2
    zone = pytz.timezone(pytz.country_timezones(code_2)[0])
    hour = datetime.datetime.now(zone).hour
    d = datetime.datetime.now(zone).day
    if d==day and hour>=2:
        return True
    else:
        print("We are going to select at 4 o'clock")
        print("local time ",d,hour)
        print("your time ", day)
        return False

def select_top100_rank():
    url = "https://www.atptour.com/en/rankings/singles"

    connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='atp-tennis')
    cursor = connect.cursor()

    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
        # "sec-ch-ua": '"Chromium";v ="92","Not A;Brand";v="99","Google Chrome";v="92"',
        # "Cookie": "_ga = GA1.2.324355889.1621857694;__gads=ID=8cfa7d12bbca2f6d-22ba21761bc80082:T=1621857691:RT = 1621857691:S=ALNI_MYJRBxeLS0iZna4gzE_F2cbdf8ZDA;gid = GA1.2.1014988429.1630369661"
    }
    req = urllib.request.Request(url, headers=head)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    bs = BeautifulSoup(html, "html.parser")
    player_ids = []
    lst = bs.find_all('li', class_="name center")
    for li_tag in lst:
        a_tag = li_tag.find('a', href=True)
        player_id = a_tag['href'].split('/')[-2]
        player_ids.append(player_id)

    point = bs.find_all('td', class_="points center bold extrabold")
    point_lst = []
    for td_tag in point:
        point_lst.append(td_tag.text.strip())

    for i in range(0,100):
        rank = i+1
        rid = player_ids[i]
        cursor.execute("select ID from Player where [R-ID]=%s",rid)
        ID = cursor.fetchone()[0]
        point = int(point_lst[i].replace(',', ''))
        now = datetime.datetime.date(datetime.datetime.now()-datetime.timedelta(days=global_day))
        print((ID, rank, now, point))
        cursor.execute("Insert TOP100 Values(%s,%s,%s,%s)", (ID, rank, now, point))

    connect.commit()
    connect.close()

def main():
    with open("tour_list_a.txt", 'r', encoding='utf-8') as f:
        line=f.readlines()
        f.close()
    global global_day
    global_day = 1
    date_now = datetime.datetime.now()-datetime.timedelta(days=global_day)
    date_now = datetime.date(date_now.year, date_now.month, date_now.day)
    if date_now.weekday() == 0:
        select_top100_rank()

    for item in line:
        info = tuple(eval(item))
        if info[3]!='Qualify':
            date_start = info[7]
            date_start = datetime.date(int(date_start[0:4]),int(date_start[5:7]),int(date_start[8:10]))
            date_end = info[8]
            date_end = datetime.date(int(date_end[0:4]), int(date_end[5:7]), int(date_end[8:10]))

            if date_now>=date_start and date_now<=date_end:
                # flag = istimeapp(info[9],date_today)
                # if flag == False:
                #     print("Not a appropriate time.")
                #     continue
                eid = convert_GS(str(int(info[0])//100))
                tournamentid = int(info[0])
                year = info[1]
                tournament = info[2]
                type = info[4]
                level = info[3]
                KO = 128
                seq = int(info[5])-1
                status = 'Finished'
                date = datetime.datetime.strptime(info[7], '%Y-%m-%d')
                constraint_stop_num = KO
                mode = 'date'
                print(tournament)
                select_data(mode, eid, tournamentid, year, tournament, type, level, seq, status, date,
                            constraint_stop_num)
            elif date_now+datetime.timedelta(days=1)<date_start:
                break
        else:
            date_end = info[8]
            date_end = datetime.date(int(date_end[0:4]), int(date_end[5:7]), int(date_end[8:10]))
            date_start = info[7]
            date_start = datetime.date(int(date_start[0:4]), int(date_start[5:7]), int(date_start[8:10]))
            if date_now == date_end:
                # flag = istimeapp(info[9], date_today)
                # if flag == False:
                #     print("Not a appropriate time.")
                #     continue
                eid = convert_GS(str((int(info[0])-99*10**(len(str(info[0]))-2)) // 100))
                print(eid)
                tournamentid = int(info[0])
                year = info[1]
                tournament = info[2]
                type = info[4]
                level = info[3]
                KO = 128
                seq = int(info[5]) - 1
                status = 'Completing'
                date = datetime.datetime.strptime(info[7], '%Y-%m-%d')
                constraint_stop_num = KO
                #mode = 'date'
                mode = 'tour'
                print(tournament)
                select_data(mode, eid, tournamentid, year, tournament, type, level, seq, status, date,
                            constraint_stop_num)
            elif date_now+datetime.timedelta(days=1) < date_start:
                break
    return 'success'

if __name__=='__main__':
    main()