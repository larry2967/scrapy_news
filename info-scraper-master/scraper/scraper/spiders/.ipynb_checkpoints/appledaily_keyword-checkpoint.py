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

# class AppledailySpider(RedisSpider):
class Appledaily_keywordSpider(scrapy.Spider):
    name = 'appledaily_keyword'

    def start_requests(self):

        if isinstance(self, RedisSpider):
            return

        requests = []
        #關鍵字
        keywords_list=['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅']
        for keyword in keywords_list:
            url='https://tw.appledaily.com/search/{}/'.format(keyword)
            item={"media": "appledaily",
                "name": "",
                "enabled": True,
                "days_limit": 3600 * 24 * 0.5,
                "interval": 3600 * 2,
                "url": url,
                "url_pattern":'https://tw.appledaily.com/pf/api/v3/content/fetch/query-feed?query=%7B%22feedQuery%22%3A%22_id%3DXFS3IT4RMFFVXARHNSXTDRBJVQ%2520V2SHJX335VEELGD527WHB3IEMY%2520NMOO6JXAJVHSHNPWEKQ2XVD2HY%2520JWS4JJEOC5FXZOAJTYE6EZPEAI%2520DCKPTHC4QBH33M6G6E4H7IXV2E%2520CGVQQBFV25BJVHF5SR43BG6P5E%25204RO33VY6TNADTIIZOW747LUFDA%252067NT2GIWJFFRDHFFCPMAEIPN74%2520WAF436DRHJBZXO7QNEJNHQERBA%2520QB4MH35UYBGAHMSCUKONLBKZTM%22%2C%22feedSize%22%3A10%7D&filter=%7B_id%2Ccontent_elements%7B_id%2Ccanonical_url%2Ccreated_date%2Cdisplay_date%2Cheadlines%7Bbasic%7D%2Clast_updated_date%2Cpromo_items%7Bbasic%7B_id%2Ccaption%2Ccreated_date%2Cheight%2Clast_updated_date%2Cpromo_image%7Burl%7D%2Ctype%2Curl%2Cversion%2Cwidth%7D%2Ccanonical_website%2Ccredits%2Cdisplay_date%2Cfirst_publish_date%2Clocation%2Cpublish_date%2Crelated_content%2Csubtype%7D%2Crevision%2Csource%7Badditional_properties%2Cname%2Csource_id%2Csource_type%2Csystem%7D%2Ctaxonomy%7Bprimary_section%7B_id%2Cpath%7D%2Ctags%7Btext%7D%7D%2Ctype%2Cversion%2Cwebsite%2Cwebsite_url%7D%2Ccount%2Ctype%2Cversion%7D&d={}&_website=tw-appledaily',
                "scrapy_key": "appledaily:start_urls",
                "priority": 1}
            requests.append(item)
        
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)

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
        print('-------------new_lists_________')
        print(news_lists)
        for news_list in news_lists:
            if 'video' in news_list['website_url']:
                continue
            content = self.parse_content(news_list['content_elements'])
            print(content)
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
    