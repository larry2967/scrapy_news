# -*- coding: utf-8 -*-
import numpy as np
import scrapy
from itertools import chain
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from scraper.items import NewsItem
import re
import json
from .redis_spiders import RedisSpider

class AppledailySpider(RedisSpider):
# class AppledailySpider(scrapy.Spider):
    name = 'appledaily'

    def start_requests(self):

        if isinstance(self, RedisSpider):
            return

        request = {
            "url_pattern": 'https://tw.appledaily.com/pf/api/v3/content/fetch/query-feed?query=%7B%22feedOffset%22%3A0%2C%22feedQuery%22%3A%22taxonomy.primary_section._id%3A%5C%22%2Frealtime%2Flocal%5C%22%2BAND%2Btype%3Astory%2BAND%2Bpublish_date%3A%5Bnow-48h%2Fh%2BTO%2Bnow%5D%22%2C%22feedSize%22%3A%22100%22%2C%22sort%22%3A%22display_date%3Adesc%22%7D&d={}&_website=tw-appledaily',
            "url": 'https://tw.appledaily.com/realtime/local/',
            "priority": 1,
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
            'scrapy_key': 'appledaily:start_urls',
            'media': 'appledaily',
            'name': 'appledaily',
            'enabled': True,
        }
        yield scrapy.Request(request['url'],
                dont_filter=True,
                meta = request)

    def parse(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
        fusion_engine_script = soup.find('script',{'id':'fusion-engine-script'})
        d = fusion_engine_script['src'].split('?d=')[-1]
        yield scrapy.Request(meta['url_pattern'].format(d),
                dont_filter=True,
                callback=self.parse_article)
        

    def parse_article(self, response):
        result = json.loads(response.body)
        news_lists = result['content_elements']
        for news_list in news_lists:
            if 'video' in news_list['website_url']:
                continue
            content = self.parse_content(news_list['content_elements'])
            item = NewsItem()
            item['url'] = 'https://tw.appledaily.com' + news_list['website_url']
            item['article_title'] = ' '.join(news_list['headlines']['basic'].split())
            item['metadata'] = self.parse_metadata(news_list['taxonomy'],news_list['additional_properties'],news_list['content_elements'])
            item['date'] = self.parse_datetime(news_list['created_date'])
            item['content'] = content  
            item['author'] = self.parse_author(content)
            item['author_url'] = []
            item['comment'] = []
            item['media'] = 'appledaily'
            item['content_type'] = 0
            item['proto'] = 'APPLEDAILY_PARSE_ITEM'
            yield item
    
    def parse_datetime(self,created_date):
        date = datetime.strptime(created_date.split('.')[0] , '%Y-%m-%dT%H:%M:%S')
        date = date + timedelta(hours=8)
        return date.strftime('%Y-%m-%dT%H:%M:%S+0800')

    def parse_content(self,content_elements):
        content_html = ''
        for cont in content_elements[:2]:
            if cont['type']=='text' or cont['type']=='raw_html':
                content_html += cont['content']
        soup = BeautifulSoup(content_html,'html.parser')
        content = soup.text
        return ''.join(content.split())


    def parse_metadata(self,taxonomy,promo_items,content_elements):
        image_url = []
        if 'basic' in promo_items.keys():
            if 'url' in promo_items['basic'].keys():
                image_url.append(promo_items['basic']['url'])
        for cont in content_elements[2:]:
            if 'additional_properties' in cont.keys():
                if 'originalUrl' in cont['additional_properties'].keys():
                    image_url.append(cont['additional_properties']['originalUrl'])
        metadata = {
                'tag': [tag['text'] for tag in taxonomy['tags']],
                'category': taxonomy['primary_section']['name'],
            'image_url':image_url
            }
        return metadata

    def parse_author(self,content):
        content = content.replace('(','（')
        content = content.replace(')','）')
            
        end_indx = []
        for m in re.finditer('報導）', content):
            end_indx.append(m.start())            
            
        start_indx = []
        for m in re.finditer('（', content):
            start_indx.append(m.end())
            
        if len(end_indx)!=1 or len(start_indx)==0:
            author = ''
        else:
            find_close = end_indx[0] - np.array(start_indx)
            start_indx = start_indx[ np.where( find_close == min(find_close[find_close>0]) )[0][0] ]
            author = re.split('／',content[start_indx:end_indx[0]])[0]
        return author
    