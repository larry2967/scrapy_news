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
            "media": "ltn",
            "name": "ltn",
            "scrapy_key": "ltn:start_urls",
            "url": "https://tw.yahoo.com/?p=us",
            "priority": 1,
            "search": False,
            "enabled": True,
            "url_pattern": "https://news.ltn.com.tw/ajax/breakingnews/society/{}",
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
        },
        {
            "media": "ltn",
            "name": "ltn",
            "scrapy_key": "ltn:start_urls",
            "url": "https://tw.yahoo.com/?p=us",
            "priority": 1,
            "search": False,
            "enabled": True,
            "url_pattern": "https://news.ltn.com.tw/ajax/breakingnews/politics/{}",
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
        },
        {
            "media": "ltn",
            "name": "ltn_keywords",
            "scrapy_key": "ltn_keywords:start_urls",
            "url": "https://tw.yahoo.com/?p=us",
            "url_pattern":"https://search.ltn.com.tw/list?keyword={}&type=all&sort=date&start_time={}&end_time={}&sort=date&type=all&page=1",
            "keywords_list": ['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅'],
            "priority": 1,
            "enabled": True, 
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
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
