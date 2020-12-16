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

# class Appledaily_keywordsSpider(RedisSpider):
class Appledaily_keywordsSpider(scrapy.Spider):
    name = 'appledaily_keywords'

    def start_requests(self):

        if isinstance(self, RedisSpider):
            return
       
        requests = [
            {
                "media": "appledaily",
                "name": "appledaily_keywords",
                "scrapy_key": "appledaily_keywords:start_urls",
                "url":"https://tw.appledaily.com/daily/headline/",
                "url_pattern":"https://tw.appledaily.com/pf/api/v3/content/fetch/search-query?query=%7B%22searchTerm{}start%22%3A{}%7D&d={}&_website=tw-appledaily",
                "keywords_list": ['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅'],
                "page": 0,
                "priority": 1,
                "enabled": True,
                "days_limit": 3600 * 24 * 2, 
                "interval": 3600 * 2,
            }
        ]
           
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)
        
    def parse(self,response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
        
        fusion_engine_script = soup.find('script',{'id':'fusion-engine-script'})
        d = fusion_engine_script['src'].split('?d=')[-1]
        
        #關鍵字
        key_dict = {'吸金':'%22%3A%22%25E5%2590%25B8%25E9%2587%2591%22%2C%22',
                    '地下通匯':'%22%3A%22%25E5%259C%25B0%25E4%25B8%258B%25E9%2580%259A%25E5%258C%25AF%22%2C%22',
                    '洗錢':'%22%3A%22%25E6%25B4%2597%25E9%258C%25A2%22%2C%22',
                    '賭博':'%22%3A%22%25E8%25B3%25AD%25E5%258D%259A%22%2C%22',
                    '販毒':'%22%3A%22%25E8%25B2%25A9%25E6%25AF%2592%22%2C%22',
                    '走私':'%22%3A%22%25E8%25B5%25B0%25E7%25A7%2581%22%2C%22',
                    '仿冒':'%22%3A%22%25E4%25BB%25BF%25E5%2586%2592%22%2C%22',
                    '犯罪集團':'%22%3A%22%25E7%258A%25AF%25E7%25BD%25AA%25E9%259B%2586%25E5%259C%2598%22%2C%22',
                    '侵占':'%22%3A%22%25E4%25BE%25B5%25E4%25BD%2594%22%2C%22',
                    '背信':'%22%3A%22%25E8%2583%258C%25E4%25BF%25A1%22%2C%22',
                    '內線交易':'%22%3A%22%25E5%2585%25A7%25E7%25B7%259A%25E4%25BA%25A4%25E6%2598%2593%22%2C%22',
                    '行賄':'%22%3A%22%25E8%25A1%258C%25E8%25B3%2584%22%2C%22',
                    '詐貸':'%22%3A%22%25E8%25A9%2590%25E8%25B2%25B8%22%2C%22',
                    '詐欺':'%22%3A%22%25E8%25A9%2590%25E6%25AC%25BA%22%2C%22',
                    '貪汙':'%22%3A%22%25E8%25B2%25AA%25E6%25B1%25A1%22%2C%22',
                    '逃稅':'%22%3A%22%25E9%2580%2583%25E7%25A8%2585%22%2C%22'}

        for key_name in meta['keywords_list']:
            meta.update({'d':d})
            meta.update({'key':key_dict[key_name]})
            yield scrapy.Request(meta['url_pattern'].format(meta['key'], str(meta['page']), meta['d']),
                    meta=meta,
                    dont_filter=True,
                    callback=self.parse_list)
    
    def parse_list(self, response):
        meta = response.meta
        result = json.loads(response.body)

        past = datetime.now() - timedelta(seconds=meta['days_limit'])

        page_len = len(result['content'])
        page = meta['page'] + page_len
        meta.update({'page':page})

        for i in range(0,page_len):
            url = result['content'][i]['sharing']['url']
            img = result['content'][i]['sharing']['image']
            time = result['content'][i]['issueId']
            category = result['content'][i]['brandCategoryName']

            meta.update({'category_name':category})
            meta.update({'img':img})

            time = datetime.strptime(time, '%Y%m%d')
            if (time < past):
                return

            yield scrapy.Request(url,
                    callback=self.parse_article,
                    meta=meta)

        next_page = meta['url_pattern'].format(meta['key'], str(meta['page']), meta['d']) 
        yield scrapy.Request(next_page,
                meta=meta,
                dont_filter=True,
                callback=self.parse_list)

    def parse_article(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        meta = response.meta
        content = self.parse_content(soup)

        item = NewsItem()
        item['url'] = response.url
        item['author'] = self.parse_author(content)
        item['article_title'] = self.parse_title(soup)
        item['author_url'] = []
        item['comment'] = []
        item['date'] = self.parse_datetime(soup)
        item['metadata'] = self.parse_metadata(soup,meta)
        item['content'] = content
        item['content_type'] = 0
        item['media'] = 'appledaily'
        item['proto'] = 'APPLEDAILY_KEYWORDS_PARSE_ITEM'
        return item

    def parse_datetime(self, soup):
        date = soup.find('div',{'class':'timestamp'}).text[6:]
        try:
            date = datetime.strptime( date , '%Y/%m/%d %H:%M')
            date = date.strftime('%Y-%m-%dT%H:%M:%S+0800')
        except:
            print('not in a date format')
        return date
    
    
    def parse_title(self, soup):
        title = soup.find('div',{'class':'article__header'}).find('span').text
        return title
    
    def parse_content(self, soup):
        # content = soup.find('head').find('meta',{'name':'description'})['content']
        articlebody = soup.find('div',{'id':'articleBody'}).text
        
        return articlebody

    def parse_metadata(self, soup,meta):
        category = meta['category_name']
        try:
            image_url = meta['img']
        except:
            image_url = ''
        metadata = {'category':category, 'image_url':image_url}
        return metadata
    
    def parse_author(self, content):
        content = content.replace('(','（')
        content = content.replace(')','）')
        re_pattern = ["（(.{,20})／(.{,5})報導）", "【(.{,20})／(.{,5})報導】"]
        re_rslt = []

        for p in re_pattern:
            search_rslt = re.search(p, content)
            if search_rslt != None:
                re_rslt.append(search_rslt.group(1)) 

        if re_rslt!=[]:
            author = re_rslt[0]
        else:
            author = ''
        return author