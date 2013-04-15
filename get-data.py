#!/usr/bin/env python
# coding: utf-8


from urllib2 import Request, urlopen
import re
from pyPdf import PdfFileReader
from StringIO import StringIO
import datetime
import redis

def wget(url):
    ufile = urlopen(url)  ## get file-like object for url
    info = ufile.info()   ## meta-info about the url content
    if info.gettype() == 'text/html':
        text = ufile.readlines()  ## read all its text
    return text

def get_current_links():
    lines = wget("http://www.gazprombank.ru/personal/tariffs/?s_code=382#d_382")
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

def read_pdf(url):
    remoteFile = urlopen(Request(url)).read()
    memoryFile = StringIO(remoteFile)
    content = ""
    # Load PDF into pyPDF
    pdf = PdfFileReader(memoryFile)
    # Iterate pages
    for i in range(0, pdf.getNumPages()):
        # Extract text from page and add to content
        content += pdf.getPage(i).extractText() + "\n"
    # Collapse whitespace
    content = " ".join(content.replace(u"\xa0", " ").strip().split())
    str = content.encode("ascii", "ignore")
    print 'pdf: ' + content + '\n'
    r = []
    if not r:
        for i in str.split(':')[-4:]:
            r.append(i.lstrip('- ').split(' - '))

    return r

def main():
    r = redis.StrictRedis(host='localhost', port=6379, db=0)

    links = get_current_links()

    for link in links:
        print link[1] + ' ' + link[2]
        date1 = datetime.datetime.strptime(link[1] + ' ' + link[2],'%d.%m.%Y %H:%M')
        ts1 =date1.strftime('%s')
        print 'timestamp:' + ts1
        print 'date+time from timestamp: ' + str(datetime.datetime.fromtimestamp(float(ts1)))
        prices =  read_pdf(link[0])
        if (not prices == [['']]):
            print prices

            s =''
            for metal in prices:
                s += metal[0].strip() + ' - ' +  metal[1].strip()
                s += ' - '
            s = s[0:len(s)-2]


            print'\n\n'
            if r.sadd('days', ts1):
                print "add new day"
                r.set('prices:'+ts1, s)
            else:
                print "day alredy exists"
            r.setnx('day:'+ts1, s)
        else:
            print "\n\n !!! cannot read pdf file !!! \n\n"



if __name__ == '__main__':
    main()


