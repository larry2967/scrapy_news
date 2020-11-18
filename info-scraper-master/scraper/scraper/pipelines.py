# -*- coding: utf-8 -*-
from scrapy.utils.project import get_project_settings
from dateutil.parser import parse as parse_time
from elasticsearch import Elasticsearch
import mysql.connector
from mysql.connector import errorcode
import pymongo
import psycopg2
import hashlib
import pytz
import datetime
import logging
import json
import yaml

# get settings from docker-compose-dev.yaml
with open('../docker-compose-dev.yaml', 'r') as stream:
    config = yaml.safe_load(stream)
MONGO_SETTINGS = config['services']['mongo']['environment']
MONGO_USERNAME = MONGO_SETTINGS[0].split('=')[-1]
MONGO_PASSWORD = MONGO_SETTINGS[1].split('=')[-1]

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

SETTINGS = get_project_settings()

logger = logging.getLogger(__name__)

class SaveToMongoPipeline:

    ''' pipeline that save data to mongodb '''
    def __init__(self):
        connection = pymongo.MongoClient('mongodb://%s:%s@localhost'%(MONGO_USERNAME,MONGO_PASSWORD))
        self.db = connection[SETTINGS['MONGODB_DB']]
        self.collection = self.db[SETTINGS['MONGODB_DATA_COLLECTION']]


    def process_item(self, item, spider):
        data = self.collection.find_one({'url': item['doc_url']})
        if data is None:
            res = self.collection.insert_one(dict(item))
            _id = res.inserted_id
        else:
            _id = data['_id']
        item['proto_id'] = str(_id)
        return item


class SaveToSqlDBPipeline:
    ''' pipeline that save data to SqlDB '''
    def __init__(self):
        self.connection = self.get_conn()
        self.columns = ['raw_id', 'create_date', 'post_date', 'media', 'category', 
                        'author', 'title', 'content', 'doc_url', 'image_url']
        self.table_name = SETTINGS['SQLDB_DATA_TABLE']
    
    def get_conn(self):
        conn = psycopg2.connect(user=SETTINGS['SQLDB_USERNAME'],
                            password=SETTINGS['SQLDB_PASSWORD'],
                            host=SETTINGS['SQLDB_SERVER'],
                            port=SETTINGS['SQLDB_PORT'],
                            database=SETTINGS['SQLDB_DB'])
        return conn

    def process_item(self, item, spider):
        # check db is connected or not
        try:
            cur = self.connection.cursor()
            cur.execute('SELECT 1')
            cur.close()
        except:
            self.connection = self.get_conn()

        raw_id = item['raw_id']
        self.cur = self.connection.cursor()
        query = f"select * from {self.table_name} where raw_id='{raw_id}';"
        self.cur.execute(query)
        data_len = self.cur.rowcount
        
        if data_len ==0:
            columns_str = ','.join(self.columns)
            placeholders_str = ','.join(['%s'] * len(self.columns))
            sql_insert = f'INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders_str})'
            records = (item['raw_id'], item['create_date'], item['post_date'], item['media'],\
                        item['category'], item['author'], item['title'], item['content'],\
                        item['doc_url'], item['image_url'])
            self.cur.execute(sql_insert, records)

        else:
            update_columns = list(filter(lambda x: x!='create_date',self.columns))
            columns_str = ','.join(map(lambda x: x + '=(%s)', update_columns))
            sql_update = f"UPDATE {self.table_name} SET {columns_str} WHERE raw_id='{raw_id}'"
            records = (item['raw_id'], item['post_date'], item['media'], item['category'],\
                        item['author'], item['title'], item['content'], item['doc_url'],\
                        item['image_url'])
            self.cur.execute(sql_update, records)

        self.connection.commit()
        self.cur.close()
        return item


class SaveToElasticsearchPipeline:

    def __init__(self):
        es_timeout = SETTINGS['ELASTICSEARCH_TIMEOUT']
        es_servers = SETTINGS['ELASTICSEARCH_SERVERS']
        es_servers = es_servers if isinstance(es_servers, list) else [es_servers]
        es_settings = dict()
        es_settings['hosts'] = es_servers
        es_settings['timeout'] = es_timeout
        if SETTINGS['ELASTICSEARCH_USERNAME'] and SETTINGS['ELASTICSEARCH_PASSWORD']:
            es_settings['http_auth'] = (SETTINGS['ELASTICSEARCH_USERNAME'], SETTINGS['ELASTICSEARCH_PASSWORD'])
        self.index = SETTINGS['ELASTICSEARCH_INDEX']
        self.type = SETTINGS['ELASTICSEARCH_TYPE']
        self.es = Elasticsearch(**es_settings)

    def upsert(self, _id, data):
        doc = dict({
            'doc_as_upsert': True,
            'doc': data
        })
        return self.es.update(
            index=self.index, doc_type=self.type, id=_id, body=doc)

    def process_item(self, item, spider):
        print('-' * 100)
        print('-' * 100)
        print('-' * 100)
        print('save to ES')
        print('-' * 100)
        print('-' * 100)
        print('-' * 100)
        _id = item['raw_id']
        self.upsert(_id, item)
        return item


