import datetime
import math
import numpy as np
import pandas as pd
import os
import time
import pymssql
import sys
sys.path.append('../project/')
import match_result as ms
import record_tour as sm
import rank_tennis as rc
import tour_forecast as ft
from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
import re
import cv2 as cv
from wtforms import StringField,  PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, NoneOf, EqualTo

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'DontTellAnyone'


def getusername():
    user_token = request.cookies.get("token")
    pat = re.compile('_(\w+)/')
    if user_token:
        user = re.findall(pat, user_token)[0]
    else:
        user = ''
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

    global tour_list
    cursor.execute("select * from tournament_list order by Date DESC")
    tour_info = cursor.fetchall()
    column = [x[0] for x in cursor.description]
    tour_list = pd.DataFrame(tour_info, columns=column)
    color = {'ATP250': 'label label-250', 'ATP500': 'label label-500', 'ATP1000': 'label label-1000',
             'Grand Slam': 'label label-GS', 'Tour Final': 'label label-F', 'Olympics': 'label label-O',
             'United Cup': 'label label-Davis', 'NextGen Finals': 'label label-Next', 'Atp Cup': 'label label-Davis'}
    surface = {'Hard': 'label label-primary', 'Clay': 'label label-danger', 'Grass': 'label label-success',
               'Carpet': 'label label-warning', 'All': 'label'}

    def cal_part(tour):
        cursor.execute(
            "select (sum(t.KO-p.rank+1)+(max(t.KO)-Count(*))*0.25)*100.0/((1+max(t.KO))*max(t.KO)/2) from Tournament t join Participator_list p on t.ID = p.tour_id and p.rank <= t.KO where t.ID=%s",
            tour)
        part = cursor.fetchone()[0]
        if part == None:
            part = 1
        part = str(math.floor(part * 10) / 10) + '%'
        return part

    def cal_diff(tour):
        cursor.execute(
            "select rank,Level from Tournament t join result r on t.Tournament=r.tournament_id and t.year=r.year and p1_id = (select top 1 p1_id from result where tournament_id*100+year%100=%s and round = 'F') join Participator_list p on t.ID = p.tour_id and p.id = r.p2_id where t.ID=%s order by match_id",
            (tour, tour))
        diff = cursor.fetchall()
        diff = pd.DataFrame(diff, columns=['rank','level'])
        diff_ = np.sum((diff.index+5) / (5+diff['rank']))
        if diff.loc[0,'level'] == 'Grand Slam':
            diff_ = 5/3*diff_
        diff_ = round(float(diff_),3)
        return diff_

    tour_list['Date'] = tour_list['Date'].apply(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))
    tour_list['Level_class'] = tour_list['Level'].apply(lambda x: color[x])
    tour_list['Court'] = tour_list['Type'].apply(lambda x: surface[x])
    tour_list['participate'] = (tour_list['Tournament'] * 100 + tour_list['year'] % 100).apply(lambda x: cal_part(x))
    tour_list['difficulty'] = (tour_list['Tournament'] * 100 + tour_list['year'] % 100).apply(lambda x: cal_diff(x))

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

    global ntour
    ntour = []
    with open("../project/tour_list_a.txt",'r',encoding='utf-8') as f:
        line=f.readlines()
        f.close()

    now = datetime.datetime.today()
    date_now = datetime.datetime.date(now)
    num = 0
    flag=False
    for item in line:
        info = tuple(eval(item))
        if info[3]!='Qualify':
            date_start = info[7]
            date_start = datetime.date(int(date_start[0:4]),int(date_start[5:7]),int(date_start[8:10]))
            date_end = info[8]
            date_end = datetime.date(int(date_end[0:4]), int(date_end[5:7]), int(date_end[8:10]))
            if date_now >= date_start and date_now <= date_end:
                flag = True
            elif (date_now-date_start).days>-7 and (date_now-date_start).days<0:
                flag = True
            if num<5 and flag==True:
                num = num+1
                ntour.append(info)
            if num == 5:
                break

@app.errorhandler(TypeError)
def type_none_error(e):
    return "<h1 style='text-align:center'> 404 Not Found </h1><h2 style='text-align:center'> This page is not exist. Please check the url you input. </h2>"

