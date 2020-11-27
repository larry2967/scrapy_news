import scrapy
import traceback, sys
from dateutil.parser import parse as date_parser
from scraper.items import NewsItem
from .redis_spiders import RedisSpider
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re

class CnaSpider(scrapy.Spider):
    name = "cna"
    def start_requests(self):
        if isinstance(self, RedisSpider):
            return
        requests = [{
            "media": "cna",
            "name": "cna",
            "enabled": True,
            "days_limit": 3600 * 24 * 2,
            "interval": 3600 * 2,
            "url": "https://www.cna.com.tw/list/asoc.aspx",
            "url_pattern":"https://www.cna.com.tw/cna2018api/api/WNewsList",
            "headers":{
                'authority': 'www.cna.com.tw',
                'sec-ch-ua': '"Chromium";v="86", ""Not\\A;Brand";v="99", "Google Chrome";v="86"',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'x-requested-with': 'XMLHttpRequest',
                'sec-ch-ua-mobile': '?0',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
                'content-type': 'application/json',
                'origin': 'https://www.cna.com.tw',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': 'https://www.cna.com.tw/list/asoc.aspx',
                'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'cookie': 'ASP.NET_SessionId=hhql1tqyberadyrrhgzggyuq; __auc=bb901549175f3d8f68ce4014d78; _ga=GA1.3.1566804492.1606113884; _gid=GA1.3.1749205380.1606113884; CnaCloseLanguage=1; __asc=90bf7ff8175f42c505ffc56cd9b; _gat_UA-6826760-1=1'
            },
            'page': '1',
            'page_idx':'0'
        }]
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)
 
    def parse(self, response):
        meta = response.meta
        print('-----parse-------')
        
        now = datetime.now()

        past = now - timedelta(seconds=meta['days_limit'])
        while True:
            payload = {'action':'0','category':'asoc','pagesize':'20','pageidx':'1'}
            yield scrapy.FormRequest(
                    url = meta["url_pattern"],
                    headers=meta['headers'],
                    method='POST',
                    body = json.dumps(payload),
                    meta=meta,
                    dont_filter=True,
                    callback=self.parse_list)
            now = now - timedelta(seconds=3600 * 24)
            if now <= past:
                break

    def parse_list(self, response):
        meta = response.meta
        data = json.loads(response.body)
        print(data['Result'])
        #find the lastest_time in parse_list
        print(type(data))
        _iteration = data
        print(_iteration['ResultData']['Items'][1]['CreateTime'])
        latest_datetime = max(_iteration['ResultData']['Items'][i]['CreateTime'] for i in range(len(_iteration['ResultData']['Items'])))
        print(latest_datetime)
        #change to datetime format
        latest_datetime = datetime.strptime(latest_datetime,'%Y/%m/%d %H:%M')
        if len(_iteration) == 0:
                raise scrapy.exceptions.CloseSpider('Response is Empty')
            
        category_name = _iteration['ResultData']['CategoryName']
        print(category_name)
        meta.update({'category_name':category_name})
        for i in range(len(_iteration['ResultData']['Items'])):
                url = _iteration['ResultData']['Items'][i]['PageUrl']
                idx = str(i)
                meta.update({'page_idx':idx})
                yield scrapy.Request(url, 
                        callback=self.parse_article, 
                        meta=meta)



        past = datetime.now() - timedelta(seconds=meta['days_limit'])
        
        if latest_datetime < past:
            return
        page = int(meta['page'])
        page = page + 1
        meta.update({'page': str(page)})
        payload=response.body
        print(payload)
        #next_page = re.search("\"pageidx\":\d+", payload).group(0)[10:12]
        #payload = re.sub("\"pageidx\":\d+","\"pageidx\":{}".format(int(next_page)+1),payload)
        payload = {'action':'0','category':'asoc','pagesize':'20','pageidx':page}
        yield scrapy.FormRequest(
                    url = meta["url_pattern"],
                    body = json.dumps(payload),
                    method='POST',
                    headers=meta['headers'],
                    meta=meta,
                    dont_filter=True,
                    callback=self.parse_list)
    
    

    def parse_article(self, response):
        meta = response.meta
        idx = meta['page_idx']
        category = meta['category_name']
        soup = BeautifulSoup(response.body, 'html.parser')
        item = NewsItem()
        item['url'] = response.url
        item['author'] = self.parse_author(soup)
        item['article_title'] = self.parse_title(soup)
        item['author_url'] = []
        item['content'] = self.parse_content(soup)
        item['comment'] = []
        item['date'] = self.parse_datetime(soup)
        item['metadata'] = self.parse_metadata(soup,idx,category)
        item['content_type'] = 0
        item['media'] = 'cna'
        item['proto'] = 'CNA_PARSE_ITEM'
        return item

    def parse_datetime(self,soup):
        datetime = soup.find('div',{'class':'updatetime'}).find('span').text
        return datetime
    
    def parse_title(self,soup):
        title = soup.find_all('h1')[0].text
        title = ' '.join(title.split())
        return title
    
    def parse_author(self,soup): 
        try:
            # try Columnist
            author = soup.find_all('p')[0].text
            author  = author[6:9]
            return author
        
        except:
            print('no author ')
        
    def parse_content(self,soup):
        content = soup.find('div',{'class':'paragraph'}).text
        return content
    
    def parse_metadata(self,soup,idx,category):
        idx = int(idx)
        metadata = {'category':'', 'fb_like_count': '','image_url':[]}
        image_url = soup.find_all('div',{'class':'wrap'})
        image_url = image_url[idx].find('img')['data-src']
        metadata['image_url'] = image_url
        metadata['category_name'] = category
        return metadata
