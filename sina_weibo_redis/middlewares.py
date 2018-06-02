# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import random

import sina_weibo_redis
from sina_weibo_redis.login.login_with_selenium import LoginWithSelenium


class AgentsDownloaderMiddleware(object):
    """
    随机选择agents,有随机和轮流两种模式
    """

    def __init__(self, agents, is_random):
        self.agents = agents
        self.is_random = is_random
        self.index = 0

    @classmethod
    def from_crawler(cls, crawler):
        agents = crawler.settings['AGENTS']
        is_random = crawler.settings['AGENTS_RANDOM_CHOOSE']
        s = cls(agents, is_random)
        return s

    def process_request(self, request, spider):
        agent = random.choice(self.agents)
        if self.is_random:
            agent = random.choice(self.agents)
        else:
            agent = self.agents[self.index % len(self.agents)]
            self.index = self.index + 1
        request.headers["User-Agent"] = agent
        return None


class CookiesDownloaderMiddleware(object):
    """
    设置登录的cookies，有随机和轮流两种模式
    """

    def __init__(self, cookies_list, is_random):
        self.cookies_list = cookies_list
        self.is_random = is_random
        self.index = 0

    @classmethod
    def from_crawler(cls, crawler):
        accounts = crawler.settings['ACCOUNTS']
        is_random = crawler.settings['ACCOUNTS_RANDOM_CHOOSE']
        chrome_driver_path = crawler.settings['CHROME_DRIVER_PATH']
        login_with_selenium = LoginWithSelenium(chrome_driver_path)
        cookies_list = sina_weibo_redis.login.login_with_selenium.get_cookies_list(login_with_selenium, accounts)
        s = cls(cookies_list, is_random)
        return s

    def process_request(self, request, spider):
        cookies = {}
        if self.is_random:
            cookies = random.choice(self.cookies_list)
        else:
            cookies = self.cookies_list[self.index % len(self.cookies_list)]
            self.index = self.index + 1
        # 设置cookies并且设置对应的账号到meta
        request.cookies = cookies['cookies']
        request.meta['account'] = cookies['act']
        return None
