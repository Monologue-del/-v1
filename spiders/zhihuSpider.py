# -*- coding: utf-8 -*-
import re
import os
import json
import datetime
import time
from zhihu.items import ZhihuQuestionItem
from zhihu.items import ZhihuAnswerItem

try:  # 为兼容py2和py3，在try中导入
    from urllib import parse  # py3
except:
    import urlparse as parse  # py2

import scrapy
from scrapy.loader import ItemLoader


# from items import ZhihuQuestionItem, ZhihuAnswerItem


class ZhihuSpider(scrapy.Spider):
    name = "zhihuSpider"
    allowed_domains = ["www.zhihu.com"]
    start_urls = [
        'https://www.zhihu.com/api/v3/feed/topstory/recommend?session_token=bc86575b6393e3ab19c3223335becf89&desktop=true&limit=7&action=down&after_id=0']

    # question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/306434148/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cattachment%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Cis_labeled%2Cpaid_info%2Cpaid_info_content%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_recognized%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B*%5D.topics%3Bdata%5B*%5D.settings.table_of_content.enabled&offset=&limit=3&sort_by=default&platform=desktop"

    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhizhu.com",
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0"
    }

    custom_settings = {
        "COOKIES_ENABLED": True
    }

    def parse(self, response):
        """
        提取出html页面中的所有url 并跟踪这些url进行一步爬取
        如果提取的url中格式为 /question/xxx 就下载之后直接进入解析函数
        """
        question_json = json.loads(response.text)

        for question in question_json['data']:
            try:
                question_id = question['target']['question']['id']  # 有时候出现广告，会出现异常
            except:
                continue
            question_url = 'https://www.zhihu.com/question/' + str(question_id)
            print(question_url)
            yield scrapy.Request(question_url, headers=self.headers, callback=self.parse_question)
        is_end_page = question_json['paging']['is_end']
        if not is_end_page:
            next_page_url = question_json['paging']['next']
            yield scrapy.Request(next_page_url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        """
        处理question页面， 从页面中提取出具体的question item
        :param response:
        :return:
        """
        if "QuestionHeader-title" in response.text:
            # # 处理新版本
            # match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            # if match_obj:
            #     question_id = (match_obj.group(2))
            question_id = response.url.split('/')[-1]
            question_id = ''.join(question_id)

            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)

            item_loader.add_css("title", "h1.QuestionHeader-title::text")
            try:
                item_loader.add_xpath("content", '//div[@class="css-eew49z"]/div/div/span//text()')
            except:
                item_loader.add_value("content", '无')
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", ".List-headerText span::text")
            item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
            item_loader.add_xpath("watch_user_num",
                                  '//*[@id="root"]/div/main/div/div[1]/div[2]/div[1]/div[2]/div/div/div/button/div/strong/text()')
            item_loader.add_css("watch_user_num", ".NumberBoard-itemValue::text")
            item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0),
                             headers=self.headers, callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        """
        处理问题回答
        :param reponse:
        :return:
        """
        # 处理question的answer
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):
        cookie = {
            '_zap': 'e19a3419-6fdd-4522-8e3c-5afad4aab04a',
            ' d_c0': '"AHDiT8OVkBCPTsOvxZyMXAL6I9aNRsucojU=|1577360842"',
            ' __utmv': '51854390.100--|2=registration_date=20170128=1^3=entry_date=20170128=1',
            ' ISSW': '1',
            ' _ga': 'GA1.2.200357884.1581345511',
            ' __utma': '51854390.200357884.1581345511.1583659553.1585060195.14',
            ' _xsrf': 'ueRkGGzczB2fBpQCECcjnLrV3OwIUv3K',
            ' Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49': '1606711701,1606714223,1606785778,1608644701',
            ' __snaker__id': 'KntFMuU6Mh9qInw7',
            ' _9755xjdesxxd_': '32',
            ' YD00517437729195%3AWM_TID': 'k2jSVLGX72NFEREAQVd7K125pxpouiNz',
            ' YD00517437729195%3AWM_NI': 'KiVb1VAHuF%2FuWphZS0up0ixUFQodzzxTE9Ssk06gj%2FifBBencWFc25cRgC97KtegvMixD4ysCm%2FSOByou%2FJVnWD4n0QRoIYWmgacBUHqLcqBHVB85LK2gjcMx0DJdRZtMWE%3D',
            ' YD00517437729195%3AWM_NIKE': '9ca17ae2e6ffcda170e2e6ee8dc95ca28ea883eb80f59a8fb7d55a869e8e84f445f3ecabb8c94d9bea8388d72af0fea7c3b92a89b79a83b45e8398bba7ae7f95b0a8bbd23cb7b0008afb5f868fa185f972bc8c8bdad279a9f0fa88e925abba8ea3e866a1898a84b13fa18ea9a4bc3d89acab88f547aba88cd5fc7981b3e1b4ce4abbb1bbd0c95eae898cd5ed3c938ea1aadc5dafb9af84c15f8caf8484f44a8c8a8ed9b84889eea98be247bcf08cabe75a9aac83b8c837e2a3',
            ' gdxidpyhxdE': 'KxST7J1Xbb0Juccb%2BYEWBpXg8qcvvHek1oPrKw0RDWMLyKyoVoWUT6%2F7ahu6X50xnjEXZdm77OD6I8bC2EIriUd2p8rnBJIGLHN%2Byx%2FaYgXQMihAuE%2F1Yj6zZHwiuEOo4d7Sqw1vMd%2Fc%5Cq4254IiHq1bIcU%2BHvch4Mq98VdfK2lVpqd6%3A1611473790861',
            ' tshl': '',
            ' q_c1': '83847eb57c5b47cd9c624e4fabaa93a7|1613901003000|1577377205000',
            ' capsion_ticket': '"2|1:0|10:1613976057|14:capsion_ticket|44:MmJlYzhlMWJlZWRlNDY4NmI0YzE1N2UyN2VjNTc5NGE=|905d50038453985f1e9b4a915eef1c2a15f1b18fd13b36c2256b027996e5db19"',
            ' r_cap_id': '"YjlmMWE5YjE0ODhjNDk2ZmI0MGMyMGIxYzg3MjBhNDQ=|1613976224|268cefe74b0c1f3820ad47068544262450454a38"',
            ' cap_id': '"NjdhNjg5M2I0NTQyNGFhZDk3M2Y2MmM2ZTRlODAwNGI=|1613976224|4b4e326e135ca822a90ad7bee141d1d09b7aeaf9"',
            ' l_cap_id': '"NDBjYjVkMTFiYmEzNDcwY2JlOWI5YmI1YzRlZDg5OGU=|1613976224|050708973c5e221753d4433928447752992bb6a0"',
            ' tst': 'r',
            ' captcha_session_v2': '"2|1:0|10:1614740506|18:captcha_session_v2|88:N3N6ZThhNGFHZE9JOGl4VDBZOS9TcjJubkExU0RoRVZ0ZVNhQi84Z0JwMlQzTHVkTW1Cb29mbkVMMHBNRzRBdQ==|ff494fc3ab1dcab53fe3a68e56afcd46e3701c57fb84dc8696b3db4aa6c2c3dc"',
            ' captcha_ticket_v2': '"2|1:0|10:1614740516|17:captcha_ticket_v2|312:eyJhcHBpZCI6IjIwMTIwMzEzMTQiLCJyZXQiOjAsInRpY2tldCI6InQwMy0yMzgtanM4bFdiOUU5NGNEcmNIM0xETl94Vm44V3hRSUVpYWtUSTRFdWo2U04tMDJYb0JCOE9ZMjJVZ3BBWGlhTUVkTTgzSHphcmI5VFNES0doRzFSTVJkS19QZ1c0SkVBbElkMUNmUFRyV2tDMUxZM2ROS2xQZEtGbEdvOTVtUGdLOWJFdWF4S1B1Nkk2dmNyMXl2ZThPZVJzZ1ZGRXdfcEdkdk10alo3USoiLCJyYW5kc3RyIjoiQElmOCJ9|c10ee00e146f49a5ec7954410f34caae19e56356f678294797c31e1f40afed60"',
            ' z_c0': '"2|1:0|10:1614740517|4:z_c0|92:Mi4xWTdxcUdBQUFBQUFBY09KUHc1V1FFQ1lBQUFCZ0FsVk5KVW9zWVFBVGlzRzZnMFJPWGJoempFeEJGVFNDVHN1LUJn|aea452393f3309795134ee391b5c7757b7b9b9162eaab41a1baf4f4d23b01358"',
            ' SESSIONID': 'ymEracPorI4ivLerm4QqoiNz9LhUukeAHexSSy7uQZy',
            ' JOID': 'V1kSC0lLqPagZCerB0Y7prkIHfEXNsO82AJA_Wc-5cTGGGzKc6qmzM1nJaICTpw30JmZhIfq9Q169G0jAflSK20=',
            ' osd': 'Wl8VAktGrvGpZiqtAE85q78PFPMaMMS12g9G-m486MLBEW7Hda2vzsBhIqsAQ5ow2ZuUgoDj9wB882QhDP9VIm8=',
            'KLBRSID': '4843ceb2c0de43091e0ff7c22eadca8c|1614743535|1614743521'
        }

        return [scrapy.Request(url=self.start_urls[0], headers=self.headers, dont_filter=True, cookies=cookie)]

    # 185的cookie
    # def start_requests(self):
    #     cookie = {'_zap': 'e19a3419-6fdd-4522-8e3c-5afad4aab04a',
    #               'd_c0': '"AHDiT8OVkBCPTsOvxZyMXAL6I9aNRsucojU=|1577360842"',
    #               '__utmv': '51854390.100--|2=registration_date=20170128=1^3=entry_date=20170128=1',
    #               ' ISSW': '1',
    #               ' _ga': 'GA1.2.200357884.1581345511',
    #               ' __utma': '51854390.200357884.1581345511.1583659553.1585060195.14',
    #               ' _xsrf': 'ueRkGGzczB2fBpQCECcjnLrV3OwIUv3K',
    #               ' Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49': '1606711701,1606714223,1606785778,1608644701',
    #               ' __snaker__id': 'KntFMuU6Mh9qInw7',
    #               ' _9755xjdesxxd_': '32',
    #               ' YD00517437729195%3AWM_TID': 'k2jSVLGX72NFEREAQVd7K125pxpouiNz',
    #               ' YD00517437729195%3AWM_NI': 'KiVb1VAHuF%2FuWphZS0up0ixUFQodzzxTE9Ssk06gj%2FifBBencWFc25cRgC97KtegvMixD4ysCm%2FSOByou%2FJVnWD4n0QRoIYWmgacBUHqLcqBHVB85LK2gjcMx0DJdRZtMWE%3D',
    #               ' YD00517437729195%3AWM_NIKE': '9ca17ae2e6ffcda170e2e6ee8dc95ca28ea883eb80f59a8fb7d55a869e8e84f445f3ecabb8c94d9bea8388d72af0fea7c3b92a89b79a83b45e8398bba7ae7f95b0a8bbd23cb7b0008afb5f868fa185f972bc8c8bdad279a9f0fa88e925abba8ea3e866a1898a84b13fa18ea9a4bc3d89acab88f547aba88cd5fc7981b3e1b4ce4abbb1bbd0c95eae898cd5ed3c938ea1aadc5dafb9af84c15f8caf8484f44a8c8a8ed9b84889eea98be247bcf08cabe75a9aac83b8c837e2a3',
    #               ' gdxidpyhxdE': 'KxST7J1Xbb0Juccb%2BYEWBpXg8qcvvHek1oPrKw0RDWMLyKyoVoWUT6%2F7ahu6X50xnjEXZdm77OD6I8bC2EIriUd2p8rnBJIGLHN%2Byx%2FaYgXQMihAuE%2F1Yj6zZHwiuEOo4d7Sqw1vMd%2Fc%5Cq4254IiHq1bIcU%2BHvch4Mq98VdfK2lVpqd6%3A1611473790861',
    #               ' tshl': '',
    #               ' q_c1': '83847eb57c5b47cd9c624e4fabaa93a7|1613901003000|1577377205000',
    #               ' capsion_ticket': '"2|1:0|10:1613976057|14:capsion_ticket|44:MmJlYzhlMWJlZWRlNDY4NmI0YzE1N2UyN2VjNTc5NGE=|905d50038453985f1e9b4a915eef1c2a15f1b18fd13b36c2256b027996e5db19"',
    #               ' r_cap_id': '"YjlmMWE5YjE0ODhjNDk2ZmI0MGMyMGIxYzg3MjBhNDQ=|1613976224|268cefe74b0c1f3820ad47068544262450454a38"',
    #               ' cap_id': '"NjdhNjg5M2I0NTQyNGFhZDk3M2Y2MmM2ZTRlODAwNGI=|1613976224|4b4e326e135ca822a90ad7bee141d1d09b7aeaf9"',
    #               ' l_cap_id': '"NDBjYjVkMTFiYmEzNDcwY2JlOWI5YmI1YzRlZDg5OGU=|1613976224|050708973c5e221753d4433928447752992bb6a0"',
    #               ' tst': 'r',
    #               ' SESSIONID': 'yXgbKHojfHkUjWUQ56OO7cP2Nf5uk5uVBG2lnUDPPak',
    #               ' JOID': 'U1wRA08qRafI1JNFbCvV8Ny9pRx7Vh3ErpreKgJJCMyZusEVPWZHmqnUlkFsxD10H8w9I0zovLl8Y5mqYQ_MyTI=',
    #               ' osd': 'UlscAEwrQqrL15JCYSjW8duwph96URDHrZvZJwFKCcuUucIUOmtEmajTm0JvxTp5HM88JEHrv7h7bpqpYAjByjE=',
    #               ' anc_cap_id': '4c93e05585a84e71b2b21eb64f1f4887',
    #               ' captcha_ticket_v2': '"2|1:0|10:1614612058|17:captcha_ticket_v2|228:eyJhcHBpZCI6IjIwMTIwMzEzMTQiLCJyZXQiOjAsInRpY2tldCI6InQwMzZKem83dmlrcC1wQV9ZYUVUcEIzY18ySFpDUk0tdkFaZUdKWGFuY3dreTlobW9mR21sQkp3Y180bVhPWFU4VVJ4dE9lSUhncEhvTWNjVGtTUGVaVEFRLXF3QWs2UWpLa1gyNUhmd3RZY2dVKiIsInJhbmRzdHIiOiJAc01GIn0=|54163f3f472a01036d5cfe894503b828d377650527e621d2540aa581cf2d1009"',
    #               ' captcha_session_v2': '"2|1:0|10:1614612059|18:captcha_session_v2|88:L2tSM0pFeWJwaHI2T0VLNVpzSy9Rd3BrVE1YQWNyLy9zWUxCQlFvN3N6czlsV1B6Ri9Zb1c2M2JBOEcyY090Qg==|78aa9ef9ea75f2ab59b02fab0b33e7ce312b8c327808add7df86cb216604ac2b"',
    #               'z_c0': '"2|1:0|10:1614612084|4:z_c0|92:Mi4xQjdBQUJBQUFBQUFBY09KUHc1V1FFQ2NBQUFDRUFsVk5kSk5rWUFCSUdMd3Y3X2hzUVlZUW9Yc1JITWRCTDQyOUdn|0bacc3038500dd9d65daaa962b7406982912425696a6bc506b06c77f432d3dc8"',
    #               'KLBRSID': '4843ceb2c0de43091e0ff7c22eadca8c|1614612086|1614606536'}
    #     return [scrapy.Request(url=self.start_urls[0], headers=self.headers, dont_filter=True, cookies=cookie)]
