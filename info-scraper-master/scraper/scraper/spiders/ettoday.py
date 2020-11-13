# -*- coding: utf-8 -*-
import scrapy
import traceback, sys
from dateutil.parser import parse as date_parser
from scraper.items import NewsItem
from .redis_spiders import RedisSpider
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re

class EttodaySpider(RedisSpider):
# class EttodaySpider(scrapy.Spider):
    name = "ettoday"

    def start_requests(self):
        if isinstance(self, RedisSpider):
            return
        requests = [{
            "media": "ettoday",
            "name": "ettoday",
            "enabled": True,
            "days_limit": 3600 * 24 * 2,
            "interval": 3600 * 2,
            "url": "https://www.ettoday.net/",
            "tFile_format": "{date}-6.xml",
            "tPage":str(3),
            "tOt":str(6),
            "offset":1,
            "scrapy_key": "ettoday:start_urls",
            "priority": 1
        }]
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)
 
    def parse(self, response):
        meta = response.meta
        now = datetime.now()

        past = now - timedelta(seconds=meta['days_limit'])

        while True:
            
            meta['tFile'] = meta['tFile_format'].format(date=now.strftime('%Y%m%d'))

            meta['date'] = now.replace(hour=0, minute=0, second=0, microsecond=0)

            data = {
                'tFile': meta['tFile'],
                'tPage': meta['tPage'],
                'tOt': meta['tOt'],
                'offset': str(meta['offset']),
            }

            yield scrapy.FormRequest(
                    url = "https://www.ettoday.net/show_roll.php",
                    formdata= data,
                    method='POST',
                    meta=meta,
                    dont_filter=True,
                    callback=self.parse_list)

            now = now - timedelta(seconds=3600 * 24)
            if now <= past:
                break

    def parse_list(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'lxml')
        
        # no more news_list
        if not soup.find('h3'):
            return

        posts = soup.find_all('h3')

        for s in posts:
            yield response.follow(s.find('a')['href'],
                    meta=meta,
                    callback=self.parse_article)

        # if the time < 00:00, stop crawl the date 
        last_datetime = datetime.strptime(posts[-1].find('span','date').text, '%Y/%m/%d %H:%M')
        if meta['date'] > last_datetime:
            return

        # scroll 
        meta['offset'] += 1

        data = {
            'tFile': meta['tFile'],
            'tPage': meta['tPage'],
            'tOt': meta['tOt'],
            'offset': str(meta['offset']),
        }
        
        yield scrapy.FormRequest(
                url = "https://www.ettoday.net/show_roll.php",
                formdata= data,
                method='POST',
                meta=meta,
                dont_filter=True,
                callback=self.parse_list)
    

    def parse_article(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        item = NewsItem()
        item['url'] = response.url
        item['author'] = self.parse_author(soup)
        item['article_title'] = self.parse_title(soup)
        item['author_url'] = []
        item['content'] = self.parse_content(soup)
        item['comment'] = []
        item['date'] = self.parse_datetime(soup)
        item['metadata'] = self.parse_metadata(soup)
        item['content_type'] = 0
        item['media'] = 'ettoday'
        item['proto'] = 'ETTODAY_PARSE_ITEM'
        return item

    def parse_datetime(self,soup):
        try:
            datetime = soup.find_all('time', {'class': 'date'})[0]['datetime']
        except:
            datetime = soup.find_all('time', {'class': 'news-time'})[0]['datetime']
        datetime = datetime[:22]+datetime[-2:] #remove ':'
        return datetime
    
    def parse_title(self,soup):
        title = soup.select('h1')[0].text
        title = ' '.join(title.split())
        return title
    
    def parse_author(self,soup): 
        try:
            # try Columnist
            block = soup.find_all('div', {'class': 'penname_news clearfix'})
            for ele in block:
                penname = ele.find_all('a', {'class': 'pic'})
            author = penname[0]['href'].split('/')[-1]
            return author
        
        except:
            script = re.search('"creator": ."[0-9]+....', str(soup.select('script')[0]))
            author = re.findall(re.compile(u"[\u4e00-\u9fa5]+"), str(script))
            return author[0] if len(author) else ''
        
    def parse_content(self,soup):
        article = soup.find('div', class_='story')
        paragraph = []
        for p in article.find_all('p'):
            text = p.text.strip()
            if len(text) == 0 or text[0]=='►':
                continue
            paragraph.append(text)
            
        content = '\n'.join(paragraph)
        content = content.split('【更多鏡週刊相關報導】')[0]
        return content
    
    def parse_metadata(self,soup):
        metadata = {'category':'', 'fb_like_count': '','image_url':[]}
        metadata['category'] = soup.find('meta',{'property':'article:section'})['content']
        image_url = soup.find('div', class_='story').find_all('img')
        metadata['image_url'] = ['https:' + x['src'] for x in image_url]
        return metadata
