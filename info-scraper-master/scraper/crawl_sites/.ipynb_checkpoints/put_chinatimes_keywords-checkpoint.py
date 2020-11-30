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
    requests=[]
    # 關鍵字
#     keywords_list=['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅']
    keywords_list=['川普']
    for keyword in keywords_list:
        url="https://www.chinatimes.com/search/{}?page=1&chdtv".format(keyword)
        requests.append(item)

    for req in requests:
        yield {
            "media": "chinatimes",
            "name": "chinatimes",
            "enabled": True,
            "days_limit": 3600 * 24 * 2,
            "interval": 3600 * 2,
            "url": req,
            "scrapy_key": "chinatimes:start_urls",
            "priority": 1
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
    media = 'chinatimes'
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('-a')
    args = my_parser.parse_args()
    if 'run' == args.a:
        save_to_redis(media)
    elif 'save' == args.a:
        save_to_mongo(media)
    else:
        print('Please give action call')
