import redis
import re
import sys


def user():
    from passlib.hash import sha256_crypt
    hash = sha256_crypt.encrypt("somepass")
    print hash
    if sha256_crypt.encrypt.verify("somepass", hash):
        print 'ok'

if __name__ == "__main__":
    #print read_prices_db(int(sys.argv[1]))
    user()


