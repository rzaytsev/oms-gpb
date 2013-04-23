import redis
import re
import sys

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
            res.append([int(day)*1000,'error: ' + prices_list[i]])
    return res


if __name__ == "__main__":
    print read_prices_db(int(sys.argv[1]))