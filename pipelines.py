# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import datetime
from openpyxl import Workbook

from itemadapter import ItemAdapter
from zhihu.items import ZhihuQuestionItem
from zhihu.items import ZhihuAnswerItem
from zhihu.util.common import extract_num
from zhihu.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT


class ZhihuPipeline:
    def open_spider(self, spider):
        self.wb_question = Workbook()
        self.ws_question = self.wb_question.active
        self.ws_question.append(
            ['zhihu_id', 'topics', 'url', 'title', 'content', 'answer_num', 'comments_num', 'watch_user_num',
             'click_num', 'crawl_time'])

        self.wb_answer = Workbook()
        self.ws_answer = self.wb_answer.active
        self.ws_answer.append(
            ['zhihu_id', 'url', 'question_id', 'author_id', 'content', 'praise_num', 'comments_num', 'create_time',
             'update_time', 'crawl_time'])

    def process_item(self, item, spider):
        if isinstance(item, ZhihuQuestionItem):
            zhihu_id = item['zhihu_id'][0]
            topics = ','.join(item['topics'])
            url = item['url'][0]
            title = item['title'][0]
            try:
                content = ''.join(item['content'])
            except:
                content = ''
            answer_num = item['answer_num'][0]
            comments_num = extract_num(item['comments_num'][0])
            crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

            if len(item["watch_user_num"]) == 2:
                watch_user_num = int(item["watch_user_num"][0].replace(',', ''))
                click_num = int(item["watch_user_num"][1].replace(',', ''))
            else:
                watch_user_num = int(item["watch_user_num"][0].replace(',', ''))
                click_num = 0

            line = [zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num, click_num,
                    crawl_time]
            self.ws_question.append(line)
            self.wb_question.save('questions.xlsx')
            return item

        elif isinstance(item, ZhihuAnswerItem):
            zhihu_id = item["zhihu_id"]
            url = item["url"]
            question_id = item["question_id"]
            author_id = item["author_id"]
            content = item["content"]
            praise_num = item["praise_num"]
            comments_num = item["comments_num"]
            create_time = datetime.datetime.fromtimestamp(item["create_time"]).strftime(SQL_DATETIME_FORMAT)
            update_time = datetime.datetime.fromtimestamp(item["update_time"]).strftime(SQL_DATETIME_FORMAT)
            crawl_time = item["crawl_time"].strftime(SQL_DATETIME_FORMAT)
            line = [zhihu_id, url, question_id, author_id, content, praise_num, comments_num, create_time, update_time,
                    crawl_time]
            self.ws_answer.append(line)
            self.wb_answer.save('answers.xlsx')

