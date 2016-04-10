import requests
import BeautifulSoup
import datetime

def get_Nday_price(contract='MTX', day=1):
    results=[]
    URL = 'http://www.taifex.com.tw/chinese/3/3_1_1_tbl.asp'
    payload = {
        'commodity_id': contract,
        'commodity_id2': '',
        'qtype': '3',
        'dateaddcnt': '-1',
    }

    contract_oft = 1 if contract == 'TX' else 2
    date_idx = datetime.datetime.now()
    while day>0:
        payload['syear'] = str(date_idx.year)
        payload['smonth'] = str(date_idx.month)
        payload['sday'] = str(date_idx.day)

        session = requests.session()
        r = requests.post(URL, data=payload)
        soup = BeautifulSoup.BeautifulSoup(r.content)
        table = soup.find("table", {"class" : "table_f"})

        if table:
            items = [a.text for a in table.findAll("tr")[contract_oft].findAll('td')]
            results.append(int(items[5]))
            day-=1

        date_idx -= datetime.timedelta(days=1)
    return results[::-1]


if __name__ == '__main__':
    print get_Nday_price()
    print get_Nday_price('TX')
    print get_Nday_price('MTX', 5)
