from scrapy import signals
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from collections import defaultdict
import json
import random
import redis

class RandomProxyMiddleware(object):
    def __init__(self, settings):
        self.proxies = defaultdict(list)
        host = settings.get('REDIS_HOST')
        port = settings.get('REDIS_PORT')
        redis_params = settings.get('REDIS_PARAMS', {})
        password = redis_params.get('password', 'lala2020')
        self.redis = redis.Redis (host, port, 0, password)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)


    def process_request(self, request, spider):
        if 'random_proxy' not in request.meta:
            return

        # Get the Proxy List in Redis
        proxies = self.redis.smembers('eng_proxies')
        if not proxies:
            proxies = self.redis.smembers('all_proxies')

        if not proxies:
            return

        proxies = list(proxies)
        proxy_index = random.randint(0, len(proxies) - 1)
        ip_port = proxies[proxy_index]
        print('random proxy {}'.format(ip_port))
        request.meta['proxy'] = str(ip_port, 'utf-8')