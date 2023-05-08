import datetime
import math
import numpy as np
import pandas as pd
import os
import pymssql
import project.match_result as ms
from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
import re
import cv2 as cv

app = Flask(__name__)
bootstrap = Bootstrap(app)


def getusername():
    user_token = request.cookies.get("token")
    pat = re.compile('_(\w+)/')
    if user_token:
        user = re.findall(pat, user_token)[0]
    else:
        user = ''
    print(user)
    return user

def global_variable():
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute("select distinct country from Player where country is not NULL and country != 'Unknown' order by country")
    countryinfo = cursor.fetchall()
    global countrylist
    countrylist = [x[0].strip() for x in countryinfo]

    cursor.execute("select Name from Player where [R-id] is not NULL order by Last_Appearance desc")
    playerinfo = cursor.fetchall()
    global playerlist
    playerlist = [x[0].strip() for x in playerinfo]

    cursor.execute("select distinct year from result order by year desc")
    yearinfo = cursor.fetchall()
    global yearlist
    yearlist = [str(x[0]) for x in yearinfo]

    connect.close()

    global countrystr
    countrystr = ""
    for item in countrylist:
        countrystr = countrystr + "<option>"+item+"</option>"
    countrystr = countrystr + '</datalist>'

    global playerstr
    playerstr = ""
    for item in playerlist:
        playerstr = playerstr + "<option>"+item+"</option>"
    playerstr = playerstr + '</datalist>'


@app.route('/')
def homepage():
    user = getusername()
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    now = datetime.datetime.today()

    cursor.execute("select Name from Player where [R-id] is not NULL order by Last_Appearance desc")
    playerlist = cursor.fetchall()
    playerlist = [x[0].strip() for x in playerlist]

    cursor.execute('select top 10 (select top 1 Name from Player where ID=TOP100.ID),rank, point, Date from TOP100 where Date = (select max(Date) from TOP100)')
    topplayer = cursor.fetchall()
    table = []
    for item in topplayer:
        item_s = list(item)
        name = item_s[0]
        if len(name) > 17:
            idx = name.rfind(' ')
            name = name[0] + '.' + name[idx:]
        else:
            name = name
        item_s[0] = name
        table.append(tuple(item_s))

    cursor.execute('select ID,Name,birthday from player where [R-id] is not NULL and MONTH(birthday)=%s and Day(birthday)=%s order by (select COUNT(*) from participator_list where id=player.ID) DESC',(now.month,now.day))
    roll_birth = cursor.fetchall()
    birthplayer = []
    for item in roll_birth:
        image = './static/Player_Photo_head/'+str(item[0])+'.webp'
        img_matrix = cv.imread(image)
        if type(img_matrix) == type(None):
            image = ""
        else:
            default_matrix = cv.imread("./static/Player_Photo_head/default.webp")
            if not np.any(img_matrix - default_matrix):
                image = ""
        birthplayer.append((image,item[1],item[2]))

    cursor.execute("select top 6 Date,ID,Name,(select top 1 name from player where ID=(select top 1 p1_id from result where tournament_id=Tournament and [year]=2023 and [round]='F')) from Tournament where Level != 'qualify' order by Date Desc")
    trophy = cursor.fetchall()
    trophy_pic = []
    for item in trophy:
        path = './static/trophy/'+str(item[1])+'.jpg'
        print(path)
        if not os.path.exists(path):
            continue
        else:
            trophy_pic.append((path,item[2],item[3],item[0]))

    cursor.execute("select top 10 player.Name, Count(*) win, max(sequence+Tournament.Year*100) id from result join Tournament on result.tournament_id=Tournament.Tournament and result.year=Tournament.Year join Player on result.p1_id=Player.ID where Tournament.Level != 'Qualify' and Year(Player.Last_Appearance)=2023 and result.result!='W/O' and result.result!='' and result.result!='Walkover' group by player.Name having COUNT(*)%10=0 and max(Tournament.Year)=2023 order by max(sequence+Tournament.Year*100) DESC, COUNT(*) DESC")
    win = cursor.fetchall()
    winplayer = []
    for item in win:
        cursor.execute("select Name from Tournament where sequence+Year*100=%s",item[2])
        tour = cursor.fetchall()[0]
        winplayer.append((item[0],item[1],tour[0]))


    return render_template('homepage.html',user = user,playerlist=playerlist,data = table,birthplayer = birthplayer,pic = trophy_pic, win = winplayer)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        user = request.form.get("user")
        pwd = request.form.get("pwd")
        print(user,pwd)
        connect = pymssql.connect(server='localhost', user='guest', password='visit', database='atp-tennis',
                                  charset='utf8')
        cursor = connect.cursor()
        cursor.execute("select password from user_info where username=%s",user)
        true_pwd = cursor.fetchone()
        if true_pwd == None:
            return render_template("login.html",warning = 'No')
        elif pwd == true_pwd[0]:
            red = redirect('/')
            cookie_data = 'hkh78y12$%f'+"_"+user+"/udbek"
            red.set_cookie("token", cookie_data)
            return red
        else:
            return render_template("login.html",warning = 'Wrong')

