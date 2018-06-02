# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class WeiboItem(scrapy.Item):
    weibo_mid = scrapy.Field()
    user_nick_name = scrapy.Field()
    user_home_url = scrapy.Field()
    content = scrapy.Field()
    time = scrapy.Field()
    forwarded_count = scrapy.Field()
    comment_count = scrapy.Field()
    like_count = scrapy.Field()
    weibo_url = scrapy.Field()


class CommentItem(scrapy.Item):
    weibo_mid = scrapy.Field()
    comment_id = scrapy.Field()
    user_nick_name = scrapy.Field()
    user_home_url = scrapy.Field()
    content = scrapy.Field()
    time = scrapy.Field()
    like_count = scrapy.Field()
