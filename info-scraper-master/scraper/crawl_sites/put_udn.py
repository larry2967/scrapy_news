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
            "media": "udn",
            "name": "udn",
            "scrapy_key": "udn:start_urls",
            "enabled": True,
            "url": "https://udn.com/api/more?page=1&id=&channelId=1&cate_id=1&type=breaknews&totalRecNo=287",
            "priority": 1,
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
        },
        {
            "media": "udn",
            "name": "udn_keywords",
            "scrapy_key": "udn_keywords:start_urls",
            "enabled": True,
            "url": "https://udn.com/",
            "url_pattern":"https://udn.com/api/more?page=1&id=search:{}&channelId=2&type=searchword",
            "keywords_list":['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅'],
            "priority": 1,
            "interval": 3600,
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
    media = 'udn'
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('-a')
    args = my_parser.parse_args()
    if 'run' == args.a:
        save_to_redis()
    elif 'save' == args.a:
        save_to_mongo(media)
    else:
        print('Please give action call')


