# -*- coding: utf-8 -*-
import scrapy
import re
import json
from .redis_spiders import RedisSpider
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from scraper.items import NewsItem
from dateutil.parser import parse as date_parser

class MirrormediaSpider(scrapy.Spider):
# class MirrormediaSpider(RedisSpider):
    name = 'mirrormedia'

    def start_requests(self):
        if isinstance(self, RedisSpider):
            return
        requests = [{
            "media": "mirrormedia",
            "name": "mirrormedia",
            "enabled": True,
            "days_limit": 3600 * 24 * 2,
            "interval": 3600,
            "url": "https://www.mirrormedia.mg/api/getlist?max_results=12&sort=-publishedDate&where=%7B%22categories%22%3A%7B%22%24in%22%3A%5B%225979ac33e531830d00e330a9%22%5D%7D%7D&page=1",
            "scrapy_key": "mirrormedia:start_urls",
            "priority": 1
        }]
        for request in requests:
            yield scrapy.Request(request['url'],
                    meta=request,
                    dont_filter=True,
                    callback=self.parse)

    def parse(self, response):
        meta = response.meta
        res, max_page = self.parse_json(response.body.decode('utf-8', 'ignore'))
        
        items = res.get("_items", [])
        links = []
        datetimes = []
        html_base = "https://www.mirrormedia.mg/story/"
        for item in items:
            links.append(html_base + item["slug"])
            dt = datetime.strptime(item["publishedDate"],
                                '%a, %d %b %Y %H:%M:%S %Z')
            datetimes.append(dt)


        for link in links:
            yield scrapy.Request(link,
                    #dont_filter=True,
                    meta=meta,
                    callback=self.parse_article)

        if len(datetimes) == 0:
            return

        latest_datetime = max(datetimes)

        past = datetime.now() - timedelta(seconds=meta['days_limit'])

        if latest_datetime < past:
            return

        next_page = self.handle_next_page(response.url, max_page)
        print(next_page)
        if next_page is None:
            return

        yield scrapy.Request(next_page,
                meta=meta,
                dont_filter=True,
                callback=self.parse)
        

    def parse_json(self, html):
        res = json.loads(html)
        try:
            url = res["_links"]["last"]["href"]
            re_list = re.search(r'page=[0-9]+', url).group().split("=")
            max_page = int(re_list[1])
        except:
            max_page = 1
        return res, max_page

    def handle_next_page(self, url, max_page):
        re_list = re.search(r'page=(\d+)', url).group().split("=")
        cur_page_num = int(re_list[1])
        if cur_page_num < max_page:
            re_list[1] = str(cur_page_num + 1)
            next = "=".join(re_list)
            next_page = url.replace(
                re.search('page=(\d+)', url).group(), next)
        else:
            next_page = None
        return next_page

    def parse_article(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.body.decode('utf-8', 'ignore'), 'html.parser')
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
        item['media'] = meta['media']
        item['proto'] =  'MIRRORMEDIA_PARSE_ITEM'
        yield item

    def parse_datetime(self, soup):
        time_ = soup.find("p", "story__published-date").text
        post_datetime = date_parser(time_) + timedelta(hours=8)
        return post_datetime.strftime('%Y-%m-%dT%H:%M:%S+0800')

    def parse_author(self, soup):
        try:
            author = soup.find('div','story__credit').text.strip().replace(
                u'\u3000', u' ').replace(u'\xa0', u' ')
            writer = re.search(".[\u4e00-\u9fa5]+", author).group()[1:]
        except:
            writer = ''
        return writer

    def parse_title(self, soup):
        return soup.h1.text.strip().replace(u'\u3000',
                                            u' ').replace(u'\xa0', u' ')

    def parse_content(self, soup):
        # clear 更多內容...
        for story_end in soup.findAll('p',{'id':'story-end'}):
            story_end.clear()

        content = ""
        for txt in soup.findAll("p", class_="g-story-paragraph"):
            for strong in txt.findAll('strong'):
                strong.clear()
            content += txt.text
        return content.strip().replace(u'\u3000', u' ').replace(u'\xa0', u' ')

    def parse_metadata(self, soup):
        
        try:
            category = soup.find('meta',{'property':'article:section'})['content']
        except:
            category = ''
        
        key = []
        try:
            for world in soup.find("div", "tags"):
                key.append(world.text)
        except:
            pass

        image_url = []
        image_url.append(json.loads(soup.find('script', {'type': 'application/ld+json'}).get_text())['image'])

        return {
            'tag': key,
            'category':category,
            'image_url': image_url
        }