class TransformDataPipeline:

    def __init__(self):
        self.media_dict = {
            'udn' : '聯合新聞網',
            'chinatimes' : '中時電子報',
            'ltn' : '自由時報',
            'ettoday' : 'ETtoday新聞雲',
            'appledaily' : '蘋果日報',
        }

    def transfer_number(self, data):
        if type(data) == str:
            if not data.isdigit():
                data = '0'
            data = int(data)
        return data

    def hash_code(self, data):
        str_data = json.dumps({
          'date': data['date'],
          'url': data['url'],
          'title': data['article_title']
        }, sort_keys=True, indent=2)
        return hashlib.md5(str_data.encode("utf-8")).hexdigest()

    def process_item(self, item, spider):
        # comment_body = []
    
        docurl = item.get('url', '')
        time = item.get('date', '')
        tw = pytz.timezone('Asia/Taipei')
        create_date = datetime.datetime.strftime(datetime.datetime.now(tw), '%Y-%m-%dT%H:%M:%S')
    
        metadata = item.get('metadata', {})
        fb_like_count = self.transfer_number(metadata.get('fb_like_count', ''))
        fb_share_count = self.transfer_number(metadata.get('fb_share_count', ''))
        line_share_count = self.transfer_number(metadata.get('line_share_count', ''))
        like_count = self.transfer_number(metadata.get('like_count', ''))
        share_count = self.transfer_number(metadata.get('fb_like_count', ''))
        reply_count = self.transfer_number(metadata.get('reply_count', ''))
        thanks_count = self.transfer_number(metadata.get('thanks_count', ''))
        agree_count = self.transfer_number(metadata.get('agree_count', ''))
        disagree_count = self.transfer_number(metadata.get('disagree_count', ''))
        view_count = self.transfer_number(metadata.get('view_count', ''))

        category = metadata.get('category','')
        news_source = metadata.get('news_source','')
        image_url = metadata.get('image_url','')

        all_comments = item.get('comment', [])
        if reply_count == 0:
            reply_count = len(all_comments)

        if view_count != 0:
            brocount = view_count
        else:
            brocount = fb_like_count + fb_share_count + line_share_count + like_count +  \
                    share_count + reply_count + thanks_count + agree_count + disagree_count
    
        raw_media = item.get('media', '')
        media = self.media_dict.get(raw_media, raw_media)

        datafrom = 0 # datafrom: type of website. (e.g. datafrom=0:news datafrom=2:forum)

        if time is None:
            time = ''
    
        if isinstance(time, str) and time != '':
            time_obj = parse_time(time, ignoretz=True)
            timestamp = time_obj.timestamp()
            post_date = datetime.datetime.fromtimestamp(timestamp)
            post_date = datetime.datetime.strftime(post_date, '%Y-%m-%dT%H:%M:%S')
        elif isinstance(time, datetime.datetime):
            post_date = datetime.datetime.strftime(time, '%Y-%m-%dT%H:%M:%S')
        else:
            post_date = create_date
    
        raw_id = self.hash_code(item)
        return dict({
            "raw_id": raw_id,
            "author": item.get('author', ''),
            "author_url": item.get('author_url', ''),
            "create_date": create_date,
            # "docid": raw_id,
            # "MainID": raw_id,
            "category": category,
            "news_source": news_source,
            "content": item['content'],
            "media": media,
            "spider_name": item.get("media", ''),
            # "SourceType": 0,
            "doc_url": docurl,
            "post_date": post_date,
            "content_type": item['content_type'], #0:main 1:comment
            # "candidate": '',
            # "mediatype": datafrom,
            # "data_from": datafrom, #0:news 1:forum 2:...
            "title": item.get('article_title', ''),
            "browse_count": brocount,
            "reply_count": int(reply_count),
            "image_url": image_url,
            # "datatype": 0,
            # "posscore": 0,
            # "negscore": 0,
            # "evaluation": -1,
            # "candidates": []
        })