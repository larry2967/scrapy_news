# info-scraper
## 架構簡述
以Scrapy-Redis當作主架構來做分散式爬取，將要爬取的網站url存到redis，讓每個子爬蟲到redis中領取url進行任務。

## 爬取網站
- 聯合新聞網_要聞
- 中時電子報_社會
- 自由時報_社會
- Ettoday新聞雲_社會
- 蘋果日報_社會

## 啟動爬蟲service
（測試時，建議使用scrapy.Spider）

### 1. scrapy.Spider
從spider資料夾裡的各個爬蟲的程式碼中，start_requests function來讀取start_urls

#### 啟動docker-compose：
`docker-compose -f docker-compose-dev.yaml up`

#### spider繼承物件
scrapy.Spider

#### 執行某隻特定spider
需要在 ~/info-scraper-master/scraper 資料層底下
`scrapy crawl [spider-name]`


### 2. RedisSpider
從指定的redis列表，讀取start_urls

#### 啟動docker-compose：
`docker-compose -f docker-compose.yaml up`
若有更動程式碼，皆須重新build docker image，所以測試來說，不建議使用

#### spider繼承物件
RedisSpider

#### 新增爬蟲任務config到mongodb
在 /crawl_sites 資料夾裡，有各個網站的config，可透過執行.py檔，將config塞到mongodb
mongodb: `python3 crawl_sites/[檔案名稱] -a save` 

#### 將爬蟲任務config塞到redis
1.將特定網站的config塞到redis:
`python3 crawl_sites/[檔案名稱] -a run`

2.將所有網站的config從mongoDB讀取並塞到redis
`python3 manager.py` 
