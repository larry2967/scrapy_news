
import redis
import pymongo
import ujson
import argparse
from utils import load_config
from scutils.redis_queue import Base, RedisQueue, RedisPriorityQueue, RedisStack

config = load_config()
SETTINGS = config['services']['mycrawler']['environment']

def get_config():
    urls = [
        "https:/www.google.com/"
    ]

    for url in urls:
        yield {
            "media": "cna",
            "name": "cna",
            "scrapy_key": "cna:start_urls",
            "url": "https://tw.yahoo.com/?p=us",
            "priority": 1,
            "search": False,
            "enabled": True,
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 ,
            "url": url,
            "url_pattern":"https://www.cna.com.tw/cna2018api/api/WNewsList",
            "headers":{
                'authority': 'www.cna.com.tw',
                'sec-ch-ua': '"Chromium";v="86", ""Not\\A;Brand";v="99", "Google Chrome";v="86"',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'x-requested-with': 'XMLHttpRequest',
                'sec-ch-ua-mobile': '?0',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
                'content-type': 'application/json',
                'origin': 'https://www.cna.com.tw',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': 'https://www.cna.com.tw/list/asoc.aspx',
                'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'cookie': 'ASP.NET_SessionId=hhql1tqyberadyrrhgzggyuq; __auc=bb901549175f3d8f68ce4014d78; _ga=GA1.3.1566804492.1606113884; _gid=GA1.3.1749205380.1606113884; CnaCloseLanguage=1; __asc=90bf7ff8175f42c505ffc56cd9b; _gat_UA-6826760-1=1'
            },
            'page': '1',
            'page_idx':'0'
        }


def save_to_redis(media):
    redis_key = "{}:start_urls".format(media)
    password = SETTINGS['REDIS_PASSWORD']
    r = redis.StrictRedis(password=password)
    q = RedisPriorityQueue(r, redis_key, encoding=ujson)
    for d in get_config():
        q.push(d, d['priority'])


def save_to_mongo(media):
    # m = pymongo.MongoClient(SETTINGS['MONGODB_SERVER'], SETTINGS['MONGODB_PORT'])
    m = pymongo.MongoClient('mongodb://%s:%s@%s'%(SETTINGS['MONGODB_USER'],SETTINGS['MONGODB_PASSWORD'],'localhost'))
    db = m['config']
    collection = db['urls']
    collection.delete_many({"media": media})

    for config in get_config():
        collection.insert_one(config)


if __name__ == '__main__':
    media = 'ltn'
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('-a')
    args = my_parser.parse_args()
    if 'run' == args.a:
        save_to_redis(media)
    elif 'save' == args.a:
        save_to_mongo(media)
    else:
        print('Please give action call')
