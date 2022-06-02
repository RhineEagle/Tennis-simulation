import re
import urllib.request
import pymssql
import json

tournament_id = 52022
match_id = 80
mode= 2
url="https://api.sofascore.com/api/v1/event/10319692/statistics"

connect = pymssql.connect(server='LAPTOP-BBQ77BE4', user='sa', password='123456', database='tennis')
cursor = connect.cursor()
cursor.execute("select ID from Player where Name LIKE '%Nadal%'")
p1_id=cursor.fetchone()[0]
cursor.execute("select ID from Player where Name LIKE '%Moutet%'")
p2_id=cursor.fetchone()[0]

match_stat=[-1 for _ in range(0,32)]
if mode==1:
    winner='home'
    loser='away'
else:
    winner='away'
    loser='home'

match_stat[0]=tournament_id
match_stat[1]=match_id
match_stat[2]=p1_id
match_stat[11]=p2_id

head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3756.400 QQBrowser/10.5.4039.400",
        #"sec-ch-ua": '"Chromium";v ="92","Not A;Brand";v="99","Google Chrome";v="92"',
        #"Cookie": "_ga = GA1.2.324355889.1621857694;__gads=ID=8cfa7d12bbca2f6d-22ba21761bc80082:T=1621857691:RT = 1621857691:S=ALNI_MYJRBxeLS0iZna4gzE_F2cbdf8ZDA;gid = GA1.2.1014988429.1630369661"
    }
req = urllib.request.Request(url, headers=head)
response = urllib.request.urlopen(req)
html = response.read().decode('utf-8')
text = json.loads(html)["statistics"][0]["groups"][0]["statisticsItems"]

for item in text:
    if item['name']=='Aces':
        match_stat[3]=int(item[winner])
        match_stat[12]=int(item[loser])
    if item['name']=='Double faults':
        match_stat[4]=int(item[winner])
        match_stat[13]=int(item[loser])
    if item['name']=='First serve':
        info1=item[winner]
        info2=item[loser]
        pat1=re.compile('/(\d+)')
        pat2=re.compile('\d+')
        match_stat[5]=int(re.findall(pat1,info1)[0])
        match_stat[6]=match_stat[5]-int(re.findall(pat2,info1)[0])
        match_stat[14]=int(re.findall(pat1,info2)[0])
        match_stat[15]=match_stat[14]-int(re.findall(pat2,info2)[0])
    if item['name']=='First serve points':
        info1 = item[winner]
        info2 = item[loser]
        pat1 = re.compile('\d+')
        match_stat[7]=int(re.findall(pat1,info1)[0])
        match_stat[16]=int(re.findall(pat1,info2)[0])
    if item['name']=='Second serve points':
        info1 = item[winner]
        info2 = item[loser]
        pat1 = re.compile('\d+')
        match_stat[8]=int(re.findall(pat1,info1)[0])
        match_stat[17]=int(re.findall(pat1,info2)[0])
    if item['name']=='Break points saved':
        info1 = item[winner]
        info2 = item[loser]
        pat1 = re.compile('/(\d+)')
        pat2 = re.compile('\d+')
        match_stat[18] = int(re.findall(pat1, info1)[0])
        match_stat[19] = int(re.findall(pat2, info1)[0])
        match_stat[9] = int(re.findall(pat1, info2)[0])
        match_stat[10] = int(re.findall(pat2, info2)[0])

for i in range(0,32):
    if match_stat[i]==-1:
        match_stat[i]=None

print(match_stat)
cursor.execute("INSERT Match_stats VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", tuple(match_stat))
connect.commit()
connect.close()