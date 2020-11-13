from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
'''
使用 CrawlerProcess 來達成同一個process運行多個spider
get_project_settings() 方法會取得爬蟲專案中的 settings.py 檔案設定
啟動爬蟲前要提供這些設定給 Scrapy Engine
p.s. 另一個進階選擇：CrawlerRunner 
'''
setting = get_project_settings()
process = CrawlerProcess(setting)

for spider_name in process.spider_loader.list():
    print ("Running spider %s" % (spider_name))
    process.crawl(spider_name)

process.start()