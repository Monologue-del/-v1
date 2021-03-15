# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import sys

import scrapy
import datetime
from zhihu.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT
from zhihu.util.common import extract_num
from scrapy.loader.processors import TakeFirst # 只取取出的第一个值
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join # 列表连接


class ZhihuItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass



class ZhihuQuestionItem(scrapy.Item):
    """
    知乎问题Item
    """
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()


class ZhihuAnswerItem(scrapy.Item):
    """
    知乎问题回答item
    """
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    crawl_time = scrapy.Field()
    update_time = scrapy.Field()
