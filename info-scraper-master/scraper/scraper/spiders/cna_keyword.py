# -*- coding: utf-8 -*-
import scrapy
import traceback, sys
from dateutil.parser import parse as date_parser
from scraper.items import NewsItem
from .redis_spiders import RedisSpider
# from scrapy_redis.spiders import RedisSpider
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re

# class Cna_keywordsSpider(RedisSpider):
class Cna_keywordsSpider(scrapy.Spider):
    name = "cna_keywords"

    def start_requests(self):
        if isinstance(self, RedisSpider):
            return
        requests = [{
            "media": "cna",
            "name": "cna_keywords",
            "scrapy_key": "cna_keywords:start_urls",
            "url":"https://www.cna.com.tw",
            "url_pattern": "https://www.cna.com.tw/search/hysearchws.aspx?q={}",
            "keywords_list":['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅'],
            "priority": 1,
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
        keywords_list = meta['keywords_list']
        for i in range(len(keywords_list)):
            yield scrapy.Request(meta['url_pattern'].format(keywords_list[i]),
                    meta = meta,
                    dont_filter=True,
                    callback = self.parse_list)

    def parse_list(self,response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
        soup = soup.find('ul',{'id':'jsMainList'})
        for s in soup.find_all("li"):
            url = s.find('a').get('href')

            time = s.find('div',{'class':'date'}).text
            time = datetime.strptime(time, '%Y/%m/%d %H:%M')
            past = datetime.now() - timedelta(seconds=meta['days_limit'])
            if (time < past):
                return

            yield scrapy.Request(url,
                    meta=meta,
                    callback=self.parse_article)


    def parse_article(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        item = NewsItem()
        item['url'] = response.url
        item['author'] = self.parse_author(soup)
        item['article_title'] = self.parse_title(soup)
        item['author_url'] = []
        item['comment'] = []
        item['date'] = self.parse_datetime(soup)
        item['metadata'] = self.parse_metadata(soup)
        item['content'] = self.parse_content(soup)
        item['content_type'] = 0
        item['media'] = 'cna'
        item['proto'] = 'CNA_KEYWORDS_PARSE_ITEM'
        return item

    def parse_datetime(self, soup):
        date = soup.find('div',{'class':'updatetime'}).find('span').text
        date = datetime.strptime( date , '%Y/%m/%d %H:%M')
        date = date.strftime('%Y-%m-%dT%H:%M:%S+0800')
        return date
    
    def parse_author(self, soup):
        try:
            # try Columnist
            author = soup.find_all('p')[0].text
            author  = author[6:9]
            return author
        except:
            print('no author')
    
    def parse_title(self, soup):
        title = soup.find_all('h1')[0].text
        title = ' '.join(title.split())
        return title
    
    def parse_content(self, soup):
        content = soup.find('div',{'class':'paragraph'}).text
        return content

    def parse_metadata(self, soup):
        category = soup.find('div',{'class':'breadcrumb'}).find_all('a')[1].text
        image_url = []
        try:
            image_url.append(soup.find('div','floatImg center').find('div','wrap').find('img').get('src')) 
        except:
            pass
        metadata = {'category':category, 'image_url':image_url}
        return metadata
    
