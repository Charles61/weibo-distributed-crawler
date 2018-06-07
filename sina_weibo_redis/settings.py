BOT_NAME = 'sina_weibo_redis'

SPIDER_MODULES = ['sina_weibo_redis.spiders']
NEWSPIDER_MODULE = 'sina_weibo_redis.spiders'

# LOG等级
LOG_LEVEL = 'INFO'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

COOKIES_ENABLED = True
COOKIES_DEBUG = False

DEFAULT_REQUEST_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en,zh;q=0.9,zh-CN;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36 '
}

# 指定使用scrapy-redis的调度器
SCHEDULER = "scrapy_redis.scheduler.Scheduler"

# 指定使用scrapy-redis的去重
DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'

# 指定排序爬取地址时使用的队列，
# 默认的 按优先级排序(Scrapy默认)，由sorted set实现的一种非FIFO、LIFO方式。
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.SpiderPriorityQueue'

# 在redis中保持scrapy-redis用到的各个队列，从而允许暂停和暂停后恢复，也就是不清理redis queues
SCHEDULER_PERSIST = True

# 通过配置RedisPipeline将item写入key为 spider.name : items 的redis的list中，供后面的分布式处理item
# 这个已经由 scrapy-redis 实现，不需要我们写代码
ITEM_PIPELINES = {
    # 'example.pipelines.ExamplePipeline': 300,
    'sina_weibo_redis.pipelines.WeiboEmojiEliminatePipeline': 200,
    'sina_weibo_redis.pipelines.ItemTypeSetPipeline': 201,
    'scrapy_redis.pipelines.RedisPipeline': 300
}

DOWNLOADER_MIDDLEWARES = {
    'sina_weibo_redis.middlewares.CookiesDownloaderMiddleware': 401,
    'sina_weibo_redis.middlewares.AgentsDownloaderMiddleware': 402
}

DOWNLOAD_DELAY = 0.3
RANDOMIZE_DOWNLOAD_DELAY = False

ACCOUNTS_RANDOM_CHOOSE = True
ACCOUNTS = [
    {'act': '账号', 'pwd': '密码'},
    {'act': '账号', 'pwd': '密码'}
]

# 谷歌浏览器驱动路径
CHROME_DRIVER_PATH = 'chromedriver'
# CHROME_DRIVER_PATH = 'D:\\Dev\\Tools\\chromedriver_win32\\chromedriver.exe'

AGENTS_RANDOM_CHOOSE = True
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36 ",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0",
]

# 指定redis数据库的连接参数
REDIS_HOST = '192.168.1.88'
REDIS_PORT = 6379

# 默认情况下,RFPDupeFilter只记录第一个重复请求。将DUPEFILTER_DEBUG设置为True会记录所有重复的请求。
DUPEFILTER_DEBUG = True