@app.route('/logout')
def logout():
    red = redirect('/')
    red.delete_cookie("token")
    return red

@app.route('/self-center')
def center():
    pass


@app.route('/h2h_query?P1=<player1>&P2=<player2>&Court_type=<court>&Level=<level>')
def h2h_query(player1,player2,court,level):
    color = {'ATP250': 'label label-250', 'ATP500': 'label label-500', 'ATP1000': 'label label-1000', 'Grand Slam': 'label label-GS', 'Atp Cup': 'label label-Cup', 'United Cup': 'label label-Cup', 'Davis Cup': 'label label-Davis', 'Tour Final': 'label label-F', 'Olympics': 'label label-O', 'Qualify': 'label label-Q'
             , 'F': 'label label-Fi', 'SF': 'label label-SF', 'BR': 'label label-SF', 'CF': 'label label-SF', 'QF': 'label label-QF', 'R1': 'label label-R', 'R2': 'label label-R', 'R3': 'label label-R', 'R4': 'label label-R', 'R128': 'label label-R', 'R64': 'label label-R', 'R32': 'label label-R', 'R16': 'label label-R', 'Q1': 'label label-R', 'Q2': 'label label-R', 'Q3': 'label label-R', 'RR': 'label label-R', 'PO': 'label label-R'}

    user = getusername()
    PlayerName = [player1, player2]

    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()

    if player2 in countrylist:
        cursor.execute("EXEC headtohead_country %s,%s", (PlayerName[0], PlayerName[1]))
    elif player2 in playerlist:
        cursor.execute("EXEC headtohead %s,%s", (PlayerName[0], PlayerName[1]))
    else:
        cursor.execute("EXEC headtohead_top %s,%s", (PlayerName[0], PlayerName[1]))

    table = cursor.fetchall()

    if court != 'All':
        table = [x for x in table if x[3].strip() == court]
    if level != 'All':
        if level == 'Grand Slam':
            table = [x for x in table if (
                        x[0] == 'Australian Open' or x[0] == 'Roland Garros' or x[0] == 'Wimbledon' or x[
                    0] == 'US Open' or x[0] == 'French Open')]
        elif level == 'Only Main Draw':
            table = [x for x in table if x[4][1] != 'Q']
        elif level == 'Only Final':
            table = [x for x in table if x[4] == 'F']

    cursor.execute(
        "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country) from Player where Name Like %s ",
        '%' + PlayerName[0] + '%')
    p1 = cursor.fetchone()
    name = [p1[0].strip()]
    image_1 = "./static/Player_Photo_head/" + str(p1[1]) + ".webp"
    img_matrix = cv.imread(image_1)
    if type(img_matrix) == type(None):
        image_1 = "./static/Player_Photo_head/default.webp"
    country = [p1[2]]

    win = 0
    lose = 0

    for i in range(len(table)):
        item = table[i]
        item_ = list(item)
        item_[1] = datetime.datetime.strftime(item_[1],'%Y-%m-%d')
        if not item_[8] or np.isnan(item_[8]):
            item_[8]='  '
        else:
            item_[8]='('+str(item_[8])+')'
        if not item_[9] or np.isnan(item_[9]):
            item_[9]='  '
        else:
            item_[9] = '(' + str(item_[9]) + ')'
        item_[2] = color[item[2].strip()]
        item_.append(color[item[4].strip()])

        if item_[7] == 'W/O':
            pass
        elif player1==item_[5]:
            win = win+1
        else:
            lose = lose+1
        table[i] = tuple(item_)

    if player2 in countrylist:
        cursor.execute(
            "select top 1 country_code from Country where Country LIKE %s ",
            '%' + PlayerName[1] + '%')
        p2 = cursor.fetchone()
        name.append(PlayerName[1])
        image_2 = "./static/Player_Photo_head/default.webp"
        country.append(p2[0])
        image = [image_1, image_2]
        flag = 1
    elif player2 in playerlist:
        cursor.execute(
            "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country) from Player where Name Like %s ",
            '%' + PlayerName[1] + '%')
        p2 = cursor.fetchone()
        name.append(p2[0].strip())
        image_2 = "./static/Player_Photo_head/" + str(p2[1]) + ".webp"
        img_matrix = cv.imread(image_2)
        if type(img_matrix) == type(None):
            image_2 = "./static/Player_Photo_head/default.webp"
        country.append(p2[2])
        image = [image_1,image_2]
        flag = 0
    else:
        name.append(PlayerName[1])
        image_2 = "./static/Player_Photo_head/default.webp"
        country.append("")
        image = [image_1, image_2]
        flag = 2

    Num = 15
    if len(table)%Num==0:
        tpage = len(table)//Num
    else:
        tpage = len(table)//Num+1
    table_=table#[int(page)*Num:int(page)*Num+Num]

    #print(playerlist)
    connect.close()
    return render_template('h2h.html', data=table_, name=name, img=image, playerlist=playerlist, countrylist = countrylist, country=country,
                           user=user, flag=flag, countrystr= countrystr, playerstr=playerstr,tp = tpage, court=court, level=level, win=win, lose=lose)


