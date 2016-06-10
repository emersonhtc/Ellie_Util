import sys
import requests
import BeautifulSoup
import datetime
import urllib
import urllib2
import json
import time
import pandas as pd

# return value: [date, open, high, low, close]
def query_future_price(year, month, day, window, contract):
	url = 'http://www.taifex.com.tw/chinese/3/3_1_1.asp'
	result_PB = []

	retry = 0
	q_date = datetime.date(year,month,day)

	while len(result_PB) < window:
		delta = datetime.timedelta(days=1)
		year_string = '{0:04d}'.format(q_date.year)
		month_string = '{0:02d}'.format(q_date.month)
		day_string = '{0:02d}'.format(q_date.day)

		values = {'DATA_DATE_Y' : year_string, 'DATA_DATE_M' : month_string, 'DATA_DATE_D' : day_string,
				  'syear' : year_string, 'smonth' : month_string, 'sday' : day_string,
				  'commodity_id' : contract.upper()}
		data = urllib.urlencode(values)
		req = urllib2.Request(url, data)
		try:
			response = urllib2.urlopen(req)
		except:
			print "url open err, wait"
			time.sleep(1)
			continue

		try:
			html = response.read()
		except:
			print "url read err, wait"
			time.sleep(1)
			continue

		soup = BeautifulSoup.BeautifulSoup(html)

		table = soup.find('table', {'class':'table_f'})
		if table:			
			for tr in table.findAll('tr'):
				tmp = [x.text for x in tr.findAll('td')]				
				if len(tmp)==0:
					continue
				if tmp[1].find('W') >=0:
					continue
				result_PB.append([q_date, tmp[2], tmp[3], tmp[4], tmp[5]])

				break
		q_date -= delta

	return result_PB


def query_future_ma(year, month, day, ma, offset, contract):
	result_list = query_future_price(year, month, day, ma+offset, contract)
	result_list = result_list[offset:]
	#print result_list
	price_sum = 0
	for n in result_list:
		price_sum += int(n[4])
		
	return price_sum/ma
	


def query_future_ma_trend(year, month, day, ma, contract):
	trend_threshold = 10	
	after = query_future_ma(year, month, day, ma, 0, contract)
	
	q_date = datetime.date(year,month,day)
	q_date -= datetime.timedelta(days=1)	

	before = query_future_ma(q_date.year, q_date.month, q_date.day, ma, 1, contract)
	
	if abs(after - before) <= trend_threshold:
		return 'FLAT', after - before
	elif after - before > trend_threshold:
		return 'UP', after - before
	else:
		return 'DOWN', after - before


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
					print result_PB,'\r',

					sys.stdout.flush()
					retry = -1
					break
				if retry==-1: 
					retry=0
					break
				else: retry+=1
				
		if retry > 15:
			return -1

	print '\r',
	return sum(result_PB) / float(len(result_PB))

def transform_time(x):
	tmp=time.localtime(int(x/1000) - 8*60*60)
	return datetime.datetime(*tmp[:6])

def get_histock_json(contract):
	url = 'http://histock.tw/stock/module/stockdata.aspx?m=minks&time=60&no=FI' + contract
	response = urllib2.urlopen(url)
	ret = response.read()
	ret_json = json.loads(json.loads(ret)['DayK'])
	
	df = pd.DataFrame.from_records(ret_json, columns=['time','open','high','low','close'])
	df.time = df.time.apply(transform_time)
	df.set_index(keys='time', inplace=True)
	
	return df

def get_N_60K_MA(contract='MTX',N=1):
	df = get_histock_json(contract)
	return df.close.tail(N).mean()
 
def get_N_day_MA(contract='MTX',N=1):
	df = get_histock_json(contract)
	return df[df.index.map(lambda x: x.time())==datetime.time(12, 45)].close.tail(N).mean()


def get_N_60K_price(contract='MTX', N=1):
	df = get_histock_json(contract)
	return df.close.tail(N).tolist()
	

def get_N_day_price(contract='MTX', N=1):
	df = get_histock_json(contract)
	return df[df.index.map(lambda x: x.time())==datetime.time(12, 45)].close.tail(N).tolist()


def main():
	cur_time = datetime.datetime.now()
	print "Today: ",
	print cur_time.year, cur_time.month, cur_time.day
	print "Trend of 5ma:",
	print query_future_ma_trend(year=cur_time.year, month=cur_time.month,
								day=cur_time.day, ma=5, contract='MTX')
	print "Price of 5ma:",
	print query_future_ma(year=cur_time.year, month=cur_time.month,
						day=cur_time.day, ma=5, offset=1, contract='MTX')
	print "5-day Price:",
	print query_future_price(year=cur_time.year, month=cur_time.month,
						day=cur_time.day, window=5, contract='MTX')
	
	#print query_PB_Ratio_MA(year=2016, month=06, day=01, ID=2330, ma=10)

	#print get_N_60K_price(N=5)
	#print get_N_60K_MA(N=5)

	#print get_N_day_price(N=5)
	#print get_N_day_MA(N=5)




if __name__ == '__main__':
	main()
