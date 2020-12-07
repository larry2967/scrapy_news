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
  
    search_day=[]
    now=datetime.datetime.now()
    today=now.strftime("%Y%m%d")
    search_day.append(today)
    day_before=2    
    for i in range(1,day_before+1):
        time_delta=datetime.timedelta(days=i) 
        day_before=(now-time_delta).strftime("%Y%m%d")
        search_day.append(day_before)
    
    for url in urls:
        yield {
            "url": url,
            "url_pattern":"https://www.mirrormedia.mg/story/{}soc{}/",
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
            "media": "mirrormedia",
            "name": "mirrormedia_keywords",
            "scrapy_key": "mirrormedia:start_urls",
            "day":search_day,
            "priority": 1,
            "search": False,
            "enabled": True,
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