@app.route('/h2h',methods=['POST','GET'])
def h2h():
    user = getusername()
    if request.method=='GET':
        name = ["",""]
        table = []
        image = []
        flag = 0
        return render_template('h2h.html', name = name, data=table, img=image, playerlist=playerlist, countrylist=countrylist, flag=flag, user = user, countrystr= countrystr, playerstr=playerstr, win=0, lose=0, tp=0)

    else:
        data = request.form.to_dict()
        court = data['court_type']
        level = data['Level_type']
        player1, player2 = data['player1'],data['player2']
        return redirect(url_for("h2h_query",player1=player1,player2=player2,court=court,level=level))


@app.route('/forecast',methods=['POST','GET'])
def forecast():
    user = getusername()
    connect = pymssql.connect(server='localhost', user='guest', password='visit', database='atp-tennis', charset='utf8')
    cursor = connect.cursor()
    cursor.execute("select Name from Player where [R-id] is not NULL order by Last_Appearance desc")
    playerlist = cursor.fetchall()
    playerlist = [x[0].strip() for x in playerlist]
    if request.method == 'GET':
        if user != '':
            return render_template("forecast.html",playerlist = playerlist)
        else:
            return redirect('/login')
    else:
        if user != '':
            data = request.form.to_dict()
            p1 = data['player1']
            p2 = data['player2']
            court = data['court_type']
            speed = data['speed']
            render_template("forecast_default.html",data = [p1,p2])
            wp,result_str = ms.start(p1, p2, court, speed, 2, None, None, 0)
            return render_template("forecast.html",data = [wp,result_str,p1,p2],user = user)
        else:
            return redirect('/login')


@app.route('/profile?Name=<Name>',methods=['GET','POST'])
def profile(Name):
    pass

@app.route('/tournament?Name=<tour>&Year=<year>')
def tournament():
    pass

@app.route('/tournament_list',methods=['GET','POST'])
def tournament_list():
    pass

