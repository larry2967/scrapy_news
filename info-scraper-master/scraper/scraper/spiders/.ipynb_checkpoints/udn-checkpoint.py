# -*- coding: utf-8 -*-
import scrapy
import traceback, sys
from dateutil.parser import parse as date_parser
from scraper.items import NewsItem
from .redis_spiders import RedisSpider
# from scrapy_redis.spiders import RedisSpider
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import json
import re
import urllib

# class UDNSpider(RedisSpider):
class UDNSpider(scrapy.Spider):
    name = "udn"

    def start_requests(self):
        if isinstance(self, RedisSpider):
            return
        requests = [{
            "media": "udn",
            "name": "udn",
            "enabled": True,
            "days_limit": 3600 * 24,
            "interval": 3600,
            "url": "https://udn.com/api/more?page=1&id=&channelId=1&cate_id=1&type=breaknews&totalRecNo=287",
            "scrapy_key": "udn:start_urls",
            "priority": 1,
        }]
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)
 

    def parse(self, response):
        meta = response.meta
        body = json.loads(response.body)

        # no more news
        if body['end'] == True:
            return

        links_date = []
        for url in body['lists']:
            str_date = url['time']['date']
            links_date.append(datetime.strptime(str_date, '%Y-%m-%d %H:%M'))
            meta.update({
                'title': url['title'],
                'datetime': str_date,
                'view_count': url['view'],
                'image_url': url['url']
            })
            yield response.follow(url['titleLink'].split('?')[0],
                    meta=meta,
                    callback=self.parse_article)

        latest_datetime = max(links_date)
        past = datetime.now() - timedelta(seconds=meta['days_limit'])
        if latest_datetime < past:
            return

        current_page = re.search("page=(\d+)", response.url).group(1)
        next_page = re.sub("page=(\d+)", "page={}".format(int(current_page) + 1), response.url)

        yield scrapy.Request(next_page,
                dont_filter=True,
                meta=meta,
                callback=self.parse)

    
    def parse_article(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
        
        if 'opinion.udn.com' in response.url:
            content = self.parse_opinion_content(soup)
            author = self.parse_opinion_author(soup)
        else:
            content = self.parse_content(soup)
            author = self.parse_author(soup)

        item = NewsItem()
        item['url'] = response.url
        item['date'] = self.parse_datetime(meta['datetime'])
        item['content'] = content
        item['author'] = author
        item['article_title'] = meta['title'] #self.parse_title(soup)
        item['author_url'] = []
        item['comment'] = []
        item['metadata'] = self.parse_metadata(soup,meta['view_count'],meta['image_url'])
        item['content_type'] = 0
        item['media'] = 'udn'
        item['proto'] = 'UDN_PARSE_ITEM'
        yield item
            

    def parse_datetime(self, date):
        date = datetime.strptime(date, '%Y-%m-%d %H:%M').strftime('%Y-%m-%dT%H:%M:%S+0800')
        return date
    
    def parse_title(self, soup):
        return soup.find('meta', {'property':'og:title'})['content'].split(' | ')[0]
            
    def parse_content(self, soup):
        
        article = soup.find('article', class_='article-content') 
        
        if article==None:  
            content= soup.find(property="og:description")['content']
        else:
            if article.find_all('script')==None:
                content= soup.find(property="og:description")['content']

            else:    
                # filter java script
                for tag in article.find_all('script'):
                    tag.clear()
                # filter paywall-content
                for tag in article.find_all('div','paywall-content'):
                    tag.clear()

                content = ''.join([ent.text for ent in article.find_all('p')])
                content = ''.join(content.split())
                if '【相關閱讀】' in content:
                    content = content.split('【相關閱讀】')[0]
                
        return content
    
    def parse_opinion_content(self, soup):
        for tag in soup.find_all('style', {'type': 'text/css'}):
            tag.clear()
        return ''.join([ent.text for ent in soup.find_all('p')[:-1]]).replace('\n', '')

    def parse_author(self, soup):
        if soup.find('div',{'id':'story_author'}) != None:
            author = soup.find('div',{'id':'story_author'})
            author = author.find('h2',{'id':'story_author_name'}).text

        elif soup.find('span','article-content__author') != None:
            if soup.find('span','article-content__author').find('a') != None:
                author = soup.find('span','article-content__author').find('a').text
            else:
                author = soup.find('span','article-content__author').text

        else:
            author = ''
        author = ''.join(author.split())
        return author    
    
    def parse_opinion_author(self, soup):
        author = soup.find('div', class_='story_bady_info_author').find('a').text
        return author

    def parse_metadata(self, soup, view_count, image_url,fb_like_count_html=None):
        metadata = {'tag':[], 'category':'','view_count':view_count, 'image_url':[],'fb_like_count':''}
        try: 
            metadata['tag'] = soup.find('meta', {'name':'news_keywords'})['content'].split(',')    
        except:
            pass 

        category = soup.find_all('a','breadcrumb-items')
        if len(category) == 3:
            metadata['category'] = category[1].text
        else:
            metadata['category'] = soup.find('meta', {'name': 'application-name'})['content']
        
        if image_url!='':
            metadata['image_url'].append(image_url)
        return metadata
