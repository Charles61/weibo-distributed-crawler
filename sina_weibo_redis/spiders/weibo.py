# -*- coding: utf-8 -*-
import json
import logging
import math
import scrapy
import re
import urllib.request
import datetime

from scrapy import Selector
from sina_weibo_redis.items import WeiboItem, CommentItem
from scrapy_redis.spiders import RedisSpider

logger = logging.getLogger(__name__)


class WeiboSpider(RedisSpider):
    # 热门列表URL
    #  https://m.weibo.cn/api/container/getIndex?type=all&queryVal=锤子科技&luicode=10000011&lfid=106003type%3D1&title=锤子科技&containerid=100103type%3D60%26q%3D锤子科技%26t%3D0
    # HOT_LIST_URL_FIRST = 'https://m.weibo.cn/api/container/getIndex?type=all&queryVal=%s&luicode=10000011&lfid=106003type%%3D1&title=%s&containerid=100103type%%3D60%%26q%%3D%s%%26t%%3D0'
    # HOT_LIST_URL = 'https://m.weibo.cn/api/container/getIndex?type=all&queryVal=%s&luicode=10000011&lfid=106003type%%3D1&title=%s&containerid=100103type%%3D60%%26q%%3D%s%%26t%%3D0&page=%s'
    # 全文URL
    FULL_CONTENT_URL = 'https://weibo.com/p/aj/mblog/getlongtext?mid=%s'
    # 评论URL
    COMMENT_URL = 'https://m.weibo.cn/api/comments/show?id=%s&page=%s'

    name = 'weibo'
    redis_key = "weibospider:start_urls"

    def __init__(self, *args, **kwargs):
        self.allowed_domains = ['weibo.cn', 'weibo.com']
        super(WeiboSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        """
        判断总共有多少待爬页面，并生成返回相应数量的Request

        :param response:
        :return:
        """

        try:
            page_json = json.loads(response.body.decode('utf-8'))
            if page_json['ok'] != 1:
                logger.warning('账号：[%s]，获取搜索微博总条目数失败，返回信息：%s', response.meta['account'], page_json)
                return None
            total = page_json['data']['cardlistInfo']['total']
            page_size = int(page_json['data']['cardlistInfo']['page_size'])
            page_count = math.ceil(total / page_size)
            logger.info('账号：[%s]，发现待爬微博 %s 条，总共 %s 页，每页 %s 条', response.meta['account'], total, page_count, page_size)
            for index in range(2, page_count + 1):
                yield scrapy.Request(
                    url=response.url + '&page=' + str(index),
                    callback=self.parse_pages,
                    meta={
                        'index': index
                    }
                )
        except BaseException as e:
            logger.error('账号：[%s]，获取搜索微博总条目数失败，错误原因：%s，返回信息：%s', response.meta['account'], e, page_json)

        #  处理第一页
        response.meta['index'] = 1
        yield from self.parse_pages(response)

    def parse_pages(self, response):
        """
        对搜索页中的每条微博信息进行抽取，
        如果微博内容中有显示完全有“展开全文”按钮则继续返回一个微博全文的请求，
        否则返回item

        :param response:
        :return:
        """
        page_json = json.loads(response.body.decode('utf-8'))
        for i in page_json['data']['cards'][-1]['card_group']:

            item = WeiboItem()
            item['weibo_mid'] = int(i['mblog']['mid'])
            item['user_nick_name'] = i['mblog']['user']['screen_name']
            item['user_home_url'] = i['mblog']['user']['profile_url'].split('?')[0]

            text = i['mblog']['text']
            text_s = Selector(text=text, type='html')
            item['content'] = text_s.xpath('normalize-space(string(.))').extract_first('')

            item['time'] = self.format_date(i['mblog']['created_at'])
            item['forwarded_count'] = i['mblog']['reposts_count']
            item['comment_count'] = i['mblog']['comments_count']
            item['like_count'] = i['mblog']['attitudes_count']
            item['weibo_url'] = i['scheme'].split('?')[0]

            if len(text_s.xpath('//a[text()="全文"]')) != 0:  # 有展开全文按钮，构造全文请求，获取全文
                yield scrapy.Request(url=WeiboSpider.FULL_CONTENT_URL % item['weibo_mid'], callback=self.parse_full_content, meta={'item': item})
            else:
                yield item

            #  构造返回该微博评论request
            comment_url = WeiboSpider.COMMENT_URL % (item['weibo_mid'], 1)
            yield scrapy.Request(
                url=comment_url,
                callback=self.parse_comment,
                meta={
                    'mid': item['weibo_mid'],  # 微博mid
                    'index': 1,
                    'count': 0
                }
            )

        logger.info('成功获取第%s页的微博信息', response.meta['index'])

    def parse_full_content(self, response):
        """
        抽取展开全文的内容

        :param response:
        :return:
        """
        item = response.meta['item']
        try:
            json_full = json.loads(response.body.decode('utf-8'), encoding='utf-8')
            selector = scrapy.Selector(text=json_full['data']['html'], type='html')
            content = selector.xpath('normalize-space(string(.))').extract_first('')
            item['content'] = content
            logger.info('成功获取到微博mid：%s的全文信息', item['weibo_mid'])
        except json.JSONDecodeError:
            logger.error('返回的微博全文内容格式不正确，不是json格式，微博URL：%s，全文URL：%s，返回内容：%s', item['weibo_url'], response.url, response.body)
        return item

    def parse_comment(self, response):
        """
        抽取评论相关信息并生成下一页Request

        :param response:
        :return:
        """

        comment_json = None
        try:
            comment_json = json.loads(response.body.decode('utf-8'))
        except BaseException as e:
            logger.error('评论json转换失败错误原因：%s，返回：%s', e, response.body)
            return None
        comment_list = None
        index = response.meta['index']

        if comment_json['ok'] != 1:
            if response.meta['count'] > 0:
                logger.info('微博mid：%s 评论获取完毕，总共 %s 条', response.meta['mid'], response.meta['count'])
            return None
        else:
            comment_list = comment_json['data']['data']

        # 构造返回下一页request
        comment_url = WeiboSpider.COMMENT_URL % (response.meta['mid'], index + 1)
        yield scrapy.Request(
            url=comment_url,
            callback=self.parse_comment,
            meta={
                'mid': response.meta['mid'],
                'index': response.meta['index'] + 1,
                'count': response.meta['count'] + len(comment_list),
            }
        )

        for c in comment_list:
            item = CommentItem()
            item['weibo_mid'] = response.meta['mid']
            item['comment_id'] = c['id']
            item['user_home_url'] = c['user']['profile_url'].split('?')[0]
            item['user_nick_name'] = c['user']['screen_name']
            item['content'] = scrapy.Selector(text=c['text'], type='html').xpath('normalize-space(string(.))').extract_first('')
            # 处理时间格式
            item['time'] = self.format_date(c['created_at'])
            item['like_count'] = c['like_counts']
            yield item

    def format_date(self, datetime_str):
        """
        处理微博评论的时间字符串，转换为时间对象

        :param datetime_str:
        :return:
        """
        search = re.search('(\d{1,2})(分钟|秒|小时)(前)', datetime_str)
        if search:
            num = int(search.group(1))
            if search.group(2) == '分钟':
                timedelta = datetime.timedelta(minutes=num)
            elif search.group(2) == '分钟':
                timedelta = datetime.timedelta(seconds=num)
            else:
                timedelta = datetime.timedelta(hours=num)
            return datetime.datetime.now() - timedelta

        search = re.fullmatch('昨天 \d{1,2}:\d{1,2}', datetime_str)
        if search:
            timedelta = datetime.timedelta(days=1)
            return datetime.datetime.now() - timedelta

        datetime_str = datetime_str.replace('今天', datetime.datetime.now().strftime('%Y-%m-%d'))
        datetime_str = datetime_str.replace('刚刚', datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))

        search = re.search('(\d{1,2})月(\d{1,2})日', datetime_str)
        if search:
            day = datetime.datetime.now().strftime('%Y') + ('-%s-%s' % (search.group(1), search.group(2)))
            datetime_str = re.sub('\d{1,2}月\d{1,2}日', day, datetime_str)

        search = re.fullmatch('(\d{1,2})-(\d{1,2}) \d{1,2}:\d{1,2}', datetime_str)
        if search:
            datetime_str = datetime.datetime.now().strftime('%Y-') + datetime_str

        search = re.fullmatch('(\d{1,2})-(\d{1,2})', datetime_str)
        if search:
            datetime_str = datetime.datetime.now().strftime('%Y-') + datetime_str + ' 00:00'

        search = re.fullmatch('(\d{4})-(\d{1,2})-(\d{1,2})', datetime_str)
        if search:
            datetime_str = datetime_str + ' 00:00'

        datetime_str = re.sub('第\d+楼 *', '', datetime_str)
        formated_date = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        return formated_date