@app.route('/result_title?name=<name>&year=<year>')
def result_title(name,year):
    user = getusername()
    color = {'ATP250': 'label label-250', 'ATP500': 'label label-500', 'ATP1000': 'label label-1000',
             'Grand Slam': 'label label-GS', 'Tour Final': 'label label-F', 'Olympics': 'label label-O',
             'Davis Cup': 'label label-Davis',
             'Qualify': 'label label-Q'
        , 'W': 'label label-W', 'F': 'label label-Fi', 'SF': 'label label-SF', 'BR': 'label label-SF', 'CF': 'label label-SF',
             'QF': 'label label-QF', 'R1': 'label label-R', 'R2': 'label label-R', 'R3': 'label label-R',
             'R4': 'label label-R', 'R128': 'label label-R', 'R64': 'label label-R', 'R32': 'label label-R',
             'R16': 'label label-R', 'Q1': 'label label-R', 'Q2': 'label label-R', 'Q3': 'label label-R',
             'RR': 'label label-R', 'PO': 'label label-R', 'ER': 'label label-R'}
    level = {'Grand Slam': 2000, 'Tour Final': 1500, 'ATP1000': 1000, 'Olympics': 800, 'ATP500': 500, 'ATP250': 250, 'Qualify':0, 'Atp Cup': 400, 'United Cup': 400, 'Davis Cup':400}
    result_level = {'W':100, 'F': 80, 'BR':70, 'SF': 70, 'QF':50, 'R1': 2, 'R2': 10, 'R3':25, 'R4':40, 'R128': 2, 'R64': 10, 'R32':25, 'R16':40, 'RR': 40, 'ER': 1, 'Q1':-1, 'Q2':0, 'Q3':1,'PO':-1}

    def choose_head_photo(ID):
        image = "./static/Player_Photo_head/" + str(ID) + ".webp"
        img_matrix = cv.imread(image)
        if type(img_matrix) == type(None):
            image = "./static/Player_Photo_head/default.webp"
        return image

    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute("EXEC Player_Appear %s,%d", (name, year))
    table = cursor.fetchall()

    df = pd.DataFrame(table,columns=['Date','Tour','Type','Level','Round'])
    df = df[df['Level'] !='United Cup']
    df = df[df['Level'] != 'Atp Cup']
    df = df[df['Level'] != 'Davis Cup']

    df['poi'] = df['Round'].apply(lambda x: result_level[x.strip()])
    df['lev'] = df['Level'].apply(lambda x: level[x.strip()])

    tmp = df[df['Level']=='Tour Final']
    for ts in tmp['Date'].unique():
        tsp = tmp[tmp['Date']==ts].sort_values(['poi'])
        if len(tsp)>1:
            del_index = tsp.index[:-1]
            df.drop(index=del_index,inplace=True)
    tmp = df[df['Level'] == 'Olympics']
    for ts in tmp['Tour'].unique():
        tsp = tmp[tmp['Tour']==ts]
        #print(tsp)
        if len(tsp) == 1:
            if tsp.iloc[0,4]== 'SF':
                print(tsp.index)
                df.loc[tsp.index[0],'Round'] = 'BR'
        elif len(tsp) == 2:
            del_index = tsp.index[-1]
            df.drop(index=del_index,inplace=True)

    df = df.sort_values(['Date'])
    df = df.sort_values(['poi','lev'],ascending=False)
    p = df['poi'].unique()[0:4]
    dic_p = {}
    champion_type = {}
    for point in p:
        tmp = df[df['poi']==point]
        tmp = tmp.sort_values(['Round'])
        for r in tmp['Round'].unique():
            temp = tmp[tmp['Round']==r]
            temp = temp.sort_values(['lev','Date'], ascending=False)
            lst = []
            for item in temp.values:
                lst.append((item[1],color[item[3].strip()],color[r]))
            dic_p[r]=lst
            if r=='W':
                type_count = temp.groupby(['Type']).agg(['count'])
                for i in range(len(type_count)):
                    court = type_count.index[i]
                    count = type_count.iloc[i,0]
                    champion_type[court] = count

    #print(df)
    cursor.execute(
        "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country) from Player where Name Like %s ",
        '%' + name + '%')
    p = cursor.fetchone()

    image = "./static/Player_Photo_full/" + str(p[1]) + ".webp"
    img_matrix = cv.imread(image)
    if type(img_matrix) == type(None):
        image = choose_head_photo(p[1])
    else:
        default_matrix = cv.imread("./static/Player_Photo_full/default.webp")
        if not np.any(img_matrix - default_matrix):
            image = choose_head_photo(p[1])
    image = [image, p[2]]

    cursor.execute("EXEC select_match %s,%d", (name, year))
    info = cursor.fetchall()
    table = pd.DataFrame(info).iloc[:,2:8]
    table.columns=['Level','Type','Round','winner','loser','result']
    table = table[table['Level']!='Qualify']
    table = table[table['result'] != 'W/O']
    table = table[table['result'] != 'Walkover']
    table = table[table['result'] != '']
    table = table[table['result'] != ' W/O']
    Type = ['Hard','Clay','Grass','Carpet']
    rate = []
    for t in Type:
        if t not in champion_type.keys():
            champion_type[t] = 0
        hd = table[table['Type'] == t]
        if hd.empty == True:
            rate.append(0.0)
            rate.append(0)
            rate.append(0)
        else:
            winner = len(hd[hd['winner']==p[0]])/len(hd)
            winner = round(winner*100,2)
            rate.append(winner)
            rate.append(len(hd[hd['winner'] == p[0]]))
            rate.append(len(hd)-rate[-1])

    if rate[11] == 0 and rate[10] == 0:
        rate = rate[0:9]
    rate.append(round(len(table[table['winner']==p[0]])/len(table)*100,2))
    rate.append(len(table[table['winner'] == p[0]]))
    rate.append(len(table)-len(table[table['winner'] == p[0]]))

    rank = []
    rk = [0, 10, 20, 50, 100]
    index = [5,6,11,12]
    table = pd.DataFrame(info).iloc[:, index]
    table.columns = ['winner', 'loser', 'w_rk', 'l_rk']
    # print(table)
    win = table[table['winner'] == p[0]]
    lose = table[table['loser'] == p[0]]
    for i in range(len(rk)-1):
        interval = (rk[i],rk[i+1])
        tmp = win[win['l_rk']>interval[0]]
        tmp = tmp[tmp['l_rk']<=interval[1]]
        w_tmp = len(tmp)
        tmp = lose[lose['w_rk'] > interval[0]]
        tmp = tmp[tmp['w_rk'] <= interval[1]]
        l_tmp = len(tmp)
        if w_tmp+l_tmp == 0:
            rank.append(0.0)
            rank.append(0)
            rank.append(0)
            continue
        r = round(w_tmp/(w_tmp+l_tmp)*100,2)
        rank.append(r)
        rank.append(w_tmp)
        rank.append(l_tmp)

    connect.close()

    return render_template('Result.html',data=dic_p,name = name, year = year, rate=rate, rank_rate=rank, img=image, user=user, yearlist=yearlist, playerlist=playerlist, court = champion_type)

