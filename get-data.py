#!/usr/bin/env python
# coding: utf-8

import sys
from urllib2 import Request, urlopen
import re
from pyPdf import PdfFileReader
from StringIO import StringIO
import datetime
import redis
import slate

def wget(url):
    ufile = urlopen(url)  ## get file-like object for url
    info = ufile.info()   ## meta-info about the url content
    if info.gettype() == 'text/html':
        text = ufile.readlines()  ## read all its text
    return text

def get_current_links(url):
    lines = wget(url)
    data = []
    for line in lines:
        item = []
        if ".pdf" in line:
            m = re.search(r'(href=")([^\s"]+)()', line)
            if m:
                item.append('http://www.gazprombank.ru/' + m.group(2))
            m = re.search(r'(\d\d.\d\d.\d\d\d\d)\s\S(\d\d:\d\d)', line)
            if m:
                item.append(m.group(1))
                item.append(m.group(2))
            data.append(item)

    return data


def extract_prices_from_pdf(str):
    res = []
    content = " ".join(str.replace(u"\xa0", " ").strip().split())
    prices = re.findall(r'([\d]*\s[\d]+,[\d]+)', content.encode("ascii", "ignore"))
    for price in prices:
        res.append(price.strip())

    return ' - '.join(res)

def read_pdf(url):
    remoteFile = urlopen(Request(url)).read()
    memoryFile = StringIO(remoteFile)
    content = ""
    # Load PDF into pyPDF
    #pdf = PdfFileReader(memoryFile)

    #print memoryFile.getvalue()

    #with open(memoryFile.getvalue()) as f:
    doc = slate.PDF(memoryFile)

    content = doc[0]
    print 'pdf: ' + content + '\n'
    res = []
    prices = re.findall(r'([\d]*\s[\d]+,[\d]+)', content)
    for price in prices:
        res.append(price.strip())

    return ' - '.join(res)


def main():
    args = sys.argv[1:]
    if not args:
        url = "http://www.gazprombank.ru/personal/tariffs/?s_code=382#d_382"
    elif args[0] == "2012":
        url = "http://www.gazprombank.ru/personal/tariffs/index.php?year=2012&s_code=382"
    elif args[0] == "2013":
        url = "http://www.gazprombank.ru/personal/tariffs/index.php?year=2013&s_code=382"
    elif args[0] == "debug":
        url = "http://www.gazprombank.ru/personal/tariffs/index.php?month=09&year=2012&s_code=382"


    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    links = get_current_links(url)

    print "last update: " +  datetime.datetime.now().strftime("%d %m %Y  %H:%M")
    print "get data from: " + url
    print'--------------------------------------------------------'

    for link in links:
        print link
        date1 = datetime.datetime.strptime(link[1] + ' ' + link[2],'%d.%m.%Y %H:%M')
        ts1 =date1.strftime('%s')
        print ts1
        s =  read_pdf(link[0])

        if r.sadd('days', ts1):
            print "add new day"
            print 'add: ' + str(datetime.datetime.fromtimestamp(float(ts1)))
            print 'prices:' + ts1 + " | " +s
            r.set('prices:'+ts1, s)
        else:
            print "alredy exists: " + str(datetime.datetime.fromtimestamp(float(ts1)))

        r.setnx('day:'+ts1, s)
        print'--------------------------------------------------------'





if __name__ == '__main__':
    main()


