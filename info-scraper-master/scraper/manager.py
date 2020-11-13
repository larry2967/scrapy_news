#!/usr/bin/python3
import redis
import pymongo
import ujson
import yaml
from scutils.redis_queue import Base, RedisQueue, RedisPriorityQueue, RedisStack

# get settings from docker-compose.yaml
with open('../docker-compose.yaml', 'r') as stream:
    config = yaml.safe_load(stream)
SETTINGS = config['services']['mycrawler']['environment']

# mongo connection
# connection = pymongo.MongoClient(SETTINGS['MONGODB_SERVER'], SETTINGS['MONGODB_PORT'])
connection = pymongo.MongoClient('mongodb://%s:%s@%s'%(SETTINGS['MONGODB_USER'],SETTINGS['MONGODB_PASSWORD'],'localhost'))
db = connection['config']
collection = db['urls']
docs = collection.find({'enabled': True})

# redis connection
password = SETTINGS['REDIS_PASSWORD']
r = redis.StrictRedis(password=password)

for doc in docs:
    # Command crawler by scrapy
    scrapy_key = doc.get('scrapy_key')
    if scrapy_key:
        print('doc:',doc)
        interval = doc.get('interval', 0)
        priority = doc.get('priority', 0)
        doc['_id'] = str(doc['_id'])
        
        q = RedisPriorityQueue(r, scrapy_key, encoding=ujson)
        q.push(doc, doc['priority'])