@app.route('/')
def homepage():
    user = getusername()
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    now = datetime.datetime.today()

    def convert_eid(eid):
        if len(eid) == 3:
            eid = '0' + eid
        return eid

    cursor.execute('select top 10 (select top 1 Name from Player where ID=TOP100.ID),rank, point, Date from TOP100 where Date = (select max(Date) from TOP100) order by [rank]')
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
        item_s.append(name)
        table.append(tuple(item_s))

    cursor.execute('select top 7 ID,Name,birthday from player where [R-id] is not NULL and MONTH(birthday)=%s and Day(birthday)=%s order by (select COUNT(*) from participator_list where id=player.ID) DESC',(now.month,now.day))
    roll_birth = cursor.fetchall()
    birthplayer = []
    for item in roll_birth:
        image = './static/Player_Photo_head/'+str(item[0])+'.webp'
        if os.path.exists(image):
            img_matrix = cv.imread(image)
            if type(img_matrix) == type(None):
                image = ""
            else:
                default_matrix = cv.imread("./static/Player_Photo_head/default.webp")
                if not np.any(img_matrix - default_matrix):
                    image = ""
        else:
            image = ""
        birthplayer.append((image,item[1],item[2]))

    cursor.execute("select * from recent_championship")
    trophy = cursor.fetchall()
    trophy_pic = []

    for item in trophy:
        path = './static/trophy/'+str(item[1])+'.jpg'
        if not os.path.exists(path):
            continue
        else:
            trophy_pic.append((path,item[2],item[3],item[0]))

    tour_pic = []
    for item in ntour:
        path = './static/Tournament/'+convert_eid(str(item[0]//100))+'.png'
        if not os.path.exists(path):
            path = './static/level/'+item[3]+'.png'
        tour_pic.append((path,item[2]))


    cursor.execute("select * from Record_Win")
    win = cursor.fetchall()
    winplayer = []
    for item in win:
        cursor.execute("select Name from Tournament where sequence+Year*100=%s",item[2])
        tour = cursor.fetchall()[0]
        winplayer.append((item[0],item[1],tour[0]))

    connect.close()
    return render_template('homepage.html',user = user,playerlist=playerlist,data = table,birthplayer = birthplayer,pic = trophy_pic, win = winplayer, tour=tour_pic)

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
        connect.close()
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

class LoginForm(FlaskForm):
    connect = pymssql.connect(server='localhost', user='guest', password='visit', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute("select username from user_info")
    user = cursor.fetchall()
    user = [x[0] for x in user]
    username = StringField('Username', [DataRequired('Username is required!'), Length(min=3, max=20, message='The length of username must between 3 to 20'),NoneOf(user,message="username has existed!")])
    email = StringField(u'Email', validators=[DataRequired(message=u"email can't be empty"), Length(1, 64), Email(message=u'Please input email, for example: username@domain.com')])
    password = PasswordField(u'Password', validators=[DataRequired(message=u"Password can't be empty!"), Length(min=5, max=13)])
    confirm = PasswordField('Repeat Password', [DataRequired("Repeat Password can't be empty!"), EqualTo('password', message='Password must be same!')])
    submit = SubmitField(u'Register')

@app.route("/signup", methods=["GET","POST"])
def register():
    form =LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = form.username.data
        print (f"email: {email}s password: {password}s" )
        red = redirect('/')

        connect = pymssql.connect(server='localhost', user='guest', password='visit', database='atp-tennis',
                                  charset='utf8')
        cursor = connect.cursor()
        cursor.execute("select max(ID) from user_info")
        maxid = cursor.fetchone()[0]
        cursor.execute("insert user_info Values(%s,%s,%s,%s,%s,%s,%s,%s)",(user,password,email,'Norm',0,0,0,maxid+1))
        cookie_data = 'hkh78y12$%f' + "_" + user + "/udbek"
        red.set_cookie("token", cookie_data)
        connect.commit()
        connect.close()
        return red
    else:
        return render_template("signup.html", form=form)

@app.route('/subres',methods=['POST'])
def submit():
    user = getusername()
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute("select ID from user_info where UserName=%s",user)
    id = cursor.fetchone()[0]
    now = datetime.datetime.now()
    date = datetime.datetime.strftime(now,"%Y-%m-%d")
    cursor.execute(
        "select (select top 1 Name from Player where ID = winner) name, winner,loser from user_choice where Date = %s and user_id = %s",
        (date, id))
    flag = cursor.fetchall()
    if flag:
        connect.close()
        return 'no'
    data = request.form.to_dict()
    html = data['submit']
    pat = re.compile('<td>(\w+\s?\w+\s?\w*)</td><td class="\w+er" id="([A-Za-z\s.-]+)">\D+</td><td>vs</td><td class="(\w+er)" id="([A-Za-z\s.-]+)')
    data = re.findall(pat,html)
    year = now.year
    num = 0
    tour = ""
    for item in data:
        num = num + 1
        if item[2]=='loser':
            choose = item[1]
            nchoose = item[3]
        else:
            choose = item[3]
            nchoose = item[1]
        if item[0] != tour:
            cursor.execute('select Tournament from Tournament where Name = %s',item[0])
            eid = cursor.fetchone()[0]*100+year%100
            num = 1
            tour = item[0]

        cursor.execute('select ID from Player where Name = %s', choose)
        try:
            choose = cursor.fetchone()[0]
        except:
            print(choose)
            continue
        cursor.execute('select ID from Player where Name = %s', nchoose)
        try:
            nchoose = cursor.fetchone()[0]
        except:
            print(nchoose)
            continue

        cursor.execute("Insert user_choice Values(%s,%s,%s,%s,%s,%s,%s)",(id,eid,None,choose,nchoose,None,date))
        connect.commit()
    connect.close()
    return "yes"


@app.route('/Daily')
def daily():
    user = getusername()
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute("select * from user_info where UserName = %s", user)
    info = cursor.fetchone()

    filelist = []
    for filename in os.listdir("D:\Git\learnskill\Forecast Result"):
        filelist.append(filename)
    max_mtime = 0
    file_ = []
    for fname in filelist:
        full_path = os.path.join("D:\Git\learnskill\Forecast Result", fname)
        mtime = os.stat(full_path).st_mtime
        if mtime//1000 > max_mtime:
            stime = mtime
            max_mtime = mtime//1000
            max_file = fname
            file_ = [max_file]
        elif mtime//1000 == max_mtime:
            file_.append(fname)
    date = time.strftime("%Y-%m-%d", time.localtime(stime))
    player_list = []
    for max_file in file_:
        full_path = os.path.join("D:\Git\learnskill\Forecast Result", max_file)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.readlines()
        flag = 0
        for i in range(len(content)):
            if content[i][:4] == '####':
                flag = flag + 1
            if flag == 2:
                break
            if '*' in content[i]:
                tour = content[i][2:-3]
            elif 'vs' in content[i]:
                p1,p2 = content[i].split('vs')
                p1 = p1.strip()
                p2 = p2.strip()

                cursor.execute('EXEC headtohead %s,%s',(p1,p2))
                h2h = cursor.fetchall()
                column = cursor.description
                column = [x[0] for x in column]
                h2h = pd.DataFrame(h2h,columns=column)
                h2h = h2h[h2h['result']!='W/O']
                w1, w2 = len(h2h[h2h['winner']==p1]),len(h2h[h2h['winner']==p2])
                player_list.append([tour,p1,p2,w1,w2])

    cursor.execute("select (select top 1 Name from Player where ID = winner) name, winner,loser from user_choice where Date = %s and user_id = %s",(date,info[7]))
    flag = cursor.fetchall()
    connect.close()
    if not flag:
        flag = 1
    else:
        dic = flag
        flag = 0
        for i in range(len(dic)):
            for j in range(len(player_list)):
                if dic[i][0] == player_list[j][1]:
                    player_list[j].append(0)
                elif dic[i][0] == player_list[j][2]:
                    player_list[j].append(1)

    print(flag)
    return render_template('Daily.html',info=info,user=user,table = player_list, time = date, flag=flag, playerlist=playerlist)

@app.route('/sqlquery',methods=['POST','GET'])
def Query():
    data = request.form.to_dict()
    sql = data['query']
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute(sql)
    if data['type'] == 'select':
        if sql[0:4] == 'EXEC' or sql[0:4] == 'sele' or sql[0:4] == 'SELE':
            table = cursor.fetchall()
            data = []
            head = []
            dtype = []
            for item in cursor.description:
                head.append(item[0])
                dtype.append(item[1])
            data.append(head)
            date_type = [i for i in range(len(dtype)) if dtype[i] == 2]
            char_type = [i for i in range(len(dtype)) if dtype[i] == 1]
            for item in table:
                item_ = list(item)
                for i in date_type:
                    if item_[i] != None:
                        item_[i] = datetime.datetime.strftime(item_[i], '%Y-%m-%d')
                for i in char_type:
                    if item_[i] != None:
                        item_[i] = item_[i].encode('latin1').decode('gbk')
                data.append(item_)
    else:
        connect.commit()
    connect.close()

    return data

@app.route('/update',methods=['POST', 'GET'])
def update():
    data = request.form.to_dict()
    type = data['name']
    if type == 'Record':
        try:
            rc.main()
        except:
            return 'fail'
        return 'success'
    elif type == 'Forecast':
        try:
            ft.main()
        except:
            return 'fail'
        return 'success'
    elif type == 'Summary':
        try:
            code = sm.main()
        except:
            return 'fail'
        return code
    else:
        return 'fail'

@app.route('/center')
def center():
    user = getusername()
    if user != 'Rhine':
        return "<h1 style='text-align:center'> You have no authority! </h1>"
    else:
        return render_template('center.html',user=user, playerlist=playerlist)

@app.route('/stats',methods=['POST'])
def stats():
    data = request.form.to_dict()
    eid = data['eid']
    year = data['year']
    mid = data['match_id']
    tournament_id = int(eid)*100+int(year)%100
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute("select * from Match_stats where tournament_id = %s and match_id=%s",(tournament_id,mid))
    data = cursor.fetchone()
    #label = ['ACE','Double Fault','1st Serve','1st Serve Won','2nd Serve Won','Break Point','Break Point Convert','1st Return Won','2nd Return Won','Total Points Won']
    if data == None:
        data = []
    else:
        data = list(data)
    connect.close()
    return data

@app.route('/h2h_query?P1=<player1>&P2=<player2>&Court_type=<court>&Level=<level>')
def h2h_query(player1,player2,court,level):
    color = {'ATP250': 'label label-250', 'ATP500': 'label label-500', 'ATP1000': 'label label-1000', 'Grand Slam': 'label label-GS', 'Atp Cup': 'label label-Cup', 'United Cup': 'label label-Cup', 'Davis Cup': 'label label-Davis', 'Laver Cup': 'label label-Laver', 'Tour Final': 'label label-F', 'NextGen Finals': 'label label-Next', 'Olympics': 'label label-O', 'Qualify': 'label label-Q'
             , 'F': 'label label-Fi', 'SF': 'label label-SF', 'BR': 'label label-SF', 'CF': 'label label-SF', 'QF': 'label label-QF', 'R1': 'label label-R', 'R2': 'label label-R', 'R3': 'label label-R', 'R4': 'label label-R', 'R128': 'label label-R', 'R64': 'label label-R', 'R32': 'label label-R', 'R16': 'label label-R', 'Q1': 'label label-R', 'Q2': 'label label-R', 'Q3': 'label label-R', 'RR': 'label label-R', 'PO': 'label label-R'}

    user = getusername()
    PlayerName = [player1, player2]

    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()

    if player2 in countrylist:
        cursor.execute("EXEC headtohead_country %s,%s", (PlayerName[0], PlayerName[1]))
    elif player2 >'0' and player2 < '9999' :
        cursor.execute("EXEC headtohead_top %s,%s", (PlayerName[0], PlayerName[1]))
    else:
        cursor.execute("EXEC headtohead %s,%s", (PlayerName[0], PlayerName[1]))

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
        "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country) from Player where Name = %s ", PlayerName[0])
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
    elif player2 > '0' and player2 < '9999':
        name.append(PlayerName[1])
        image_2 = "./static/Player_Photo_head/default.webp"
        country.append("")
        image = [image_1, image_2]
        flag = 2
    else:
        cursor.execute(
            "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country) from Player where Name = %s ",
            PlayerName[1])
        p2 = cursor.fetchone()
        name.append(p2[0].strip())
        image_2 = "./static/Player_Photo_head/" + str(p2[1]) + ".webp"
        img_matrix = cv.imread(image_2)
        if type(img_matrix) == type(None):
            image_2 = "./static/Player_Photo_head/default.webp"
        country.append(p2[2])
        image = [image_1, image_2]
        flag = 0

    Num = 15
    if len(table)%Num==0:
        tpage = len(table)//Num
    else:
        tpage = len(table)//Num+1
    table_=table

    connect.close()
    return render_template('h2h.html', data=table_, name=name, img=image, playerlist=playerlist, countrylist = countrylist, country=country,
                           user=user, flag=flag, countrystr= countrystr, playerstr=playerstr,tp = tpage, court=court, level=level, win=win, lose=lose)


@app.route('/h2h',methods=['POST','GET'])
def h2h():
    user = getusername()
    if request.method == 'GET':
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

@app.route('/forecast_simulation', methods=['POST'])
def simulation():
    data = request.form.to_dict()
    print(data)
    p1 = data['player1']
    p2 = data['player2']
    court = data['surface']
    speed = int(data['speed'])
    mode = 3
    wp, result_str = ms.start(p1, p2, court, speed, mode, None, None, 0)
    result_str = result_str.replace('\n','*')

    return result_str

@app.route('/forecast_view?P1=<player1>&P2=<player2>&Type=<court>&speed=<speed>')
def forecast_view(player1,player2,court,speed):
    user = getusername()
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()

    cursor.execute(
        "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country) from Player where Name = %s ", player1)
    p1 = cursor.fetchone()
    name = [p1[0].strip()]
    image_1 = "./static/Player_Photo_head/" + str(p1[1]) + ".webp"
    img_matrix = cv.imread(image_1)
    if type(img_matrix) == type(None):
        image_1 = "./static/Player_Photo_head/default.webp"
    country = [p1[2]]
    cursor.execute(
        "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country) from Player where Name = %s ", player2)
    p2 = cursor.fetchone()
    name.append(p2[0].strip())
    image_2 = "./static/Player_Photo_head/" + str(p2[1]) + ".webp"
    img_matrix = cv.imread(image_2)
    if type(img_matrix) == type(None):
        image_2 = "./static/Player_Photo_head/default.webp"
    country.append(p2[2])
    image = [image_1, image_2]
    cursor.execute('EXEC headtohead %s,%s', (player1, player2))
    h2h = cursor.fetchall()
    h2h = pd.DataFrame(h2h)
    if h2h.empty:
        w1, w2 = 0, 0
    else:
        drop_index = [i for i in range(len(h2h)) if 'W' in h2h[7][i]]
        h2h = h2h.drop(index=drop_index)
        w1 = len(h2h[h2h[5] == player1])
        w2 = len(h2h[h2h[5] == player2])

    return render_template("forecast.html", user=user, playerlist=playerlist, img=image, name=name, country=country, win=w1,
                    lose=w2,court=court,speed=speed)

@app.route('/forecast',methods=['POST','GET'])
def forecast():
    user = getusername()
    if user != '':
        if request.method == 'GET':
            return render_template("forecast.html",user=user,playerlist = playerlist, img=['',''],name=['',''],country=['',''],win='',lose='')
        else:
            data = request.form.to_dict()
            p1 = data['player1']
            p2 = data['player2']
            court = data['court_type']
            speed = int(data['speed'])
            return redirect(url_for("forecast_view", player1=p1, player2=p2, court=court, speed=speed))

    else:
        return redirect('/login')


@app.route('/profile_detail?Name=<Name>')
def profile_detail(Name):
    user = getusername()

    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis', charset='utf8')
    cursor = connect.cursor()

    color = {'ATP250': 'label label-250', 'ATP500': 'label label-500', 'ATP1000': 'label label-1000',
             'Grand Slam': 'label label-GS', 'Tour Final': 'label label-F', 'Olympics': 'label label-O',
             'Davis Cup': 'label label-Davis', 'NextGen Finals': 'label label-Next',
             'Qualify': 'label label-Q', 'United Cup': 'label label-Davis', 'ATP Cup': 'label label-Davis',
             'Hard':'label label-primary', 'Clay':'label label-danger','Grass': 'label label-success',
             'W': 'label label-W', 'F': 'label label-Fi', 'SF': 'label label-SF', 'BR': 'label label-SF',
             'CF': 'label label-SF',
             'QF': 'label label-QF', 'R1': 'label label-R', 'R2': 'label label-R', 'R3': 'label label-RD',
             'R4': 'label label-RD', 'Q1': 'label label-Qy', 'Q2': 'label label-Qy', 'Q3': 'label label-Qy',
             'RR': 'label label-R', 'PO': 'label label-R', 'ER': 'label label-R'}
    level_style = {'ATP250': '#ACD6FF', 'ATP500': '#D2A2CC', 'ATP1000': '#FFA042',
             'Grand Slam': '#FF2D2D', 'Tour Final': '#EAC100', 'Olympics': '#00DB00',
             'Davis Cup': '#ffa6ff', 'NextGen Finals': '#BEBEBE'}

    def h2h_title_result_summary():
        cursor.execute("EXEC Player_Appear %s,0", Name)
        table = cursor.fetchall()
        level_std = {'ATP1000':100,'ATP250':25,'ATP500':50,"Grand Slam":200,'Tour Final':150,'Olympics':80,'NextGen Finals':0}
        df = pd.DataFrame(table, columns=['Date', 'Tour', 'Type', 'Level', 'Round', 'tourid'])
        champion_level = {}
        df = df[df['Level'] != 'United Cup']
        df = df[df['Level'] != 'Atp Cup']
        df = df[df['Level'] != 'Davis Cup']
        tmp = df[df['Round'] == 'W']
        tmp['lev'] = tmp['Level'].apply(lambda x:level_std[x])
        tmp['style'] = tmp['Level'].apply(lambda x:level_style[x])
        level_count = tmp[['Level','Round','lev','style']].groupby(['Level']).agg({'Round':'count','lev':'mean','style':'last'})
        level_count = level_count.sort_values(['lev'],ascending=False)
        for i in range(len(level_count)):
            court = level_count.index[i]
            count = level_count.iloc[i, 0]
            color_style = level_count.iloc[i,2]
            champion_level[court] = (color[court],count,color_style)

        df = df[df['Level'] != 'NextGen Finals']
        df = df[df['Level'] != 'Laver Cup']
        champion_type = {}
        temp = df[df['Round'] == 'W']
        type_count = temp.groupby(['Type']).agg(['count'])
        for i in range(len(type_count)):
            court = type_count.index[i]
            count = type_count.iloc[i, 0]
            champion_type[court] = count

        cursor.execute("EXEC select_match %s,0",Name)
        df = cursor.fetchall()
        column = ['tour', 'year', 'level', 'type', 'round', 'p1', 'p2', 'result', 'speed', 'c1', 'c2', 'r1', 'r2', 'tid',
                  'date', 'm1','m2']
        df = pd.DataFrame(df, columns=column)
        drop_index = [i for i in range(len(df)) if 'W' in df['result'][i]]
        df = df.drop(index=drop_index)
        win = df[df['p1'] == Name]
        loss = df[df['p2'] == Name]
        win = win.groupby(['p2']).agg(['count'])[('p1', 'count')]
        loss = loss.groupby(['p1']).agg(['count'])[('p2', 'count')]
        summary = pd.DataFrame(win)
        summary.columns = ['win']
        loss = pd.DataFrame(loss)
        loss.columns = ['loss']
        summary = summary.merge(loss, left_index=True, right_index=True, how='outer').fillna(0)
        lead = summary[summary['win'] > summary['loss']]
        tail = summary[summary['win'] < summary['loss']]
        tie = summary[summary['win'] == summary['loss']]

        df = df[df['level'] != 'Qualify']
        Type = ['Hard', 'Clay', 'Grass', 'Carpet']
        rate = []
        for t in Type:
            if t not in champion_type.keys():
                champion_type[t] = 0
            hd = df[df['type'] == t]
            if hd.empty == True:
                rate.append(0.0)
                rate.append(0)
                rate.append(0)
            else:
                winner = len(hd[hd['p1'] == Name]) / len(hd)
                winner = round(winner * 100, 2)
                rate.append(winner)
                rate.append(len(hd[hd['p1'] == Name]))
                rate.append(len(hd) - rate[-1])
        win_rate = (rate[1]+rate[4]+rate[7]+rate[10])/len(df)
        win_rate = round(win_rate * 100, 2)
        rate.append(win_rate)
        rate.append(rate[1]+rate[4]+rate[7]+rate[10])
        rate.append(len(df)-(rate[1]+rate[4]+rate[7]+rate[10]))

        return lead,tail,tie,champion_type,rate,champion_level

    def cal_age(birth):
        if birth:
            today = datetime.date.today()
            base_age = today.year - birth.year
            day_delta = today - datetime.date(today.year, birth.month, birth.day)
            year_delta = math.floor(abs(day_delta.days) / 365 * 10) / 10
            age = base_age + year_delta
        else:
            age = ""
        return age

    def choose_head_photo(ID):
        image = "./static/Player_Photo_full/" + str(ID) + ".webp"
        img_matrix = cv.imread(image)
        default_matrix = cv.imread("./static/Player_Photo_full/default.webp")
        if not np.any(img_matrix - default_matrix):
            image = "./static/Player_Photo_head/" + str(ID) + ".webp"
        return image

    def cal_special(max_rate,rate):
        return (max_rate-rate)/max_rate*0.5+(max_rate-rate)/(1-rate)*0.5

    cursor.execute("select top 1 p.ID, p.Name as Name, Height, p.country as Country,country_code, Last_Appearance, birthday, t.Name Tour, t.Tournament tourid, t.year as year, round, Level from Player p join Country c on p.country = c.country join Tournament t on p.Last_Appearance = t.Date join result r on r.tournament_id*100+r.year%100 = t.ID and (r.p1_id=p.ID or r.p2_id=p.ID) where p.Name = %s order by match_id DESC",Name)
    info = cursor.fetchone()

    info = [info]
    column = cursor.description
    column = [x[0] for x in column]
    info = pd.DataFrame(info,columns=column)
    birth = info.loc[0,'birthday']
    age = cal_age(info.loc[0,'birthday'])
    Name = info.loc[0,'Name']
    Last_appearance = info.loc[0,'Last_Appearance']
    Height = info.loc[0,'Height']
    Country = info.loc[0,'Country']
    Tour = info.loc[0,'Tour']
    tourid = info.loc[0,'tourid']
    year = info.loc[0,'year']
    Round = info.loc[0,'round']
    round_style = color[Round]
    Level = color[info.loc[0,'Level']]
    photo = choose_head_photo(info.loc[0,'ID'])
    flag = info.loc[0,'country_code']
    lead, tail, tie, champion_type, rate,champion_level = h2h_title_result_summary()
    hard,clay,grass = rate[0],rate[3],rate[6]
    surface = ['Hard','Clay','Grass']
    surface_rate = [hard,clay,grass]
    max_rate = max(surface_rate)
    surface = surface[surface_rate.index(max_rate)]
    surface_type = color[surface]
    surface_rate.pop(surface_rate.index(max_rate))
    special = 0
    for r in surface_rate:
        special = special + cal_special(max_rate/100,r/100)
    special = round(special/2,3)*100

    info = {'age':age,'Name':Name,'Height':Height,'birth': birth,'Tour':Tour,'tourid':tourid,'year':year,'Round':Round,'flag':flag,'Photo':photo,'Country':Country,'Last appear':Last_appearance,'Level':Level,'lead':lead,'lead_num':len(lead),'tail':tail,'tail_num':len(tail),'tie':tie,'tie_num':len(tie),'champion':champion_type,'champion_level':champion_level,'rate':rate,'surface':surface,'round_style':round_style,'surface_style':surface_type,'special':special}
    #print(info['rate'])
    return render_template("profile.html",user=user,playerlist=playerlist,info=info)

@app.route('/profile',methods=['POST','GET'])
def profile():
    user = getusername()
    color = {'ATP250': 'label label-250', 'ATP500': 'label label-500', 'ATP1000': 'label label-1000',
             'Grand Slam': 'label label-GS', 'Tour Final': 'label label-F', 'Olympics': 'label label-O',
             'Davis Cup': 'label label-Davis', 'NextGen Finals': 'label label-Next',
             'Qualify': 'label label-Q',
             'W': 'label label-W', 'F': 'label label-Fi', 'SF': 'label label-SF', 'BR': 'label label-SF',
             'CF': 'label label-SF',
             'QF': 'label label-QF', 'R1': 'label label-R', 'R2': 'label label-R', 'R3': 'label label-RD',
             'R4': 'label label-RD', 'Q1': 'label label-Qy', 'Q2': 'label label-Qy', 'Q3': 'label label-Qy',
             'RR': 'label label-R', 'PO': 'label label-R', 'ER': 'label label-R'}

    def next_round(round,KO,flag):
        if flag == 'L' or (round[0] == 'Q' and round[1] != 'F'):
            return round
        if round == 'R4':
            return 'QF'
        elif round == 'QF':
            return 'SF'
        elif round == 'SF':
            return 'F'
        elif round == 'F':
            return 'W'
        elif round == 'R1':
            return 'R2'
        k = 16
        while k<KO:
            k = k*2
        if round == 'R2':
            k = k/4
            if k>=16:
                return 'R3'
            else:
                return 'QF'
        elif round == 'R3':
            k = k/8
            if k>=16:
                return 'R4'
            else:
                return 'QF'

    def cal_age(birth):
        if birth:
            today = datetime.date.today()
            base_age = today.year - birth.year
            day_delta = today - datetime.date(today.year, birth.month, birth.day)
            year_delta = math.floor(abs(day_delta.days) / 365 * 10) / 10
            age = base_age + year_delta
        else:
            age = ""
        return age

    def process_result(score_str):
        if score_str == 'W/O':
            return '0:0 (W/O)'
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
        result = str(set_1) + ":" + str(set_2)
        if flag <= 0:
            result = result + ' (RET)'

        return result

    if request.method == 'GET':
        connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                                  charset='utf8')
        cursor = connect.cursor()
        cursor.execute("select * from Top100_profile where rn = 1 order by rank")
        df = cursor.fetchall()
        column = cursor.description
        column = [x[0] for x in column]
        df = pd.DataFrame(df,columns=column)
        df['W/L'] = (df['p1_id'] == df['ID'])
        df['W/L'] = df['W/L'].apply(lambda x: 'W' if x==True else 'L')
        df['birthday'] = df['birthday'].apply(lambda x:cal_age(x))
        df['result'] = df['result'].apply(lambda x:process_result(x))
        df['Level'] = df['Level'].apply(lambda x:color[x])
        df['round'] = df[['round','KO','W/L']].apply(lambda x:next_round(x['round'],x['KO'],x['W/L']),axis=1)
        df['round_style'] = df['round'].apply(lambda x: color[x])

        return render_template('profile_list.html',user=user,data=df,playerlist=playerlist)

    else:
        data = request.form.to_dict()
        name = data['player']
        return redirect(url_for("profile_detail", Name = name))

@app.route('/event')
def event():
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute("EXEC Player_Appear %s,%s",('Novak Djokovic',2023))
    df = cursor.fetchall()
    print(df)
    column = cursor.description
    column = [x[0] for x in column]
    df = pd.DataFrame(df,columns=column)
    df['Date'] = df['Date'].apply(lambda x: datetime.datetime.strftime(x,'%Y-%m-%d'))
    df = df.merge(tour_list,how='inner',left_on=['Date','Tour'],right_on=['Date','Name'])
    print(df)

    connect.close()
    pass

@app.route('/tournament?Tour=<tour>&Year=<year>')
def tournament(tour,year):
    user = getusername()
    tour_dic = {'ATP250': './static/level/ATP250.png', 'ATP500': './static/level/ATP500.png',
                'ATP1000': './static/level/ATP1000.png', 'Atp Cup': './static/level/Atp-Cup.png',
                'Tour Final': './static/level/Tour-Final.png',
                'United Cup': './static/level/United-Cup.png',
                'Davis Cup': './static/level/Davis-Cup.png',
                'Olympics': './static/level/OL.png',
                'Laver Cup': './static/level/Laver-Cup.png' ,
                'NextGen Finals': './static/level/Nextgen-Final.png' ,
                'Grand Slam-Australian Open': './static/level/GS-AO.png',
                'Grand Slam-Roland Garros': './static/level/GS-RG.png',
                'Grand Slam-French Open': './static/level/GS-RG.png',
                'Grand Slam-US Open': './static/level/GS-UO.png',
                'Grand Slam-Wimbledon': './static/level/GS-WC.png'}

    level_rank = {'QF': 80, 'R1': 40, 'R2': 50, 'R4': 70, 'R3': 60, 'F': 100, 'CF': 50,
                  'Q1': 0, 'ER': 20, 'BR': 95, 'SF': 90, 'PO': 60, 'Q3': 20, 'RR': 30, 'Q2': 10}

    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    # 赛事列表

    def score_process(table_tour,level):
        # 对比分的预处理函数
        table_tour_dic = {}
        # 将比分拆开
        for unit in table_tour:
            try:
                unit[3], unit[6] = int(unit[3]), int(unit[6])
            except:
                if np.isnan(unit[3]):
                    unit[3] = ''
                if np.isnan(unit[6]):
                    unit[6] = ''

            unit[-3] = unit[-3].strip()
            unit[-3] = unit[-3].replace('Played and unfinished','RET')
            if 'RET' not in unit[-3]:
                pat = re.compile('(\d+)[(\d+)]*-(\d+)[(\d+)]*$')
                test = re.findall(pat,unit[-3])
                if test != []:
                    test = test[0]
                    p1, p2 = test[0], test[1]
                    if level != 'NextGen Finals':
                        if int(p1)<6:
                            unit[-3] = unit[-3]+' RET'
                        elif p1=='6' and p2>='5':
                            unit[-3] = unit[-3]+' RET'
                        elif int(p1)-int(p2)<=1 and p1 != '7' and p1 != '13':
                            unit[-3] = unit[-3] + ' RET'
                    else:
                        if p1 != '4':
                            unit[-3] = unit[-3] + ' RET'
            pex = ''
            while len(unit[2])>22:
                op = unit[2][len(pex):]
                ix = op.index(" ")
                pex = pex + op[0]+'. '
                unit[2] = pex+op[ix+1:]
            pex = ''
            while len(unit[5])>22:
                op = unit[5][len(pex):]
                ix = op.index(" ")
                pex = pex + op[0] + '. '
                unit[5] = pex+op[ix+1:]
            unit = tuple(unit)
            # 判断比赛轮次是否变化
            if (unit[0] not in table_tour_dic.keys()):
                table_tour_dic[unit[0]] = []

            scores = unit[-3].split(' ')
            # 用空格补齐缺少场数
            if 'Grand Slam' in level:
                score_win = [[' '] for _ in range(5 - len(scores))]
                score_lose = [[' '] for _ in range(5 - len(scores))]
            else:
                score_win = [[' '] for _ in range(3 - len(scores))]
                score_lose = [[' '] for _ in range(3 - len(scores))]
            for score in scores:
                if ('-' in score):
                    w, l = score.split('-')
                elif score=='W/O':
                    w, l = score, ''
                elif score=='RET':
                    w, l = '', score
                else:
                    w, l = '', ''
                if '(' in w:
                    w1,w2=w.split('(')
                    w2 = w2[:-1]
                    w=[w1,w2]
                else:
                    w= [w]
                if '(' in l:
                    l1,l2=l.split('(')
                    l2 = l2[:-1]
                    l=[l1,l2]
                    if l1>w[0]:
                        w=[w[0],l2]
                        l=[l1]
                else:
                    l=[l]
                score_win.append(w)
                score_lose.append(l)
            unit_new = unit[:-3] + ([unit[-2],unit[-1]], [score_win, score_lose])
            table_tour_dic[unit[0]].append(unit_new)
        return table_tour_dic

    cursor.execute("select top 1 * from Tournament where Tournament=%s and year=%d", (tour, year))
    table = cursor.fetchone()
    # if not table:
    #     return "<h1 style='text-align:center'> 404 Not Found </h1><h2 style='text-align:center'> This page is not exist. Please check the url you input. </h2>"
    tour_name = table[2]
    tour_type = table[3]
    court = table[4]
    date = table[-2]
    if date == None:
        date = ''
    else:
        date = datetime.datetime.strftime(date,'%Y-%m-%d')
    if tour_type=='Grand Slam':
        tour_type = tour_type + '-'+tour_name
    tour_img = tour_dic[tour_type]

    name_img = './static/Tournament/' + '%04d' % int(tour) + '.png'  # 赛事图片
    if (not os.path.exists(name_img)):
        # 图片不存在默认用第一张
        name_img = ''

    cursor.execute('select distinct year from Tournament where Tournament=%s', tour)
    yearlist = [unit[0] for unit in cursor.fetchall()]
    yearlist.sort(reverse=True)
    # 正式赛数据
    cursor.execute('Exec Tournament_Result %d,%d', (tour, year))
    table_tour = cursor.fetchall()
    # 资格赛数据
    cursor.execute('Exec Tournament_Result %d,%d', (int('99' + str(tour)), year))
    table_tour_q = cursor.fetchall()
    # 合并正式赛和资格赛
    table_tour = table_tour_q + table_tour

    # 比赛重排序
    df = pd.DataFrame(table_tour)
    df['rank'] = df[0].apply(lambda x: level_rank[x])
    df = df.sort_values(['rank'],ascending=False)
    df = df.drop(columns=['rank'])
    # 转化为字典输出
    table_tour_dic = score_process(df.values,tour_type)

    connect.close()
    return render_template('tournament.html', user=user, data=table_tour_dic, tour_name=tour_name, year=year, img=tour_img,
                           tour_court=court, tour_type=tour_type, name_img=name_img, eid=tour, playerlist=playerlist,
                           yearlist=yearlist, date=date)

@app.route('/tournament')
def tournament_list():
    user = getusername()
    total_page = len(tour_list)//25 if len(tour_list)%25 == 0 else len(tour_list)//25+1
    table = []
    for item in tour_list.values:
        table.append(tuple(item))
    print(total_page)
    return render_template('tournament_list.html',user=user, data = table,tp=total_page,playerlist=playerlist)

@app.route('/player_year_check',methods=['POST'])
def player_year_check():
    data = request.form.to_dict()
    print(data)
    type = data['type']
    check_item = data[type]
    connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                              charset='utf8')
    cursor = connect.cursor()
    cursor.execute("select ID from Player where Name = %s",check_item)
    check_item = cursor.fetchone()
    if check_item != None:
        check_item = check_item[0]
    else:
        check_item = 0
    cursor.execute("select distinct year from result where p1_id=%s or p2_id=%s order by year DESC",(check_item,check_item))
    data = cursor.fetchall()
    connect.close()
    return data


