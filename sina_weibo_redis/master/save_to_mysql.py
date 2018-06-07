#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : save_to_mysql.py
# @Author: Xu
# @Date  : 2018/6/2
# @Desc  : 将master中redis的items存入mysql数据库
import json
import logging

import mysql.connector
import redis

MYSQL_HOST = '192.168.1.88'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = '111111'
MYSQL_DATABASE = 'weibo'

REDIS_HOST = '192.168.1.88'
REDIS_PORT = 6379
REDIS_DB = 0

logger = logging.getLogger(__name__)
logger.setLevel('ERROR')


def main():
    conn = mysql.connector.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
                                   database=MYSQL_DATABASE)
    rediscli = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    while True:
        try:
            key, data = rediscli.blpop('weibo:items')
            item = json.loads(data)

            cursor = conn.cursor()

            if item['item_type'] == 1:  # item_type=1是微博
                cursor.execute(
                    'insert into weibo('
                    'user_nick_name,user_home_url,content,post_time,forwarded_count,comment_count,'
                    'like_count,weibo_url,weibo_mid)'
                    ' values (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    [item['user_nick_name'], item['user_home_url'], item['content'], item['time'],
                     item['forwarded_count'], item['comment_count'], item['like_count'], item['weibo_url'], item['weibo_mid']])
            elif item['item_type'] == 2:  # item_type=1是评论
                cursor.execute(
                    'insert into comment(weibo_mid,user_nick_name,user_home_url,content,time,like_count,comment_id)'
                    ' values (%s,%s,%s,%s,%s,%s,%s)',
                    [item['weibo_mid'], item['user_nick_name'], item['user_home_url'], item['content'],
                     item['time'], item['like_count'], item['comment_id']])
            conn.commit()
            cursor.close()
        except BaseException as e:
            logger.error('保存item失败，错误原因：%s，内容：%s', e, item)
            conn.rollback()


if __name__ == '__main__':
    main()
