import pymssql
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/h2h',methods=['POST','GET'])
def h2h():
    if request.method=='GET':
        PlayerName = ['Novak Djokovic', 'Carlos Alcaraz']
        connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis', charset='utf8')
        cursor = connect.cursor()
        cursor.execute("EXEC headtohead %s,%s",(PlayerName[0],PlayerName[1]))
        table = cursor.fetchall()
        cursor.execute("select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country),img from Player where Name Like %s ", '%' + PlayerName[0] + '%')
        p1 = cursor.fetchone()
        name = [p1[0].strip()]
        if p1[3][-1] == 'g':
            image = ["./static/Player_Photo/atp_default.svg"]
        else:
            image = ["./static/Player_Photo/" + str(p1[1]) + ".webp"]
        country = [p1[2]]
        cursor.execute("select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country),img from Player where Name Like %s ", '%' + PlayerName[1] + '%')
        p2 = cursor.fetchone()
        name.append(p2[0].strip())
        if p2[3][-1]=='g':
            image.append("./static/Player_Photo/atp_default.svg")
        else:
            image.append("./static/Player_Photo/"+str(p2[1])+".webp")
        country.append(p2[2])
        cursor.execute("select Name from Player where img is not NULL order by Last_Appearance desc")
        playerlist = cursor.fetchall()
        playerlist = [x[0].strip() for x in playerlist]
        connect.close()

        return render_template('h2h.html', data=table, name=name, img=image, playerlist=playerlist, country=country)

    else:

        data = request.form.to_dict()
        court = data['court_type']
        level = data['Level_type']
        PlayerName = [data['player1'],data['player2']]

        connect = pymssql.connect(server='localhost', user='sa', password='123456', database='atp-tennis',
                                  charset='utf8')
        cursor = connect.cursor()

        cursor.execute("EXEC headtohead %s,%s", (PlayerName[0], PlayerName[1]))
        table = cursor.fetchall()
        if court != 'All':
            table = [x for x in table if x[2].strip()==court]
        if level != 'All':
            if level == 'Grand Slam':
                table = [x for x in table if (x[0]=='Australian Open' or x[0]=='Roland Garros' or x[0]=='Wimbledon' or x[0]=='US Open' or x[0]=='French Open')]
            elif level == 'Only Main Draw':
                table = [x for x in table if x[3][1]!='Q']
            elif level == 'Only Final':
                table = [x for x in table if x[3] == 'F']

        cursor.execute("select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country),img from Player where Name Like %s ", '%' + PlayerName[0] + '%')
        p1 = cursor.fetchone()
        name = [p1[0].strip()]
        if p1[3][-1] == 'g':
            image = ["./static/Player_Photo/atp_default.svg"]
        else:
            image = ["./static/Player_Photo/" + str(p1[1]) + ".webp"]
        country = [p1[2]]

        cursor.execute(
            "select top 1 Name,ID,(select top 1 country_code from Country where Country = Player.country),img from Player where Name Like %s ",
            '%' + PlayerName[1] + '%')
        p2 = cursor.fetchone()
        name.append(p2[0].strip())
        if p2[3][-1] == 'g':
            image.append("./static/Player_Photo/atp_default.svg")
        else:
            image.append("./static/Player_Photo/" + str(p2[1]) + ".webp")
        country.append(p2[2])

        cursor.execute("select Name from Player where img is not NULL order by Last_Appearance desc")
        playerlist = cursor.fetchall()
        playerlist = [x[0].strip() for x in playerlist]
        connect.close()
        return render_template('h2h.html', data=table, name=name, img=image, playerlist = playerlist, country = country)


if __name__ == '__main__':
    app.run(debug=True)
