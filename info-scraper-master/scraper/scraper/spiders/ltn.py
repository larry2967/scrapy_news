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
# from scrapy_redis.spiders import RedisSpider

# class LtnSpider(RedisSpider):
class LtnSpider(scrapy.Spider):
    name = "ltn"

    def start_requests(self):

        if isinstance(self, RedisSpider):
            return

        requests = [
        {
            "url": "https://www.myip.com/",
            "priority": 3,
            "search": False,
            "url_pattern": "https://news.ltn.com.tw/ajax/breakingnews/society/{}",
            "interval": 3600,
            "days_limit": 3600 * 24 
        },
        {
        "url": "https://www.myip.com/",
            "priority": 3,
            "search": False,
            "url_pattern": "https://news.ltn.com.tw/ajax/breakingnews/politics/{}",
            "interval": 3600,
            "days_limit": 3600 * 24

        }]
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)
        # yield scrapy.Request(request['url'],
        #         meta = request)
                
    def parse(self, response):
        meta = response.meta
        meta['page'] = 1
        url = meta['url_pattern'].format(1)
        yield scrapy.http.Request(url,
            dont_filter=True,
            callback=self.parse_list,
            meta=meta
        )

    def parse_list(self, response):
        content = response.body
        meta = response.meta
        page = meta['page']
        search_page = meta['search']
        if not search_page:
            data = json.loads(response.body)
            if isinstance(data['data'], list):
                _iteration = data['data']
                latest_datetime = date_parser(_iteration[0]['time'])
            elif isinstance(data['data'], dict):
                _iteration = data['data'].values()
                latest_datetime = date_parser(list(_iteration)[0]['time'])

            if len(_iteration) == 0:
                return
                #raise scrapy.exceptions.CloseSpider('Response is Empty')

            for article in _iteration:
                url = article['url']
                new_meta = article.copy()
                new_meta.update(meta)
                yield scrapy.Request(url, 
                        callback=self.parse_article, 
                        meta=new_meta)
        else:
            soup = BeautifulSoup(content, 'html.parser')
            latest_datetime = ''
            for link in soup.find_all('a', class_='tit'):
                url = link.get('href')
                yield scrapy.Request(url,
                        callback=self.parse_article,
                        dont_filter=True)

        past = datetime.now() - timedelta(seconds=meta['days_limit'])
        if latest_datetime < past:
            return

        page = page + 1
        meta.update({'page': page})
        url = meta['url_pattern'].format(page)
        yield scrapy.Request(url,
                callback=self.parse_list,
                dont_filter=True,
                meta=meta)

    def parse_article(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
          
        metadata = {'category':'','image_url':[]}
        
        content, author, metadata['image_url'] = self.parse_content_author_image(soup)
        
        if 'title' in meta and 'tagText' in meta:
            title = meta['title']
            metadata['category'] = meta.get('tagText', "")
        else:
            title, metadata['category'] = self.parse_title_metadata(soup)
       
        item = NewsItem()
        item['url'] = response.url
        item['article_title'] = title
        item['author'] = author
        item['author_url'] = []
        item['comment'] = []
        item['date'] = self.parse_datetime(soup)
        item['content'] = content
        item['metadata'] = metadata
        item['content_type'] = 0
        item['media'] = 'ltn'
        item['proto'] = 'LTN_PARSE_ITEM'
        return item


    def parse_datetime(self,soup):
        date = soup.find('meta', {'name':'pubdate'})
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
            
    
    def find_author(self,list_text):
        list_text = [x for x in list_text if x!='文']
        tmp = [x for x in list_text if '記者' in x]
        if tmp:
            author = tmp[0].replace('記者', '').replace('攝影', '').strip()                
        else:
            author = min(list_text, key=len)
        return author
        

    def parse_content_author_image(self,soup): 
        content = soup.find('div',{'itemprop':'articleBody'})

        # image
        image_url = []
        for photo in content.find_all('div','photo boxTitle'):
            image_url.append(photo.find('img')['src'])

        # content
        for appE1121 in content.find_all('p','appE1121'):
            appE1121.clear()
        for photo in content.find_all('div','photo boxTitle'):
            photo.clear()
        for photo in content.find_all('span','ph_b ph_d1'):
            photo.clear()
        for tag in content.find_all('script'):
            tag.clear()
        content = ''.join(x.text for x in content.find_all('p') if x.text!='爆')
        content = ''.join(content.split())

        #author
        au = ''
        reg = re.compile(r'(［\D*／\D*］|〔\D*／\D*〕)', re.VERBOSE)
        author_reg = reg.findall(content)
        if author_reg:
            au = author_reg[0].split('／')[0].replace('〔', '').replace('［', '').replace('記者', '').replace('編譯', '')

        if not au:
            author = soup.find('div', {'class':'writer boxTitle'})
            if author: 
                au = author.find('a')['data-desc']
        if not au:
            author = soup.find('p', {'class':'auther'})
            if author:
                tmp = author.find('span').text.split('／')
                au = self.find_author(tmp)
        if not au:        
            author = soup.find('p', {'class':'writer'})
            if author:
                tmp = author.find('span').text.split('／')
                au = self.find_author(tmp)
        if not au:        
            author = soup.find('div', {'class':'writer'})
            if author:
                tmp = author.find('span').text.split('／')
                au = self.find_author(tmp)
        if not au: 
            author = soup.find('div', {'class':'conbox_tit boxTitle'})
            if author:
                au = author.find('a')['data-desc']
        if not au:
            author = soup.find('div', {'class':'article_header'})
            if author:
                tmp = author.find('span').text.split('／')
                au = self.find_author(tmp)
        if not au:
            try:
                author = soup.find('div', {'itemprop':'articleBody'}).find('p')
            except:
                author = ''
            if author:
                if '／' in author.text:
                    tmp = author.text.split('／')
                    au = self.find_author(tmp)
                if author.find('strong'):
                    au = author.find('strong').text.split('◎')[1].replace('記者', '').replace('攝影', '').strip()
                if '■' in author.text:
                    au = author.text.replace('■', '')
        if not au:
            try:
                author = soup.find('div', {'itemprop':'articleBody'}).find('span', {'class':'writer'})
            except:
                author = ''
            if author:
                if '／' in author.text:
                    tmp = author.text.split('／')
                    au = self.find_author(tmp)
        if not au:
            try:
                author = soup.find('div', {'itemprop':'articleBody'}).find('h4')
            except:
                author = ''
            if author:
                if '／' in author.text:
                    tmp = author.text.split('／')
                    au = self.find_author(tmp)
                elif '◎' in author.text:
                    au = author.text.replace('◎', '')
        return content, au, image_url