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
class Ltn_keywordsSpider(scrapy.Spider):
    name = "ltn_keywords"
    

    def start_requests(self):
            
        if isinstance(self, RedisSpider):
            return
        
        # url
        requests=[{
            "url": 'https://www.myip.com/',
            "url_pattern":"https://search.ltn.com.tw/list?keyword={}&type=all&sort=date&start_time={}&end_time={}&sort=date&type=all&page=1",
            "keywords_list": ['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅'],
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
            "media": "ltn",
            "name": "ltn_keywords",
            "scrapy_key": "ltn_keywords:start_urls",
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
        meta['page'] = 1
        #搜尋時間範圍      
        now=datetime.datetime.now()
        end_time=now.strftime("%Y%m%d")
        time_delta=datetime.timedelta(days=2) 
        start_time=(now-time_delta).strftime("%Y%m%d")
        for keyword in meta['keywords_list']:
            url=meta['url_pattern'].format(keyword,start_time,end_time)
            yield scrapy.Request(url,
                    meta=meta,
                    dont_filter=True,
                    callback=self.parse_list)
        

    def parse_list(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
        if(len(soup.findAll(class_="cont"))!=0):
            for s in soup.findAll(class_="cont"):
                url = s.find('a').get('href')
                if 'ec.ltn.com.tw' in url: 
                    yield response.follow(url,
                    meta=meta,
                    callback=self.parse_article_ec)      
                elif ('news.ltn.com.tw' in url):
                    yield response.follow(url,
                    meta=meta,
                    callback=self.parse_article_news)
                
            current_page = re.search("page=(\d+)", response.url).group(1)
            next_page = re.sub("page=(\d+)", "page={}".format(int(current_page) + 1), response.url)
        
            yield scrapy.Request(next_page,
                    dont_filter=True,
                    meta=meta,
                    callback=self.parse_list)
            
    def parse_article_ec(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
          
        metadata = {'category':'','image_url':[]}
        
        content, author, metadata['image_url'] = self.parse_content_author_image_ec(soup)
        
        title=soup.find(class_="whitecon boxTitle boxText").find('h1').string 
        metadata['category'] = '自由財經'
       
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

    def parse_article_news(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.body, 'html.parser')
          
        metadata = {'category':'','image_url':[]}
        
        content, author, metadata['image_url'] = self.parse_content_author_image_news(soup)
        
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
    
    def parse_content_author_image_ec(self,soup): 
        
        # content
        content=''
        for text in soup.find(class_="text").findAll('p')[1:4]:
            content=content+text.get_text()
        for text in soup.find(class_="text").findAll('p')[5:-2]:
            content=content+text.get_text()
            
        # author
        au = ''
        author_text=soup.find(class_='text').findAll('p')[1].get_text()
        begin=author_text.rfind('〔')
        end=author_text.find('／')
        if begin!=-1 & end!=-1:
            au=author_text[begin+1:end]
            if '記者' in au:
                au=au.replace('記者', '')
        
        # image
        image_url = []
        image_url.append(soup.find(class_='text').find(class_="lazy_imgs_ltn")['data-src'])

        return content, au, image_url

    def parse_content_author_image_news(self,soup): 
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