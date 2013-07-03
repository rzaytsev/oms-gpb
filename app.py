#!/usr/bin/env python
# coding: utf-8
#
#
#
from flask import Flask, redirect, render_template, request, session, escape, url_for, flash
from werkzeug.contrib.fixers import  ProxyFix
import redis
import json
import datetime
import re

app = Flask(__name__)
app.debug = True

@app.route("/all")
def hello():
    date =  datetime.datetime.fromtimestamp(float(read_prices_db(0)[-1][0])/1000,).strftime('%d.%m.%Y %H:%M')
    gold_buy =read_prices_db(0)[-1][1]
    gold_sell = read_prices_db(1)[-1][1]
    silver_buy = read_prices_db(2)[-1][1]
    silver_sell = read_prices_db(3)[-1][1]
    return render_template('page1.html', today=date, gold_buy=gold_buy, gold_sell=gold_sell, silver_buy=silver_buy, silver_sell=silver_sell)

def get_login_name():
    login_button_caption = u'Вход'
    if 'username' in session:
         login_button_caption = escape(session['username'])
    return login_button_caption

@app.route("/")
def start():
    return render_template('page2.html', login_button_caption=get_login_name(), active_menu=1)

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = u'''Ввведите логин и пароль или <a href='/register'>зарегистрируйтесь</a>'''
    if request.method == 'POST':
        if valid_login(request.form['username'],
                       request.form['password']):
            session['username'] = request.form['username']
            return redirect(url_for('start'))
        else:
            error = u'''Неправильный логин/пароль. <a href="/register">Зарегистрироваться</a>'''

    if 'username' in session:
        error = ""
        user_form = u"Личный кабинет  " + session['username'] + '<br>' + u'''<a href='/logout'>Выйти</a><br><br>'''
        user_form += get_user_items(session['username'])


        return render_template('login.html', error=error, login_form = user_form, active_menu=6,login_button_caption=get_login_name())
    else:

        return render_template('login.html', error=error, login_form = login_form, active_menu=6,login_button_caption=get_login_name())

def get_user_items(user):
    res = u'''<br>Покупки:<br><a href="/add-item">Добавить информацию о покупке</a><br><hr>'''
    res1 = ''
    id = 0
    metals = [u'Золото', u'Серебро', u'Платина', u'Палладий']
    r = redis.StrictRedis(host="localhost",port=6379,db=0)
    items = r.lrange('user:'+user+':items',0,-1)
    if items > 0:
        for item in items:
            i = item.split(',')
            res1 += str(id+1) +'<br><br>'
            res1 += u'Цена: ' + i[2] + u' руб. <br>Метал: ' + metals[int(i[0])-1] + u'<br>Количество: '+ i[1] + u" грамм<br><br><a href='/del-item/" + str(id) + u"'>удалить</a><br><hr>"
            id += 1
    if res1 != '':
        return res + res1
    else:
        return res

def draw_lines(user,metal):
    res = ''
    r = redis.StrictRedis(host="localhost",port=6379,db=0)
    items = r.lrange('user:'+user+':items',0,-1)
    if  items:
        for item in items:
            i = item.split(',')
            if metal == int(i[0]):
                res += u"{ color: 'blue', width: 2, value: %s , dashStyle : 'shortdash' , label: { text: '%s - %s грамм'}}," % (i[2], i[2], i[1])
        return res[0:-1]
    else:
        return '{ }'

def get_today_sell_data(user, metal,today_sell_price):
    total = 0.0
    res = ' '
    r = redis.StrictRedis(host="localhost",port=6379,db=0)
    items = r.lrange('user:'+user+':items',0,-1)
    if items:
        for item in items:
            i = item.split(',')
            if metal == int(i[0]):
                res += u"&nbsp;&nbsp;&nbsp;%s грамм будет стоить:  " % (i[1]) + str (float(i[1]) * today_sell_price)+ u' руб. ' + u'(Цена покупки: ' + str(float(i[2]))+ u" руб.)"
                text = u'Убыток'
                income = (float(i[1]) * today_sell_price - float(i[1]) * float(i[2]) )
                if income >= 0:
                    text = u'Прибыль'
                res += u"<br>&nbsp;&nbsp;&nbsp;" + text + ": " + str(income).replace('-', '') + u' руб. '
                res += '<br><br>'
                total += income
    if res != ' ':
        total_text = u"Общий убыток: "
        if total >= 0:
            total_text = u"Общий доход: "
        return u'Если продать сегодня:<br> ' + res + "<hr>" +total_text + str(total) + u"руб."
    else:
        return ' '


@app.route('/add-item', methods=['POST', 'GET'])
def add_item():
    if request.method == 'GET':
        return render_template('login.html', error=u"", login_form = add_form, active_menu=6,login_button_caption=get_login_name())
    else:
        add_new_item(request.form['metal'],request.form['volume'],request.form['price'])
        return render_template('login.html', error=u"Информация добавлена", login_form = '', active_menu=6, login_button_caption=get_login_name())



def add_new_item(metal,volume,price):
    '''
    Format
    list
        key - user:<name>:items
        value  - metal,value,price
    '''
    r = redis.StrictRedis(host="localhost",port=6379,db=0)
    user = session['username']
    price = price.replace(',', '.')
    r.rpush('user:'+user+':items', metal + ',' + volume + ',' + price)
    return True

