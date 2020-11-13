# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field

class NewsItem(Item):
    url = Field()
    article_title = Field()
    author = Field()
    author_url = Field()
    comment = Field()
    date = Field()
    content = Field()
    metadata = Field()
    media = Field()
    content_type = Field()
    proto = Field()
    proto_id = Field()
