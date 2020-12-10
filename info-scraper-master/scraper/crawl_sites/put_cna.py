import redis
import pymongo
import ujson
import argparse
from utils import load_config
from scutils.redis_queue import Base, RedisQueue, RedisPriorityQueue, RedisStack

config = load_config()
SETTINGS = config['services']['mycrawler']['environment']

def get_config():
    requests = [
        {
            "media": "cna",
            "name": "cna",
            "scrapy_key": "cna:start_urls",
            "url": "https://www.cna.com.tw/",
            "url_api":"https://www.cna.com.tw/cna2018api/api/WNewsList",
            "headers": {
                'authority': 'www.cna.com.tw',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'x-requested-with': 'XMLHttpRequest',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
                'content-type': 'application/json',
                'origin': 'https://www.cna.com.tw',
                'referer': 'https://www.cna.com.tw/list/asoc.aspx',
                'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            "page": "1",
            "priority": 1,
            "enabled": True,
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
        },
        {
            "media": "cna",
            "name": "cna_keywords",
            "scrapy_key": "cna_keywords:start_urls",
            "url":"https://www.cna.com.tw",
            "url_pattern": "https://www.cna.com.tw/search/hysearchws.aspx?q={}",
            "keywords_list":['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅'],
            "priority": 1,
            "enabled": True,
            "days_limit": 3600 * 24 * 2,
            "interval": 3600 * 2,
        }
    ]

    for req in requests:
        yield req


def save_to_redis():
    password = SETTINGS['REDIS_PASSWORD']
    r = redis.StrictRedis(password=password)
    for d in get_config():
        q = RedisPriorityQueue(r, d['scrapy_key'], encoding=ujson)
        q.push(d, d['priority'])


def save_to_mongo(media):
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
        save_to_redis()
    elif 'save' == args.a:
        save_to_mongo(media)
    else:
        print('Please give action call')
