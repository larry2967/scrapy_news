import redis
import pymongo
import ujson
import argparse
from utils import load_config
from scutils.redis_queue import Base, RedisQueue, RedisPriorityQueue, RedisStack

config = load_config()
SETTINGS = config['services']['mycrawler']['environment']

def get_config():
    requests = [{
            'media': 'appledaily',
            'name': 'appledaily',
            'scrapy_key': 'appledaily:start_urls',
            "url_pattern": 'https://tw.appledaily.com/pf/api/v3/content/fetch/query-feed?query=%7B%22feedOffset%22%3A0%2C%22feedQuery%22%3A%22taxonomy.primary_section._id%3A%5C%22%2Frealtime%2Flocal%5C%22%2BAND%2Btype%3Astory%2BAND%2Bpublish_date%3A%5Bnow-48h%2Fh%2BTO%2Bnow%5D%22%2C%22feedSize%22%3A%22100%22%2C%22sort%22%3A%22display_date%3Adesc%22%7D&d={}&_website=tw-appledaily',
            "url": 'https://tw.appledaily.com/realtime/local/',
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
            'enabled': True,
            "priority": 1,
        },{
        'media': 'appledaily',
            'name': 'appledaily',
            'scrapy_key': 'appledaily:start_urls',
            "url_pattern": 'https://tw.appledaily.com/pf/api/v3/content/fetch/query-feed?query=%7B%22feedOffset%22%3A0%2C%22feedQuery%22%3A%22taxonomy.primary_section._id%3A%5C%22%2Frealtime%2Flocal%5C%22%2BAND%2Btype%3Astory%2BAND%2Bpublish_date%3A%5Bnow-48h%2Fh%2BTO%2Bnow%5D%22%2C%22feedSize%22%3A%22100%22%2C%22sort%22%3A%22display_date%3Adesc%22%7D&d={}&_website=tw-appledaily','url':"https://tw.appledaily.com/daily/headline/"
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
            'enabled': True,
            "priority": 1,
    }]
    for req in requests:
        yield req


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
    media = 'appledaily'
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('-a')
    args = my_parser.parse_args()
    if 'run' == args.a:
        save_to_redis(media)
    elif 'save' == args.a:
        save_to_mongo(media)
    else:
        print('Please give action call')


