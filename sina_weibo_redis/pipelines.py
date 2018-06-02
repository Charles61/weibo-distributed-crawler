import re


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
