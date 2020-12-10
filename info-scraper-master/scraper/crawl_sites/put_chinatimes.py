import redis
import pymongo
import ujson
import argparse
from utils import load_config
from scutils.redis_queue import Base, RedisQueue, RedisPriorityQueue, RedisStack

config = load_config()
SETTINGS = config['services']['mycrawler']['environment']

'''
save to mongo: python3 crawl_sites/put_chinatimes.py -a save
add queue to redis: python3 crawl_sites/put_chinatimes.py -a run
'''

def get_config():
    requests = [
        {
            "media": "chinatimes",
            "name": "chinatimes",
            "enabled": True,
            "days_limit": 3600 * 24 * 2,
            "interval": 3600 * 2,
            "url": "https://www.chinatimes.com/society/total?page=1&chdtv",
            "scrapy_key": "chinatimes:start_urls",
            "priority": 1
        },
        {
            "url": "https://www.chinatimes.com/",
            "url_pattern":'https://www.chinatimes.com/search/{}?page=1&chdtv',
            "keywords_list":['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅'],
            "days_limit": 3600 * 24 * 2,
            "interval": 3600 * 2,
            "media": "chinatimes",
            "name": "chinatimes_keywords",
            "enabled": True,
            "scrapy_key": "chinatimes_keywords:start_urls",
            "priority": 1}
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
    media = 'chinatimes'
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('-a')
    args = my_parser.parse_args()
    if 'run' == args.a:
        save_to_redis()
    elif 'save' == args.a:
        save_to_mongo(media)
    else:
        print('Please give action call')
