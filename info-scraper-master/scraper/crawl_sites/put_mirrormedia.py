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
            "media": "mirrormedia",
            "name": "mirrormedia",
            "enabled": True,
            "days_limit": 3600 * 24 * 2,
            "interval": 3600,
            "url": "https://www.mirrormedia.mg/api/getlist?max_results=12&sort=-publishedDate&where=%7B%22categories%22%3A%7B%22%24in%22%3A%5B%225979ac33e531830d00e330a9%22%5D%7D%7D&page=1",
            "scrapy_key": "mirrormedia:start_urls",
            "priority": 1
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
    media = 'mirrormedia'
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('-a')
    args = my_parser.parse_args()
    if 'run' == args.a:
        save_to_redis()
    elif 'save' == args.a:
        save_to_mongo(media)
    else:
        print('Please give action call')