@app.route('/result', methods=['POST', 'GET'])
def result():
    user = getusername()
    color = {'ATP250': 'label label-250', 'ATP500': 'label label-500', 'ATP1000': 'label label-1000',
             'Grand Slam': 'label label-GS', 'Tour Final': 'label label-F', 'Olympics': 'label label-O',
             'Davis Cup': 'label label-Davis',
             'Qualify': 'label label-Q'
        , 'W': 'label label-W', 'F': 'label label-Fi', 'SF': 'label label-SF', 'BR': 'label label-SF',
             'CF': 'label label-SF',
             'QF': 'label label-QF', 'R1': 'label label-R', 'R2': 'label label-R', 'R3': 'label label-R',
             'R4': 'label label-R', 'R128': 'label label-R', 'R64': 'label label-R', 'R32': 'label label-R',
             'R16': 'label label-R', 'Q1': 'label label-R', 'Q2': 'label label-R', 'Q3': 'label label-R',
             'RR': 'label label-R', 'PO': 'label label-R', 'ER': 'label label-R',
             'Hard': 'label label-primary', 'Clay':'label label-danger', 'Grass': 'label label-success'}
    level = {'Grand Slam': 2000, 'Tour Final': 1500, 'ATP1000': 1000, 'Olympics': 800, 'ATP500': 500, 'ATP250': 250,
             'Qualify': 0, 'Atp Cup': 400, 'United Cup': 400, 'Davis Cup': 400}

    if request.method == 'GET':
        connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                                  charset='utf8')
        cursor = connect.cursor()
        cursor.execute("select * from TOP100 where Date = (select max(Date) from TOP100)")
        rinfo = cursor.fetchall()
        table = []
        rank = 1
        Date = rinfo[0][2]
        cursor.execute("EXEC Player_Appear_52W")
        total_info = cursor.fetchall()
        total_info = pd.DataFrame(total_info, columns=['ID','Name','Country','Birth','Date', 'Tour', 'Type', 'Level', 'Round'])
        for item in rinfo:
            df = total_info[total_info['ID']==item[0]]
            if df.empty:
                cursor.execute("select Name,(select top 1 country_code from Country where Country = Player.country) country, birthday from Player where ID = %s",item[0])
                info = cursor.fetchone()
                id = info[0]
                country = info[1]
                if info[2]:
                    today = datetime.date.today()
                    base_age = today.year - info[2].year
                    day_delta = today - datetime.date(today.year,info[2].month,info[2].day)
                    year_delta = math.floor(abs(day_delta.days) / 365 * 10) / 10
                    age = base_age + year_delta
                else:
                    age = ""
                w_table = pd.DataFrame()
                f_table = pd.DataFrame()
                sf_table = pd.DataFrame()

            else:
                if df['Birth'].iloc[0]:
                    birth = df['Birth'].iloc[0]
                    today = datetime.date.today()
                    base_age = today.year - birth.year
                    day_delta = today - datetime.date(today.year, birth.month, birth.day)
                    year_delta = math.floor(day_delta.days / 365 * 10) / 10
                    age = base_age + year_delta
                else:
                    age = ""
                id = df['Name'].iloc[0]
                country = df['Country'].iloc[0]

                df = df[df['Level'] != 'United Cup']
                df = df[df['Level'] != 'Atp Cup']
                df = df[df['Level'] != 'Davis Cup']
                df['poi'] = df['Level'].apply(lambda x: level[x.strip()])
                df = df.sort_values(['poi'],ascending=False)

                w_table = df[df['Round']=='W']
                f_table = df[df['Round']=='F']
                sf_table = df[df['Round']=='SF']

                lst = []
                for info in w_table.values:
                    lst.append((info[5],color[info[7].strip()], info[6], color[info[6].strip()]))
                w_table = lst

                lst = []
                for info in f_table.values:
                    lst.append((info[5], color[info[7].strip()], info[6], color[info[6].strip()]))
                f_table = lst

                lst = []
                for info in sf_table.values:
                    lst.append((info[5], color[info[7].strip()], info[6], color[info[6].strip()]))
                sf_table = lst

            if len(id)>17:
                idx = id.rfind(' ')
                name = id[0]+'.'+id[idx:]
            else:
                name = id
            point = item[3]
            dic = {'rank': rank, 'Name':name, 'point': point, 'age': age, 'Country':country, 'W':w_table, 'F': f_table, 'SF': sf_table, 'id':id }
            rank = rank + 1
            table.append(dic)

        return render_template('Last52Week.html',data = table, Date = Date, user=user)
        #return redirect(url_for("result_title", name='Novak Djokovic', year=2023))
    else:
        data = request.form.to_dict()
        PlayerName = data['player_name'].strip()
        if data['year']=='Career':
            TargetYear = 0
        elif data['year'] == 'Last 52 Weeks':
            TargetYear = 1
        else:
            TargetYear = int(data['year'])
        #print(PlayerName,TargetYear)
        return redirect(url_for("result_title",name=PlayerName,year=TargetYear))

