
# coding: utf-8

# In[1]:

get_ipython().magic(u'matplotlib inline')

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import urllib
import urllib2
from IPython.core.display import display, HTML
import requests
import BeautifulSoup


import numpy as np

import itertools
import datetime
import time


# In[2]:

def query_month_price(year, month, ID):
    url = 'http://www.twse.com.tw/ch/trading/exchange/STOCK_DAY_AVG/STOCK_DAY_AVGMAIN.php'
    values = {'query_year' : str(year), 'query_month' : str(month), 'CO_ID' : str(ID)}
    data = urllib.urlencode(values)

    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    html = response.read()
    soup = BeautifulSoup.BeautifulSoup(html)

    tmp_df = pd.DataFrame(columns=['date', 'price'])
    for table in soup.findAll('tbody'):
        for tr in table.findAll('tr'):
            tmp_df.loc[len(tmp_df)] = [x.text for x in tr.findAll('td')]
        tmp_df = tmp_df.drop(tmp_df.index[-1])

    return tmp_df


# In[22]:

def query_PB_Ratio_MA(year, month, day, ID, ma):        
    
    url = 'http://www.twse.com.tw/ch/trading/exchange/BWIBBU/BWIBBU_d.php'
    result_PB = []
    
    retry = 0
    q_date = datetime.date(year,month,day)
    while len(result_PB) < ma:
        delta = datetime.timedelta(days=1)
        q_date -= delta
        if q_date.year-1911 > 99:
            date_string = '{0:03d}/{1:02d}/{2:02d}'.format(q_date.year-1911,q_date.month,q_date.day)
        else:
            date_string = '{0:02d}/{1:02d}/{2:02d}'.format(q_date.year-1911,q_date.month,q_date.day)
            
        #print date_string,
        
        values = {'input_date' : date_string, 'select2' : 'ALL', 'order' : 'STKNO'}
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        try:
            response = urllib2.urlopen(req)
        except:
            print "url open err, wait"            
            time.sleep(3)
            continue
        
        try:
            html = response.read()
        except:
            print "url read err, wait"
            time.sleep(3)
            continue
            
        soup = BeautifulSoup.BeautifulSoup(html)

        
        for table in soup.findAll('tbody'):
            for tr in table.findAll('tr'):
                tmp = [x.text for x in tr.findAll('td')]
                if tmp[0] == str(ID):
                    result_PB.append(float(tmp[4]))
                    #print result_PB
                    retry = -1
                    break
                if retry==-1: 
                    retry=0
                    break
                else: retry+=1
                
        if retry > 15:
            return -1
        

    
    
    return sum(result_PB) / float(len(result_PB))
    
    


# In[21]:

#6257 2015 12 24
#1558 2009 5 6
query_PB_Ratio_MA(year=2011,month=8,day=24,ID=3454, ma=30)


# In[23]:

input_df = pd.read_csv('C:\Users\Emerson\Downloads\chad1.csv', encoding = 'utf-8', names = ['ID','Name','date'], header = 0)

input_df['year'] = input_df.date.apply(str).str[0:4].astype(int)
input_df['month'] = input_df.date.apply(str).str[4:6].astype(int)
input_df['day'] = input_df.date.apply(str).str[6:8].astype(int)

input_df['PB_Ratio_30_MA'] = np.NaN


for row in input_df.itertuples():
    year, month, day = row.year, row.month, row.day
    ID = row.ID
    
    print ID, year, month, day,
    
    query_date = datetime.date(year,month,day) 
    
    result = query_PB_Ratio_MA(year=year,month=month,day=day,ID=ID, ma=30)
    input_df.at[row.Index, 'PB_Ratio_30_MA'] = result
    print result
        


# In[ ]:

def query_ma_price(year, month, day, ID, window):
    q_date = datetime.date(year,month,day)    
    delta = datetime.timedelta(weeks=8)  #enough weeks for finding 30 days

    date_candidate = set()
    for single_date in pd.date_range(q_date - delta, q_date):
        date_candidate.add((single_date.year, single_date.month))

    tmp_df = pd.DataFrame(columns=['date', 'price'])
    for date_index in list(date_candidate):
        year_i, month_i = date_index[0], date_index[1]
        tmp_df = pd.concat([tmp_df, query_month_price(year_i, month_i, ID)])

    tmp_df = tmp_df.set_index('date').sort_index()
    tmp_df['ma']=tmp_df.price.rolling(30).mean()
    
    
    q_string = '{0:03d}/{1:02d}/{2:02d}'.format(year-1911,month,day)

    return tmp_df[tmp_df.index >= q_string].ma.values[0]


# In[ ]:

def date_to_last_quarter(query_date):    
    delta = datetime.timedelta(days=123)
    query_date = query_date - delta
    return query_date.month/3+1


# In[ ]:

def BVS(stock_no, year, season , item):
    year -= 1911
    url = 'http://mops.twse.com.tw/mops/web/t163sb05'
    values = {'step' : '1', 'firstin' : 'true', 'off' : '1', 'typeK' : 'otc', 'year' : str(year), 'season' : str(season)}
    data = urllib.urlencode(values)

    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    html = response.read()
    soup = BeautifulSoup.BeautifulSoup(html)
    
    result_df = []
    for tr in soup.findAll("tr"):
        if len(tr.attrs) > 0:
            if 'tblHead' in tr.attrs[0]:
                result_df.append(pd.DataFrame())
                for th in tr.findAll("th"):
                    (result_df[-1])[th.text] = np.NaN

            if 'even' in tr.attrs[0] or 'odd' in tr.attrs[0]:
                tmp = []
                for td in tr.findAll("td"):
                    tmp.append(td.text)
                result_df[-1].loc[len(result_df[-1])]=tmp
    if sum([len(x) for x in result_df]) == 0:
        print "no result"
        return np.NaN
        
    final_df = pd.concat([x for x in result_df], ignore_index=True)
    final_df = final_df.set_index([u'公司代號', u'公司名稱'])

    if str(stock_no) not in final_df.index:
        print "stock_no not exist"
        return np.NaN

    return float(final_df.loc[str(stock_no)][item][0])
    


# In[ ]:




# In[ ]:

BVS(stock_no=2311, year=105, season=2, item=u'每股參考淨值')


# In[ ]:

for year, season in list(itertools.product([2014], [1,2,3,4])):
    print year, season, BVS(stock_no=2311, year=year, season=season, item=u'每股參考淨值')


# In[ ]:

query_ma_price(2015,3,2,2311,30)


# In[ ]:

#日期
year, month, day = 2010, 12, 24
#股票代號
ID = 2103

query_date = datetime.date(year,month,day) 
print BVS(stock_no=ID, year=query_date.year, season=date_to_last_quarter(query_date), item=u'每股參考淨值')
print query_ma_price(year=query_date.year, month=query_date.month, day=query_date.day, ID=ID, window=30)


# In[ ]:

input_df


# In[ ]:



