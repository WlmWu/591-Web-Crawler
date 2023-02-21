import re
from bs4 import BeautifulSoup
import requests
import pygsheets
import pandas as pd
import json

def crawler():
    s = requests.Session()
    headers = { 
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15'
    }

    url="https://rent.591.com.tw"
    response = s.get(url,headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")


    token_item = soup.select_one('meta[name="csrf-token"]')
    token=token_item.get('content')

    setCookie=response.headers['Set-Cookie']
    mth=re.search('591_new_session=',setCookie).span()[0]
    cookie=setCookie[mth:len(setCookie)]
    

    # time.sleep(random.uniform(2, 5))
    headers = { 
        'X-CSRF-TOKEN' : token,
        'Cookie' : f'{cookie}; urlJumpIp=4;',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15'
    }
    url='https://rent.591.com.tw/home/search/rsList'
    params='is_format_data=1&is_new_list=1&type=1&region=4&rentprice=,9000&order=posttime&orderType=desc'

    response = s.get(url,params=params,headers=headers)
    data = response.json()
    crawlerRlt=[]
    houses=[]
    soup = BeautifulSoup(response.text, "html.parser")
    if response.status_code==requests.codes.ok:
        crawlerRlt.extend(data['data']['data'])
        for rlt in crawlerRlt:
            tmp={'title':rlt['title'], 'post_id':rlt['post_id'], 'price':rlt['price'], 'location': rlt['location'], 'url':f'https://rent.591.com.tw/rent-detail-{rlt["post_id"]}.html'}
            houses.append(tmp)
    else:
        print(response.status_code)
    
    return(houses)

def gsheet(houses):
    gc = pygsheets.authorize(service_account_file='credentials.json')

    survey_url = 'https://docs.google.com/spreadsheets/d/1Pwr4KZk6ABDUxuPTJStJPbEHTSpyRF_lTmchhpzpf8Q'
    sht = gc.open_by_url(survey_url)
    ws = sht[0]
    df = ws.get_as_df(start='A1', include_tailing_empty=False, numerize=False)
    df = df.replace(',','', regex=True)
    nData=(df.shape)[0]
    houseList=[]
    for i in range(nData):
        houseList.append({'id':df.loc[i]['post_id'],'price':df.loc[i]['price']})
    
    newHouse=[]
    for hs in houses:
        hasFetched=0
        for h in houseList:
            hs['price']=hs['price'].replace(',','')
            if (hs['post_id']==int(h['id']) and int(hs['price'])==int(h['price'])):
                hasFetched=1
                break
        if hasFetched:
            continue
        newHouse.append(hs)
        # print(hs)  
    newHouse.reverse()
    for newh in newHouse:
        houses.insert(0,newh)
        makeNotify(newh)
        
    maxHList=60
    while len(houses)>maxHList:
        houses=houses[:-1]

    for i in range(len(houses)):
        newDF=pd.DataFrame([houses[i]])
        ws.set_dataframe(newDF, f'A{i+2}', nan='', copy_head=False)

def makeNotify(house):
    with open('lineToken.json', 'r') as j:
        token = json.loads(j.read())['token']

    msg='\n'
    houseMsg=f"{house['title']} \n{house['location']} \n$ {house['price']} \n{house['url']}"
    msg+=houseMsg
    headers = {
        "Authorization": "Bearer " + token, 
        "Content-Type" : "application/x-www-form-urlencoded"
    }

    payload = {'message': msg }
    r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
    

if __name__=='__main__':
    houses=crawler()
    gsheet(houses)
    # tmp={'title': '清大交大科學園區', 'post_id': 12731333, 'price': '5,200', 'location': '東區-金山六街', 'url': 'https://rent.591.com.tw/rent-detail-12731333.html'}
        
