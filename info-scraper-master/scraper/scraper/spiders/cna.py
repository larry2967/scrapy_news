import scrapy
import traceback, sys
from dateutil.parser import parse as date_parser
from scraper.items import NewsItem
from .redis_spiders import RedisSpider
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re

# class CnaSpider(RedisSpider):
class CnaSpider(scrapy.Spider):
    name = "cna"
    def start_requests(self):
        if isinstance(self, RedisSpider):
            return
        requests = [{
            "media": "cna",
            "name": "cna",
            "url": "https://www.cna.com.tw/",
            "url_api":"https://www.cna.com.tw/cna2018api/api/WNewsList",
            "headers":{
                'authority': 'www.cna.com.tw',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'x-requested-with': 'XMLHttpRequest',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
                'content-type': 'application/json',
                'origin': 'https://www.cna.com.tw',
                'referer': 'https://www.cna.com.tw/list/asoc.aspx',
                'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            "page":"1",
            "enabled": True,
            "days_limit": 3600 * 24 * 2,
            "interval": 3600 * 2,
        }]
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)
 
    def parse(self, response):
        meta = response.meta
        payload = {'action':'0','category':'asoc','pagesize':'20','pageidx':meta['page']}
        yield scrapy.FormRequest(
                url = meta["url_api"],
                headers=meta['headers'],
                method='POST',
                body = json.dumps(payload),
                meta=meta,
                dont_filter=True,
                callback=self.parse_list)
 

    def parse_list(self, response):
        meta = response.meta
        _iteration = json.loads(response.body)
        
        # checkout _iteration content is not empty
        if len(_iteration) == 0:
            return
            
        category_name = _iteration['ResultData']['CategoryName']
        meta.update({'category_name':category_name})
        for i in range(len(_iteration['ResultData']['Items'])):
            url = _iteration['ResultData']['Items'][i]['PageUrl']
            yield scrapy.Request(url,
                    callback=self.parse_article, 
                    meta=meta)
        
        # checkout latest_datetime
        latest_datetime = max(_iteration['ResultData']['Items'][i]['CreateTime'] for i in range(len(_iteration['ResultData']['Items'])))
        latest_datetime = datetime.strptime(latest_datetime,'%Y/%m/%d %H:%M')
        past = datetime.now() - timedelta(seconds=meta['days_limit'])
        if latest_datetime < past:
            return
        
        # next page
        meta.update({'page': str(int(meta['page']) + 1)})
        payload = {'action':'0','category':'asoc','pagesize':'20','pageidx':meta['page']}
        yield scrapy.FormRequest(
                    url = meta["url_api"],
                    body = json.dumps(payload),
                    method='POST',
                    headers=meta['headers'],
                    meta=meta,
                    dont_filter=True,
                    callback=self.parse_list)
    

    def parse_article(self, response):
        meta = response.meta
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
        item['metadata'] = self.parse_metadata(soup, category)
        item['content_type'] = 0
        item['media'] = 'cna'
        item['proto'] = 'CNA_PARSE_ITEM'
        return item

    def parse_datetime(self,soup):
        date = soup.find('div',{'class':'updatetime'}).find('span').text
        date = datetime.strptime( date , '%Y/%m/%d %H:%M')
        date = date.strftime('%Y-%m-%dT%H:%M:%S+0800')
        return date
    
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
            print('no author')
        
    def parse_content(self,soup):
        content = soup.find('div',{'class':'paragraph'}).text
        return content
    
    def parse_metadata(self, soup, category):
        metadata = {'category':'', 'fb_like_count': '','image_url':[]}
        try:

            metadata['image_url'].append(soup.find('div','floatImg center').find('div','wrap').find('img').get('src')) 
        except:
            pass
        metadata['category'] = category
        return metadata
