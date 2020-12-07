# -*- coding: utf-8 -*-
import scrapy
from bs4 import BeautifulSoup
import traceback, sys
from datetime import datetime, timedelta
import re
from dateutil.parser import parse as date_parser
from scraper.items import NewsItem
import json
from .redis_spiders import RedisSpider
import datetime

# from scrapy_redis.spiders import RedisSpider

# class LtnSpider(RedisSpider):
class MirrormediaSpider(scrapy.Spider):
    name = "mirrormedia"
    

    def start_requests(self):
            
        if isinstance(self, RedisSpider):
            return
        
        search_day=[]
        now=datetime.datetime.now()
        today=now.strftime("%Y%m%d")
        search_day.append(today)
        day_before=2
        
        for i in range(1,day_before+1):
            time_delta=datetime.timedelta(days=i) 
            day_before=(now-time_delta).strftime("%Y%m%d")
            search_day.append(day_before)
            
        # url
        
        requests=[{
            "url": 'https://www.myip.com/',
            "url_pattern":"https://www.mirrormedia.mg/story/{}soc{}/",
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
            "media": "mirrormedia",
            "name": "mirrormedia_keywords",
            "scrapy_key": "mirrormedia:start_urls",
            "day":search_day,
            "priority": 1,
            "search": False,
            "enabled": True,
        }]
        
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)
                
    def parse(self, response):
        
        meta = response.meta 
        url_pattern=meta['url_pattern']
        for day in meta['day']:
            meta['url_pattern']=url_pattern
            url=url_pattern.format(day,'001')
            meta['url_pattern']=url
            yield scrapy.Request(url,
                    meta=meta,
                    dont_filter=True,
                    callback=self.recursive_parse)
            
    def recursive_parse(self,response): 
        # 回傳404停止尋找
        if(response.status==404):
            return
        elif(response.status==200):
            # 繼續parse回傳200的url
            meta = response.meta
            url=meta['url_pattern']
            yield scrapy.Request(url,
                    meta=meta,
                    dont_filter=True,
                    callback=self.parse_article)
            
            # 回傳200繼續往下找
            num=url[-4:-1]
            print(num)
            story_num=int(num)
            # 填成3位數：如'1'->'001'
            story_num=str(story_num+1).zfill(3)
            # 下一篇文章的url
            next_url=meta['url_pattern'][:-4]+story_num+'/'
            meta['url_pattern']=next_url
            yield scrapy.Request(next_url,
                    meta=meta,
                    dont_filter=True,
                    callback=self.recursive_parse)
            
    def parse_article(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
          
        metadata = {'category':'','image_url':[]}
        
        content, author, author_url,metadata['image_url'] = self.parse_content_author_image(soup)
        
        title=soup.find('title').get_text()
        
        metadata['category']=soup.find('meta',{'property':'article:section2'})['content']
        
        item = NewsItem()
        item['url'] = response.url
        item['article_title'] = title
        item['author'] = author
        item['author_url'] = [author_url]
        item['comment'] = []
        item['date'] = self.parse_datetime(soup)
        item['content'] = content
        item['metadata'] = metadata
        item['content_type'] = 0
        item['media'] = 'mirrormedia'
        item['proto'] = 'MIRRORMEDIA_PARSE_ITEM'
        
        return item


    def parse_datetime(self,soup):
        date = soup.find('meta', {'property':'article:published_time'})
        if date:
            return date['content'].replace('Z', '+0800')
        
        date = soup.find('span', {'class':'time'})
        if date:
            return date_parser(date.text).strftime('%Y-%m-%dT%H:%M:%S+0800')

        date = soup.find('div', {'class':'article_header'})
        if date:
            return datetime.datetime.strptime(date.find_all('span')[1].text, '%Y-%m-%d').strftime('%Y-%m-%dT%H:%M:%S+0800')
        
        date = soup.find('div', {'class':'writer'})
        if date:
            return datetime.datetime.strptime(date.find_all('span')[1].text, '%Y-%m-%d %H:%M').strftime('%Y-%m-%dT%H:%M:%S+0800')

    def parse_title_metadata(self,soup):        
        title = soup.find('title').text.replace(' - 自由時報電子報', '').replace(' 自由電子報', '')
        title_ = title.split('-')
        if not title_[-1]:
            del title_[-1]
        if len(title_) > 2:
            category = title_[-1]
            del title_[-1]
            ti = ''.join(x for x in title_)
            return ti.strip(), category.strip()
        elif len(title_) == 2:
            category = title_[1]
            ti = title_[0]
            return ti.strip(), category.strip()
        elif '3C科技' in title_[0]:
            category = '3C科技'
            ti = title_[0].replace('3C科技', '')
            return ti.strip(), category
        elif '玩咖Playing' in title_[0]:                
            category = '玩咖Playing'
            ti = title_[0].replace('玩咖Playing', '')            
            return ti.strip(), category
        else:
            category = ''
            ti = title_[0]
            return ti.strip(), category
            
    
    def parse_content_author_image(self,soup): 
        
        # content
        content=''
        for text in soup.findAll('p')[2:-3]:
            content=content+text.get_text()
            
        # author
        # au = soup.find(property='dable:author')['content']
        au=json.loads(soup.findAll('script', {'type': 'application/ld+json'})[1].get_text())['name']
        au_url=json.loads(soup.findAll('script', {'type': 'application/ld+json'})[1].get_text())['url']
        
        # image
        image_url = []
        image_url.append(json.loads(soup.find('script', {'type': 'application/ld+json'}).get_text())['image'])

        return content, au, au_url, image_url
