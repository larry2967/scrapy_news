# -*- coding: utf-8 -*-
import os
import datetime
# Scrapy settings for scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# import logging
# # from scrapy.utils.log import configure_logging

# logging.basicConfig(
#     filename='log.txt',
#     format='%(levelname)s: %(message)s',
#     level=logging.INFO
# )
# LOG_LEVEL = 'ERROR'
# to_day = datetime.datetime.now()
# LOG_FILE = 'log/scrapy_{}_{}_{}.log'.format(to_day.year,to_day.month,to_day.day)

BOT_NAME = 'scraper'

SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'scraper (+http://www.yourdomain.com)'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Enables scheduling storing requests queue in redis.
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'scraper.middlewares.ScraperSpiderMiddleware': 543,
#}

# Retry when proxies fail
RETRY_TIMES = 3

# Retry on most error codes since proxies fail for different reasons
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'scrapy_html_storage.HtmlStorageMiddleware': 10,
    #'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 100,
    'scraper.proxyMiddleware.RandomProxyMiddleware': 100,
#    'scraper.middlewares.ScraperDownloaderMiddleware': 543,
}

# do certificate verification, or even enable client-side authentication
# DOWNLOADER_CLIENTCONTEXTFACTORY = 'scrapy.core.downloader.contextfactory.BrowserLikeContextFactory'

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
#    'scraper.pipelines.ScraperPipeline': 300,
    'scraper.pipelines.TransformDataPipeline':100,
#    'scraper.pipelines.EvaluationPipeline':200,
    # 'scraper.pipelines.SaveToElasticsearchPipeline':300, # replace `SaveToFilePipeline` with this to use elasticsearch
    'scraper.pipelines.SaveToMongoPipeline':300, # replace `SaveToFilePipeline` with this to use MongoDB
    # 'scraper.pipelines.SaveToSqlDBPipeline':300, # replace `SaveToFilePipeline` with this to use SqlDB
    #'scraper.pipelines.SaveToRabbitMQPipeline':200, 
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Redis Connection Info
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_PARAMS = {
    'password': os.environ.get("REDIS_PASSWORD", "lala2020"),
}

#MongoDB Connection Info
MONGODB_SERVER = os.environ.get("MONGODB_SERVER", "localhost")
MONGODB_PORT = os.environ.get('MONGODB_PORT', 27017)
MONGODB_DB = os.environ.get('MONGODB_DB', "debug")        # database name to save the crawled data
MONGODB_DATA_COLLECTION = os.environ.get('MONGODB_DATA_COLLECTION', "debug")
MONGODB_USER = os.environ.get('MONGODB_USER')
MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD')

#SqlDB Connection Info
SQLDB_SERVER = os.environ.get("SQLDB_SERVER", "localhost")
SQLDB_PORT = os.environ.get('SQLDB_PORT', 5432)
SQLDB_DB = os.environ.get('SQLDB_DB')        # database name to save the crawled data
SQLDB_DATA_TABLE = os.environ.get('SQLDB_DATA_TABLE')
SQLDB_USERNAME = os.environ.get('SQLDB_USERNAME')
SQLDB_PASSWORD = os.environ.get('SQLDB_PASSWORD')

# Elasticsearch Info
ELASTICSEARCH_SERVERS = os.environ.get('ELASTICSEARCH_SERVERS', 'localhost')
ELASTICSEARCH_TIMEOUT = 60
ELASTICSEARCH_USERNAME = os.environ.get('ELASTICSEARCH_USERNAME')
ELASTICSEARCH_PASSWORD = os.environ.get('ELASTICSEARCH_PASSWORD')
ELASTICSEARCH_INDEX = os.environ.get('ELASTICSEARCH_INDEX', 'debug')
ELASTICSEARCH_TYPE = os.environ.get('ELASTICSEARCH_TYPE', 'debug')