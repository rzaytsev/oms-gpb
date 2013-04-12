import redis
import datetime
import json


def main():
    r = redis.StrictRedis(host="localhost",port=6379,db=0)
    days = r.smembers('days')
    ts =[]

    gold_buy = []
    gold_sell = []
    for day in sorted(days):
        #print 'day: '+day
        ts.append(day)
        prices_list = r.get('prices:'+day).split(' - ')
        gold_buy.append(prices_list[2].replace(' ', '').replace(',', '.'))
        gold_sell.append(prices_list[3].replace(' ', '').replace(',', '.'))

    print gold_buy
    print gold_sell


if __name__ == '__main__':
    main()