@app.route('/performance_view?player=<player>&year=<year>&Type=<court>&special=<special>')
def performance_view(player,year,court,special):
    #print(player,year)
    user = getusername()
    tour_dic = {'ATP250': './static/level/ATP250.png', 'ATP500': './static/level/ATP500.png',
                'ATP1000': './static/level/ATP1000.png', 'Atp Cup': './static/level/Atp-Cup.png',
                'Tour Final': './static/level/Tour-Final.png',
                'United Cup': './static/level/United-Cup.png',
                'Davis Cup': './static/level/Davis-Cup.png',
                'Olympics': './static/level/OL.png',
                'Grand Slam-Australian Open': './static/level/GS-AO.png',
                'Grand Slam-Roland Garros': './static/level/GS-RG.png',
                'Grand Slam-French Open': './static/level/GS-RG.png',
                'Grand Slam-US Open': './static/level/GS-UO.png',
                'Grand Slam-Wimbledon': './static/level/GS-WC.png'}
    color = {'Hard': '#0080FF', 'Clay': '#D26900', 'Grass': '#00BB00', 'Carpet': '#D9B300', 'All': 'black'}

    def qualify2formal(q_id):
        # 寻找资格赛对应的正式赛
        cursor.execute(
            "select top 1 B.Name as 'name', B.Level as 'level',B.ID as 'tournament_id' from  Tournament as A left join Tournament as B on A.ID=convert(int,concat('99',B.ID)) where A.Level='Qualify' and A.ID=%d",
            (q_id))
        unit = cursor.fetchone()
        real_name, formal_name, formal_id = unit[0].strip(), unit[1].strip(), unit[2]
        return real_name, formal_name, formal_id

    def find_pic(real_name, formal_name):
        # 寻找赛事对应的图标
        # 设置一个默认标防止意外情况发生
        defaut = './static/level/ATP250.png'
        # print(formal_name)
        if (formal_name.strip() in tour_dic):
            # print(tour_dic[formal_name.strip()])
            return tour_dic[formal_name.strip()]
        if (real_name.strip() in tour_dic):
            return tour_dic[real_name.strip()]
        name_now = formal_name.strip() + '-' + real_name.strip()
        if (name_now in tour_dic):
            return tour_dic[name_now]
        return defaut

    def change_score(scores):
        # 输了的赛事对调比分
        score_list = scores.strip().split(' ')
        score_new = []
        for unit in score_list:
            if ('-' in unit):
                head, tail = unit.split('-')
                score_new.append(tail + '-' + head)
            else:
                score_new.append(unit)
        return ' '.join(score_new)

    def choose_head_photo(ID):
        image = "./static/Player_Photo_head/" + str(ID) + ".webp"
        img_matrix = cv.imread(image)
        if type(img_matrix) == type(None):
            image = "./static/Player_Photo_head/default.webp"
        return image

    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute("EXEC select_match %s,%d", (player,year))
    table = cursor.fetchall()

    if court in ['Hard','Clay','Grass','Carpet']:
        table = pd.DataFrame(table)
        table = table[table.iloc[:,3]==court]
        table = tuple(table.values)
    elif court in ['Grand Slam','Masters']:
        table = pd.DataFrame(table)
        if court == 'Grand Slam':
            table = table[table.iloc[:,2]==court]
        else:
            table = table[table.iloc[:,2]=='ATP1000']
        table = tuple(table.values)

    df = []
    former = None
    for item in table:
        item_l = list(item)

        if not item_l[11] or np.isnan(item_l[11]):
            item_l[11] = '    '
        else:
            item_l[11] = int(item_l[11])
        if not item_l[12] or np.isnan(item_l[12]):
            item_l[12] = '    '
        else:
            item_l[12] = int(item_l[12])


        item_l[5] = item_l[5].strip()  # 去除获胜球员后面的空格
        if (item_l[2].strip() == 'Qualify'):
            item_l[0], item_l[2], item_l[13] = qualify2formal(item_l[13])
        if (item_l[5] != player):
            # 胜者不是当前球员时对调比分
            item_l[7] = change_score(item_l[7])
        item = tuple(item_l)
        if special == 'With game 6-0':
            try:
                item_l[7].index('6-0')
            except:
                continue
        elif special == 'With game 0-6':
            try:
                item_l[7].index('0-6')
            except:
                continue
        elif special == 'After 0-1 set':
            pat = re.compile('(\d+)[(\d+)]*-(\d+)[(\d+)]*')
            s = re.findall(pat,item_l[7])
            if not s:
                continue
            elif s[0][0]>s[0][1] or len(s) == 1:
                continue
        elif special == 'After 0-2 set':
            pat = re.compile('(\d+)[(\d+)]*-(\d+)[(\d+)]*')
            s = re.findall(pat, item_l[7])
            if not s:
                continue
            elif len(s) < 3:
                continue
            elif s[0][0] > s[0][1] or s[1][0] > s[1][1]:
                continue
        elif special == 'With RET':
            pat = re.compile('(\d+)[(\d+)]*-(\d+)[(\d+)]*')
            s = re.findall(pat, item_l[7])
            if not s:
                continue
            elif not ((int(s[-1][0])<6 and int(s[-1][1])<6) or (abs(int(s[-1][0])-int(s[-1][1]))<=1 and max(int(s[-1][0]),int(s[-1][1])) not in [7,13])):
                continue
        elif special[0:6] == 'VS Top':
            pat = re.compile('\d+')
            rk = re.findall(pat,special)[0]
            rk_list = [0,10,20,50,100]
            rk = int(rk)
            idx = rk_list.index(rk)
            rk_e = rk_list[idx]
            rk_s = rk_list[idx-1]
            if item_l[5]!=player  and (type(item_l[11])==str or item_l[11]>rk_e or item_l[11]<=rk_s):
                continue
            elif item_l[5]==player and (type(item_l[12])==str or item_l[12]>rk_e or item_l[12]<=rk_s):
                continue


        now = item[13]
        title = '{}'.format(item[0].strip())
        if (now != former):
            match_loc = find_pic(item[0], item[2])
            rank = ""
            if item_l[5] == player:
                try:
                    rank = int(item_l[11])
                except:
                    pass
            else:
                try:
                    rank = int(item_l[12])
                except:
                    pass
            if item_l[14] == None:
                date = ""
            else:
                date = item_l[14]
            if item[3] == None:
                df.append((0, title, match_loc, 'black', rank, date))  # 赛事信息
            else:
                df.append((0, title, match_loc, color[item[3].strip()], rank, date))  # 赛事信息
            df.append((1,) + item[4:])  # 赛事下每场比赛信息
            former = now
        else:
            df.append((1,) + item[4:])

    cursor.execute(
        "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country),birthday from Player where Name Like %s ",
        '%' + player + '%')
    p = cursor.fetchone()

    image = "./static/Player_Photo_full/" + str(p[1]) + ".webp"
    img_matrix = cv.imread(image)
    if type(img_matrix) == type(None):
        image = choose_head_photo(p[1])
    else:
        default_matrix = cv.imread("./static/Player_Photo_full/default.webp")
        if not np.any(img_matrix-default_matrix):
            image = choose_head_photo(p[1])

    image = [image, p[2]]
    birthday = p[3]
    age = ""
    if year != '0' and year != '1':
        age = int(year) - birthday.year
        if age<=0:
            age = ""

    connect.close()
    return render_template('performance.html', data=df, name=player, year=year, img=image,special=special, user=user,
                           playerlist=playerlist, yearlist=yearlist,age=age,court=court)


@app.route('/performance', methods=['POST', 'GET'])
def performance():
    user = getusername()
    if request.method == 'GET':
        df = []
        image = []
        player = ""
        return render_template('performance.html', name = player, data=df, img=image, playerlist=playerlist, yearlist=yearlist, user=user)
    else:
        data = request.form.to_dict()
        # print(data)
        PlayerName = data['player_name'].strip()
        if data['year']=='Last 52 Weeks':
            TargetYear = 1
        elif data['year']=='Career':
            TargetYear = 0
        else:
            TargetYear = int(data['year'])
        court = data['court']
        special = data['special']
        if not special:
            special = 1
        # print(PlayerName,TargetYear)
        return redirect(url_for("performance_view",player=PlayerName,year=TargetYear,court=court,special=special))


if __name__ == '__main__':
    global_variable()
    app.run(debug=True)
