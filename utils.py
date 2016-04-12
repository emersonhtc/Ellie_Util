import requests
import BeautifulSoup
import datetime
import urllib2
import json
import time

def get_N_60K_price(contract='MTX', N=1):
    url = 'http://histock.tw/stock/module/stockdata.aspx?m=minks&time=60&no=FI' + contract
    response = urllib2.urlopen(url)
    ret = response.read()
    ret_json = json.loads(json.loads(ret)['DayK'])
    for i in ret_json:
        i[0] = time.strftime("%D %H:%M", time.localtime(int(i[0]/1000) - 8*60*60))

    return ret_json[-int(N):]


def get_N_day_price(contract='MTX', N=1):
    # TODO replace original one with histock

if __name__ == '__main__':
    print get_N_60K_price(N=5)
    print get_N_day_price(N=5)
    # print get_Nday_price()
    # print get_Nday_price('TX')
    # print get_Nday_price('MTX', 5)
