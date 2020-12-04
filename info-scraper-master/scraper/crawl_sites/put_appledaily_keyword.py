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
        yield {{"url": url,
                "url_pattern":"https://udn.com/api/more?page=1&id=search:{}&channelId=2&type=searchword",
                "key_dict":"{'吸金':'%22%3A%22%25E5%2590%25B8%25E9%2587%2591%22%2C%22','地下通匯':'%22%3A%22%25E5%259C%25B0%25E4%25B8%258B%25E9%2580%259A%25E5%258C%25AF%22%2C%22','洗錢':'%22%3A%22%25E6%25B4%2597%25E9%258C%25A2%22%2C%22','賭博':'%22%3A%22%25E8%25B3%25AD%25E5%258D%259A%22%2C%22','販毒':'%22%3A%22%25E8%25B2%25A9%25E6%25AF%2592%22%2C%22','走私':'%22%3A%22%25E8%25B5%25B0%25E7%25A7%2581%22%2C%22','仿冒':'%22%3A%22%25E4%25BB%25BF%25E5%2586%2592%22%2C%22','犯罪集團':'%22%3A%22%25E7%258A%25AF%25E7%25BD%25AA%25E9%259B%2586%25E5%259C%2598%22%2C%22','侵占':'%22%3A%22%25E4%25BE%25B5%25E4%25BD%2594%22%2C%22','背信':'%22%3A%22%25E8%2583%258C%25E4%25BF%25A1%22%2C%22','內線交易':'%22%3A%22%25E5%2585%25A7%25E7%25B7%259A%25E4%25BA%25A4%25E6%2598%2593%22%2C%22','行賄':'%22%3A%22%25E8%25A1%258C%25E8%25B3%2584%22%2C%22','詐貸':'%22%3A%22%25E8%25A9%2590%25E8%25B2%25B8%22%2C%22','詐欺':'%22%3A%22%25E8%25A9%2590%25E6%25AC%25BA%22%2C%22','貪汙':'%22%3A%22%25E8%25B2%25AA%25E6%25B1%25A1%22%2C%22','逃稅':'%22%3A%22%25E9%2580%2583%25E7%25A8%2585%22%2C%22'}",
                "days_limit": 3600 * 24,
                "interval": 3600,
                "media": "udn",
                "name": "appledaily_keywords",
                "enabled": True,
                "scrapy_key": "appledaily_keywords:start_urls",
                "priority": 1,}
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


