#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : login_with_selenium.py
# @Author: Xu
# @Date  : 2018/5/28
# @Desc  : 使用Selenium+Chrome登录手机版新浪微博
import json
import random
import re
from math import sqrt

import numpy
from io import BytesIO
from time import sleep

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image

import logging

logger = logging.getLogger(__name__)


class LoginWithSelenium:

    def __init__(self, chrome_driver_path):
        self.imgs = json.load(open('sina_weibo_redis/login/imgs_data.json', 'r'))
        self.chrome_driver_path = chrome_driver_path

    def login(self, act, pwd):
        """
        登录

        :param act: 要登录的账号
        :param pwd: 密码
        :return: 登录成功后的cookies
        """

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--window-size=1200x600')
        options.add_argument('--disable-dev-shm-usage')  # overcome limited resource problems
        options.add_argument('--no-sandbox')  # Bypass OS security model
        options.add_argument('--disable-gpu')  # applicable to windows os only
        driver = webdriver.Chrome(chrome_options=options, executable_path=self.chrome_driver_path)
        driver.get(
            'https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=https%3A%2F%2Fm.weibo.cn%2F%3Fjumpfrom%3Dwapv4%26tip%3D1')
        submit = None
        try:
            submit = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'loginAction'))
            )
        except TimeoutException as e:
            logger.error('账号[%s]登录失败，原因：加载登录页面超时...', act, e)
            return None

        login_name = driver.find_element_by_id('loginName')
        login_pwd = driver.find_element_by_id('loginPassword')
        login_name.click()
        login_name.send_keys(act)
        login_pwd.click()
        login_pwd.send_keys(pwd)
        submit.click()

        try:  # 需要验证码验证
            captcha_holder = WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located((By.ID, 'patternCaptchaHolder'))
            )
            sleep(2.1)
            screen_shot = Image.open(BytesIO(driver.get_screenshot_as_png()))
            size = screen_shot.size

            left = (size[0] - 260) // 2 + 50
            upper = (size[1] - 340) // 2 + 140
            right = (size[0] - 260) // 2 + 210
            lower = (size[1] - 340) // 2 + 300
            frame = (left, upper, right, lower)  # 滑块部分
            crop_img = screen_shot.crop(frame).convert('L')
            path = self.__get_captcha_path(crop_img)
            if path is None:
                logger.error('账号[%s]登录失败，原因：未能识别出验证码', act)

            self.__draw_path(path, driver, size)

        except TimeoutException:  # 不需要验证码验证
            logger.info('账号[%s]不需要验证码', act)

        sleep(2)

        cookies_raw = driver.get_cookies()
        cookies = {}
        for c in cookies_raw:
            cookies.update({c['name']: c['value']})

        if check_cookies(cookies):
            logger.info('账号：[%s]登录成功', act)
        else:
            logger.info('账号：[%s]登录失败，check_cookies失败', act)
            cookies = None

        driver.close()
        return cookies

    def __get_captcha_path(self, img):
        """
        求出img对应的验证码路径

        :param img:
        :return: 路径元组如(1,3,4,2)，没有找到返回None
        """

        for i in self.imgs.keys():
            equal = LoginWithSelenium.__compare(self.imgs[i], img)
            if equal:
                return int(i[0]), int(i[1]), int(i[2]), int(i[3])
        return None

    @staticmethod
    def __compare(img1, img2):
        """
        比较两张图片是否相等

        :param img1: 像素矩阵
        :param img2: Image对象
        :return:
        """
        width = img2.size[0]
        height = img2.size[1]
        img2 = numpy.array(img2).tolist()
        for i in range(width):
            for j in range(height):
                if abs(img1[i][j] - img2[i][j]) > 25:
                    return False
        return True

    def __draw_path(self, path, driver, size):
        """
        画出验证码路径

        :param path: 路径元组
        :param driver: 浏览器
        :param size: 屏幕大小
        :return:
        """
        points = []
        points.append(((size[0] - 260) // 2 + 80, (size[1] - 340) // 2 + 170))
        points.append(((size[0] - 260) // 2 + 180, (size[1] - 340) // 2 + 170))
        points.append(((size[0] - 260) // 2 + 80, (size[1] - 340) // 2 + 270))
        points.append(((size[0] - 260) // 2 + 180, (size[1] - 340) // 2 + 270))

        holder = driver.find_element_by_class_name('patt-holder-body')
        # 移动到路径第一个点
        ActionChains(driver).move_to_element(holder).move_by_offset(points[path[0] - 1][0] - holder.location['x'] - int(holder.size['width'] / 2),
                                                                    points[path[0] - 1][1] - holder.location['y'] - int(
                                                                        holder.size['height'] / 2)).perform()
        #  画出路径
        driver.execute(Command.MOUSE_DOWN, {})
        self.__move(points[path[0] - 1], points[path[1] - 1], driver)
        self.__move(points[path[1] - 1], points[path[2] - 1], driver)
        self.__move(points[path[2] - 1], points[path[3] - 1], driver)
        driver.execute(Command.MOUSE_UP, {})

    def __move(self, point1, point2, driver):
        """
        从点point1移动到点point2

        :param point1:
        :param point2:
        :param driver:
        :return:
        """
        # sleep(0.05)
        distance = sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)
        if distance < 4:  # 如果两点之间距离小于4px，直接划过去
            ActionChains(driver).move_by_offset(point2[0] - point1[0], point2[1] - point1[1]).perform()
        else:
            step = random.randint(3, 5)
            x = int(step * (point2[0] - point1[0]) / distance)  # 按比例
            y = int(step * (point2[1] - point1[1]) / distance)
            ActionChains(driver).move_by_offset(x, y).perform()
            self.__move((point1[0] + x, point1[1] + y), point2, driver)


def get_cookies_list(login_with_selenium, accounts):
    """
    登录并获得cookies

    :param login_with_selenium: 登录类
    :param accounts: 账号列表
    :return: 所有成功登录账号的cookies列表
    """
    cookies_list = []
    accounts_logined = []
    accounts_failed = []
    cookies_file = None
    try:
        cookies_file = open('sina_weibo_redis/login/cookies-selenium.json', 'r')
        cookies_list = json.load(fp=cookies_file)
    except IOError as e:
        logging.info('cookies-selenium.json文件打开出错，现尝试重新登录所有账号，错误原因：%s', e)
    finally:
        if cookies_file:
            cookies_file.close()

    for a in accounts:
        has = False
        for l in cookies_list:
            if l['act'] == a['act']:
                has = True
                break
        if not has:
            accounts_failed.append(a)

    for a in cookies_list:
        if check_cookies(a['cookies']):
            accounts_logined.append(a)
            logger.info('账号：[%s]cookies有效，无需重复登录', a['act'])
        else:
            accounts_failed.append(a)

    for a in accounts_failed:
        cookies = login_with_selenium.login(a['act'], a['pwd'])
        if cookies:
            accounts_logined.append({'act': a['act'], 'pwd': a['pwd'], 'cookies': cookies})
        else:
            logging.error('账号[%s]登录失败', a['act'])

    logger.info('成功登录账号%s个，失败%s个', len(accounts_logined), len(accounts) - len(accounts_logined))
    # 将cookies写入文件下次备用
    with open('sina_weibo_redis/login/cookies-selenium.json', 'w') as f2:
        json.dump(obj=accounts_logined, fp=f2)

    return accounts_logined


def check_cookies(cookies):
    """
    检查cookies是否有效

    :param cookies:
    :return:
    """
    session = requests.session()
    session.headers[
        'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36 '
    response = session.get(url='https://m.weibo.cn/api/config', cookies=cookies)
    logined = False
    try:
        json_data = json.loads(s=response.text, encoding='utf-8')
        logined = json_data['data']['login']
    except BaseException as e:
        logger.warning('账号[%s]的cookies无效...', cookies['act'])
    session.close()
    return logined
