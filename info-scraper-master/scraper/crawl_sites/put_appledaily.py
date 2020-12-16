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
            "media": "appledaily",
            "name": "appledaily",
            "scrapy_key": "appledaily:start_urls",
            "url_pattern": "https://tw.appledaily.com/pf/api/v3/content/fetch/query-feed?query=%7B%22feedOffset%22%3A0%2C%22feedQuery%22%3A%22taxonomy.primary_section._id%3A%5C%22%2Frealtime%2Flocal%5C%22%2BAND%2Btype%3Astory%2BAND%2Bpublish_date%3A%5Bnow-48h%2Fh%2BTO%2Bnow%5D%22%2C%22feedSize%22%3A%22100%22%2C%22sort%22%3A%22display_date%3Adesc%22%7D&d={}&_website=tw-appledaily",
            "url": "https://tw.appledaily.com/realtime/local/",
            "priority": 1,
            "enabled": True,
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2,
        },
        {
            'media': "appledaily",
            'name': "appledaily",
            "scrapy_key": "appledaily:start_urls",
            "url": "https://tw.appledaily.com/daily/headline/",
            "url_pattern": "https://tw.appledaily.com/pf/api/v3/content/fetch/query-feed?query=%7B%22feedOffset%22%3A0%2C%22feedQuery%22%3A%22taxonomy.primary_section._id%3A%5C%22%2Fdaily%2Fheadline%5C%22%2BAND%2Btype%3Astory%2BAND%2Beditor_note%3A%5C%22{}%5C%22%2BAND%2BNOT%2Btaxonomy.tags.text.raw%3A_no_show_for_web%2BAND%2BNOT%2Btaxonomy.tags.text.raw%3A_nohkad%22%2C%22feedSize%22%3A100%2C%22sort%22%3A%22location%3Aasc%22%7D&d={}&_website=tw-appledaily", #feedsize來調整一頁看多少篇
            "priority": 1,
            "enabled": True,
            "interval": 3600 * 2,
            "days_limit": 3600 * 24 * 2, 
        },
        {
            "media": "appledaily",
            "name": "appledaily_keywords",
            "scrapy_key": "appledaily_keywords:start_urls",
            "url":"https://tw.appledaily.com/daily/headline/",
            "url_pattern":"https://tw.appledaily.com/pf/api/v3/content/fetch/search-query?query=%7B%22searchTerm{}start%22%3A{}%7D&d={}&_website=tw-appledaily",
            "keywords_list": ['吸金','地下通匯','洗錢','賭博','販毒','走私','仿冒','犯罪集團','侵占','背信','內線交易','行賄','詐貸','詐欺','貪汙','逃稅'],
            "page": 0,
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
    media = 'appledaily'
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('-a')
    args = my_parser.parse_args()
    if 'run' == args.a:
        save_to_redis()
    elif 'save' == args.a:
        save_to_mongo(media)
    else:
        print('Please give action call')


