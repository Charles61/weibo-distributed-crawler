import re

from sina_weibo_redis import items


class WeiboEmojiEliminatePipeline(object):
    """
    清除所有字段中的emoji（四字节）字符
    """
    emoji_regex = re.compile(u'[\U00010000-\U0010ffff]')

    def process_item(self, item, spider):
        for key in item.keys():
            if isinstance(item[key], str):
                item[key] = WeiboEmojiEliminatePipeline.emoji_regex.sub('', item[key])
        return item

class ItemTypeSetPipeline(object):
    """
    设置item类型字段
    """
    def process_item(self, item, spider):
        if isinstance(item, items.WeiboItem):
            item['item_type'] = 1  # item类型 1为微博
        elif isinstance(item, items.CommentItem):
            item['item_type'] = 2  # item类型 2为评论
        return item