@app.route('/result_title?name=<name>&year=<year>')
def result_title(name,year):
    user = getusername()
    if name not in playerlist:
        return "<h1 style='text-align:center'> 404 Not Found </h1><h2 style='text-align:center'> This page is not exist. Please check the url you input. </h2>"

    color = {'ATP250': 'label label-250', 'ATP500': 'label label-500', 'ATP1000': 'label label-1000',
             'Grand Slam': 'label label-GS', 'Tour Final': 'label label-F', 'Olympics': 'label label-O',
             'Davis Cup': 'label label-Davis','NextGen Finals': 'label label-Next',
             'Qualify': 'label label-Q',
             'W': 'label label-W', 'F': 'label label-Fi', 'SF': 'label label-SF', 'BR': 'label label-SF', 'CF': 'label label-SF',
             'QF': 'label label-QF', 'R1': 'label label-R', 'R2': 'label label-R', 'R3': 'label label-RD',
             'R4': 'label label-RD', 'Q1': 'label label-Qy', 'Q2': 'label label-Qy', 'Q3': 'label label-Qy',
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

    df = pd.DataFrame(table,columns=['Date','Tour','Type','Level','Round','tourid'])
    df = df[df['Level'] !='United Cup']
    df = df[df['Level'] != 'Atp Cup']
    df = df[df['Level'] != 'Davis Cup']
    df = df[df['Level'] != 'NextGen Finals']
    df = df[df['Level'] != 'Laver Cup']

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
        if len(tsp) == 1:
            if tsp.iloc[0,4] == 'SF':
                df.loc[tsp.index[0],'Round'] = 'BR'
        elif len(tsp) == 2:
            del_index = tsp[tsp['Round'] == 'BR'].index[0]
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
                if item[3] == 'Qualify':
                    item[5] = int(str(item[5])[2:])
                lst.append((item[1],color[item[3].strip()],color[r],(item[0]+datetime.timedelta(days=10)).year,item[5]))
            dic_p[r]=lst
            if r=='W':
                type_count = temp.groupby(['Type']).agg(['count'])
                for i in range(len(type_count)):
                    court = type_count.index[i]
                    count = type_count.iloc[i,0]
                    champion_type[court] = count

    #print(df)
    cursor.execute(
        "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country) from Player where Name = %s ", name)
    p = cursor.fetchone()

    cursor.execute("select distinct year from result where p1_id=%s or p2_id=%s order by year DESC",
                   (p[1], p[1]))
    yearinfo = cursor.fetchall()
    yearlist = [str(x[0]) for x in yearinfo]
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
    if table.empty:
        rate, rank = [], []
        for _ in range(4):
            rate.append(0.0)
            rank.append(0.0)
            rate.append(0)
            rank.append(0)
            rate.append(0)
            rank.append(0)
        return render_template('Result.html', data={}, name=name, year=year, rate=rate, rank_rate=rank, img=image,
                               user=user, yearlist=yearlist, playerlist=playerlist, court={'Hard':0,'Clay':0,'Grass':0})

    table.columns=['Level','Type','Round','winner','loser','result']
    drop_index = [i for i in range(len(table)) if 'W' in table['result'][i]]
    table = table.drop(index=drop_index)
    table = table[table['Level']!='Qualify']
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
    if table.empty:
        rate.append(0.0)
        rate.append(0)
        rate.append(0)
    else:
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
        cursor.execute("select * from Player_Title_52W")
        total_info = cursor.fetchall()
        total_info = pd.DataFrame(total_info, columns=['ID','Name','Country','Birth','Date', 'Tour', 'Type', 'Level', 'Round','tourid'])
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
                df = df[df['Level'] != 'NextGen Finals']
                df['poi'] = df['Level'].apply(lambda x: level[x.strip()])
                df = df.sort_values(['poi'],ascending=False)

                w_table = df[df['Round']=='W']
                f_table = df[df['Round']=='F']
                sf_table = df[df['Round']=='SF']

                lst = []
                for info in w_table.values:
                    lst.append((info[5],color[info[7].strip()], info[6], color[info[6].strip()],(info[4]+datetime.timedelta(days=10)).year,info[9]))
                w_table = lst

                lst = []

                for info in f_table.values:
                    lst.append((info[5], color[info[7].strip()], info[6], color[info[6].strip()],(info[4]+datetime.timedelta(days=10)).year,info[9]))
                f_table = lst

                lst = []
                for info in sf_table.values:
                    lst.append((info[5], color[info[7].strip()], info[6], color[info[6].strip()],(info[4]+datetime.timedelta(days=10)).year,info[9]))
                sf_table = lst

            pex = ''
            name = id
            id = id.replace("-"," ")
            while len(id) > 17:
                print(id)
                op = id[len(pex):]
                try:
                    ix = op.index(" ")
                    pex = pex + op[0] + '. '
                    id = pex + op[ix + 1:]
                except:
                    pex = pex[0:3] + pex[6:]
                    id = pex + op

            point = item[3]
            dic = {'rank': rank, 'Name':name, 'point': point, 'age': age, 'Country':country, 'W':w_table, 'F': f_table, 'SF': sf_table, 'id':id }
            rank = rank + 1
            table.append(dic)

        return render_template('Last52Week.html',data = table, Date = Date, user=user,playerlist=playerlist)
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

@app.route('/performance_view?player=<player>&year=<year>&Type=<court>&level=<level>&special=<special>')
def performance_view(player,year,court,level,special):
    #print(player,year)
    user = getusername()
    if player not in playerlist:
        return "<h1 style='text-align:center'> 404 Not Found </h1><h2 style='text-align:center'> This page is not exist. Please check the url you input. </h2>"

    tour_dic = {'ATP250': './static/level/ATP250.png', 'ATP500': './static/level/ATP500.png',
                'ATP1000': './static/level/ATP1000.png', 'Atp Cup': './static/level/Atp-Cup.png',
                'Tour Final': './static/level/Tour-Final.png',
                'NextGen Finals': './static/level/NextGen-Final.png',
                'United Cup': './static/level/United-Cup.png',
                'Davis Cup': './static/level/Davis-Cup.png',
                'Laver Cup': './static/level/Laver-Cup.png',
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
            "select top 1 B.Name as 'name', B.Level as 'level',B.ID as 'tournament_id' from Tournament as A left join Tournament as B on convert(varchar(20),A.ID)=convert(varchar(20),concat('99',B.ID)) where A.Level='Qualify' and A.ID=%d",
            (q_id))
        unit = cursor.fetchone()
        if unit[0] == None:
            if q_id%100 == datetime.datetime.now().year%100:
                year = q_id%100
                cursor.execute(
                    "select top 1 B.Name as 'name', B.Level as 'level',B.Tournament as 'tournament_id' from Tournament as A left join Tournament as B on convert(varchar(20),A.Tournament)=convert(varchar(20),concat('99',B.Tournament)) where A.Level='Qualify' and A.Tournament=%d",
                    (q_id//100))
                unit = cursor.fetchone()
                real_name, formal_name, formal_id = unit[0].strip(), unit[1].strip(), unit[2]*100+year
            else:
                return "","",q_id
        else:
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
    if level in ['Grand Slam','Masters']:
        table = pd.DataFrame(table)
        if level == 'Grand Slam':
            table = table[table.iloc[:,2]==level]
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
        "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country),birthday from Player where Name = %s ", player)
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
        if birthday != None:
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
        level = data['level']
        special = data['special']
        if not special:
            special = 1
        # print(PlayerName,TargetYear)
        return redirect(url_for("performance_view",player=PlayerName,year=TargetYear,level = level, court=court,special=special))


if __name__ == '__main__':
    global_variable()
    app.run(debug=True,port=2023)