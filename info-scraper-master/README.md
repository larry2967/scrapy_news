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
`docker-compose -f docker-compose.yaml up`

## 將爬蟲任務config塞到redis
`python3 manager.py` <br>
可以透過task.sh來結合crontab定時啟動manager.py

## 新增爬蟲任務config到mongodb
在 /crawl_sites 資料夾裡，有各個網站的config，可透過執行.py檔，將config塞到mongodb或是redis

mongodb: `python3 crawl_sites/[檔案名稱] -a save` <br>
redis: `python3 crawl_sites/[檔案名稱] -a run`

