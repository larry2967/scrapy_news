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

# class ChinatimesSpider(RedisSpider):
class Chinatimes_keywordsSpider(scrapy.Spider):
    name = "chinatimes_keywords"

    def start_requests(self):
        if isinstance(self, RedisSpider):
            return
        
            
        # url
        requests=[{"media": "chinatimes",
                "name": "chinatimes_keywords",
                "enabled": True,
                "url_pattern":'https://www.chinatimes.com/search/{}?page=1&chdtv',
                "keywords_list":['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅'],
                "days_limit": 3600 * 24 * 2,
                "interval": 3600 * 2,
                "url": 'https://www.myip.com/',
                "scrapy_key": "chinatimes_keywords:start_urls",
                "priority": 1}]
        
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)
            
    
    def parse(self, response):
        meta = response.meta
        meta['page'] = 1
        for keyword in meta['keywords_list']:
            url=meta['url_pattern'].format(keyword)
            yield scrapy.Request(url,
                    meta=meta,
                    dont_filter=True,
                    callback=self.parse_list)
        

    def parse_list(self, response):
        # self.logger.debug('parse function called on %s',response.url)
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.error('parse function called on %s',response.url)

        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
        
        past = datetime.now() - timedelta(seconds=meta['days_limit'])
        link_date=[]
        for s in soup.findAll("div", class_="col"):
            link_date.append(datetime.strptime(s.find("time")['datetime'], '%Y-%m-%d %H:%M'))
            latest_datetime = link_date[-1]
            if(latest_datetime > past):
                url = s.find("h3", class_="title").find('a').get('href')
                yield response.follow(url,
                    meta=meta,
                    callback=self.parse_article)

        latest_datetime = max(link_date)
        past = datetime.now() - timedelta(seconds=meta['days_limit'])
        
        if latest_datetime < past:
            return

        current_page = re.search("page=(\d+)", response.url).group(1)
        next_page = re.sub("page=(\d+)", "page={}".format(int(current_page) + 1), response.url)

        yield scrapy.Request(next_page,
                dont_filter=True,
                meta=meta,
                callback=self.parse_list)


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
        item['media'] = 'chinatimes'
        item['proto'] = 'CHINATIMES_PARSE_ITEM'
        return item

    def parse_datetime(self, soup):
        date = soup.find('div','meta-info').find('time')['datetime']
        date = datetime.strptime( date , '%Y-%m-%d %H:%M')
        date = date.strftime('%Y-%m-%dT%H:%M:%S+0800')
        return date
    
    def parse_author(self, soup):
        author = re.findall('\S',soup.find('div','author').text)
        author = ''.join([x for x in author ]) 
        return author
    
    def parse_title(self, soup):
        title = soup.find('h1','article-title').text
        title = ' '.join(title.split())
        return title
    
    def parse_content(self, soup):
        # content = soup.find('head').find('meta',{'name':'description'})['content']
        articlebody = soup.find('div','article-body')
        for promote in articlebody.find_all('div','promote-word'):
            promote.clear()
        for hashtag in articlebody.find_all('div','article-hash-tag'):
            hashtag.clear()
        content = ''.join(articlebody.text.split())
        return content

    def parse_metadata(self, soup):
        keywords = soup.find('div','article-hash-tag').find_all('span','hash-tag')
        keywords = [x.text.replace('#','') for x in keywords]
        category = soup.find('meta',{'property':'article:section'})['content']
        image_url = soup.find('article','article-box').find_all('div','photo-container')
        image_url = [x.find('img')['src'] for x in image_url]
        metadata = {'tag': keywords, 'category':category, 'image_url':image_url}
        return metadata
    
