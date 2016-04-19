import requests
import BeautifulSoup
import datetime
import urllib2
import json
import time
import pandas as pd

def transform_time(x):
    tmp=time.localtime(int(x/1000) - 8*60*60)
    return datetime.datetime(*tmp[:6])

def get_source_json(contract):
    url = 'http://histock.tw/stock/module/stockdata.aspx?m=minks&time=60&no=FI' + contract
    response = urllib2.urlopen(url)
    ret = response.read()
    ret_json = json.loads(json.loads(ret)['DayK'])
	
    df = pd.DataFrame.from_records(ret_json, columns=['time','open','high','low','close'])
    df.time = df.time.apply(transform_time)
    df.set_index(keys='time', inplace=True)
    
    return df

def get_N_60K_price(contract='MTX', N=1):
    df = get_source_json(contract)
    return df.close.tail(N).tolist()
    

def get_N_day_price(contract='MTX', N=1):
    df = get_source_json(contract)
    return df[df.index.map(lambda x: x.time())==datetime.time(12, 45)].close.tail(N).tolist()



if __name__ == '__main__':
    print get_N_60K_price(N=5)
    print get_N_day_price(N=5)
    # print get_Nday_price()
    # print get_Nday_price('TX')
    # print get_Nday_price('MTX', 5)
