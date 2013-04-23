#!/usr/bin/env python
# coding: utf-8
#
#
#
from flask import Flask, redirect, render_template
from werkzeug.contrib.fixers import  ProxyFix
import redis
import json
import datetime

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

@app.route("/")
def start():
    return render_template('page2.html',active_menu=1)

@app.route("/test")
def test():
    return "Hello world!"

@app.route("/log")
def test():
    return render_template('update.log')

@app.route("/login")
def login():
    return render_template('login.html',active_menu=6)

@app.route("/gold")
def get_gold():
    date =  datetime.datetime.fromtimestamp(float(read_prices_db(0)[-1][0])/1000,).strftime(u'%d.%m.%Y  %H:%M')
    buy_price =read_prices_db(0)[-1][1]
    sell_price = read_prices_db(1)[-1][1]
    #plotlines = r'''plotLines: [{ color: 'green', width: 2, value: 1600, dashStyle : 'shortdash', label: { text: 'label1'}}, { color: 'yellow', width: 2, value: 1400, dashStyle : 'shortdash', label: { text: 'label2'}} ]'''
    plotlines = ""
    return render_template('metal.html', today=date, data_id=0, data_id1=1, metal_name=u'Золото',buy_price=buy_price, sell_price=sell_price, active_menu=2, plotlines=plotlines)

@app.route("/silver")
def get_silver():
    date =  datetime.datetime.fromtimestamp(float(read_prices_db(0)[-1][0])/1000,).strftime('%d.%m.%Y  %H:%M')
    buy_price =read_prices_db(2)[-1][1]
    sell_price = read_prices_db(3)[-1][1]
    return render_template('metal.html', today=date, data_id=2, data_id1=3, metal_name=u'Серебро',buy_price=buy_price, sell_price=sell_price, active_menu=3)

@app.route("/platinum")
def get_platinum():
    date =  datetime.datetime.fromtimestamp(float(read_prices_db(0)[-1][0])/1000,).strftime('%d.%m.%Y  %H:%M')
    buy_price =read_prices_db(4)[-1][1]
    sell_price = read_prices_db(5)[-1][1]
    return render_template('metal.html', today=date, data_id=4, data_id1=5, metal_name=u'Платина',buy_price=buy_price, sell_price=sell_price, active_menu=4)

@app.route("/palladium")
def get_palladium():
    date =  datetime.datetime.fromtimestamp(float(read_prices_db(0)[-1][0])/1000,).strftime('%d.%m.%Y  %H:%M')
    buy_price =read_prices_db(6)[-1][1]
    sell_price = read_prices_db(7)[-1][1]
    return render_template('metal.html', today=date, data_id=6, data_id1=7, metal_name=u'Палладий',buy_price=buy_price, sell_price=sell_price, active_menu=5)


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
        res.append([int(day)*1000,float(prices_list[i].replace(' ', '').replace(',', '.'))])
    return res

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == "__main__":
    app.run(host='0.0.0.0')