@app.route('/del-item/<int:item_id>')
def del_item(item_id):
    # добавить проверку есть ли сессия
    r = redis.StrictRedis(host="localhost",port=6379,db=0)
    r.lrem('user:'+session['username']+':items', 1, r.lindex('user:'+session['username']+':items', item_id))
    return redirect(url_for('login'))




@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('start'))

@app.route('/reg', methods=['POST'])
def reg_user():
    from passlib.hash import sha256_crypt
    if request.method == 'POST':
        r = redis.StrictRedis(host="localhost",port=6379,db=0)
        user = request.form['username']
        hash = sha256_crypt.encrypt(request.form['password'])
        exists_user = r.get('user:'+user+':password')
        if not exists_user:
            session['username'] = user
            r.set('user:'+user+':password', hash)
            return redirect(url_for('start'))
            # Flash!
            # Send email
            send_email(user)
        else:
            return render_template('login.html', error=u"Пользователь с таким именем уже существует! Введите другое имя.", login_form = regisrer_form, active_menu=6,login_button_caption=get_login_name())

    else:
        error = u'''Ошибка'''
        return render_template('login.html', error=error, login_form = regisrer_form, active_menu=6,login_button_caption=get_login_name())

@app.route('/register')
def register():
    error = u"Регистрация.<br>Ведите ваш email в кечестве логина и пароль."

    return render_template('login.html', error=error, login_form = regisrer_form, active_menu=6,login_button_caption=get_login_name())

def valid_login(user, password):
    from passlib.hash import sha256_crypt
    r = redis.StrictRedis(host="localhost",port=6379,db=0)
    exists_user_hash = r.get('user:'+user+':password')
    if exists_user_hash:
        valid_password = sha256_crypt.verify(password, exists_user_hash)
        if valid_password:
            return True
        else:
            return False
    else:
        return False

def log_the_user_in(user):
    return 'Welcome, user!'

#def login():
#    return render_template('login.html',active_menu=6)

def get_metal(metal):
    metals = [u'Золото', u'Серебро', u'Платина', u'Палладий']
    date =  datetime.datetime.fromtimestamp(float(read_prices_db(metal)[-1][0])/1000,).strftime(u'%d.%m.%Y  %H:%M')
    buy_price =read_prices_db(metal*2)[-1][1]
    sell_price = read_prices_db(metal*2+1)[-1][1]
    plotlines = ""
    sell_today = ""
    if 'username' in session:
        plotlines = draw_lines(session['username'], metal+1)
        sell_today = get_today_sell_data(session['username'], metal+1, buy_price)
    return render_template('metal.html', login_button_caption=get_login_name(), \
        today=date, data_id=metal*2, data_id1=metal*2+1, metal_name=metals[metal], \
        buy_price=buy_price, sell_price=sell_price, active_menu=metal+2, plotlines = plotlines, sell_today = sell_today)

@app.route("/gold")
def get_gold():
    return get_metal(0)

@app.route("/silver")
def get_silver():
    return get_metal(1)

@app.route("/platinum")
def get_platinum():
    return get_metal(2)

@app.route("/palladium")
def get_palladium():
    return get_metal(3)

@app.route('/read-data/<int:id>')
def read_data(id):
    if id >=0 and id <=7:
        return json.dumps(read_prices_db(id))

def read_prices_db(i):
    r = redis.StrictRedis(host="localhost",port=6379,db=0)
    days = r.smembers('days')
    ts =[]
    res =[]
    for day in sorted(days):
        ts.append(day)
        prices_list = r.get('prices:'+day).split(' - ')
        m = re.search(r'\d+,\d+', prices_list[i].replace(' ', ''))
        if m:
            res.append([int(day)*1000,float(m.group().replace(',', '.'))])
        else:
            res.append([int(day)*1000,float(0)])
    return res

def send_email(mail_to):
    # Import smtplib for the actual sending function
    import smtplib

    me = 'no-replay@sshok.com'
    msg['Subject'] = 'Вы успешно зарегистрировались!'
    msg['From'] = me
    msg['To'] = mail_to

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(me, mail_to, msg.as_string())
    s.quit()

regisrer_form  = u'''<form action="/reg"  method="post">
    <p><input placeholder="email" type=text name=username>
    <p><input placeholder="password" type=text name=password>
    <p><input type=submit value=Зарегистрироваться>
    </form>
    '''

login_form  = '''<form action=""  method="post">
            <p><input placeholder="email" type=text name=username>
            <p><input placeholder="password" type="password" name=password>
            <p><input type=submit value=Login>
        </form>
        '''

add_form = u'''<form action="/add-item"  method="post">
    <p>
        <select name="metal">
          <option value="1">Золото</option>
          <option value="2">Серебро</option>
          <option value="3">Платина</option>
          <option value="4">Палладий</option>
        </select>

    <p><input type=text name="volume" placeholder="количество, грамм">
    <p><input type=text name="price" placeholder="цена, руб.">
    <p><input type=submit value="Добавить">
    </form>
    '''

app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = 'A0Zr98j/sds43edsX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
    app.run(host='0.0.0.0')
