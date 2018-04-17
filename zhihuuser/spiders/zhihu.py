# -*- coding: utf-8 -*-
from scrapy import Spider,Request
import json
from zhihuuser.items import UserItem
import scrapy

class ZhihuSpider(Spider):
    name = 'zhihu'#爬虫名
    allowed_domains = ['www.zhihu.com']#允许爬虫的url
    start_urls = ['http://www.zhihu.com/']#初始URL
    start_user = "cao-jiang-50"#选定开始的大V
    user_url = "https://www.zhihu.com/api/v4/members/{user}?include={include}" #个人信息
    #用来请求个人信息
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'

    follows_url = "https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}"#大V关注列表
    follows_query = "data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics"

    followees_url ='https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}' #大V的粉丝
    followees_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
    def start_requests(self):
        '''
        这里重写了start_requests方法，分别请求了用户查询的url和关注列表的查询以及粉丝列表信息查询
        :return:
        '''
        yield Request(self.user_url.format(user=self.start_user,include=self.user_query),callback=self.parse_user)#获取本身信息
        yield Request(self.follows_url.format(user=self.start_user,include=self.follows_query,offset=0,limit=20),callback=self.parse_follows)#获取关注列表
        yield Request(self.followees_url.format(user=self.start_user,include=self.followees_query,offset=0,limit=20),callback=self.parse_follows)#获粉丝注列表


    def parse_user(self, response):#处理获得个人信息 关注和粉丝列表
        #因为返回的是json格式的数据，所以这里直接通过json.loads获取结果
        result = json.loads(response.text)#获得的信息json解析
        item = UserItem()#初始化item
        #这里循环判断获取的字段是否在自己定义的字段中，然后进行赋值 filds=自己定义的变量
        for field in item.fields:
            if field in result.keys():#自己定义的和json里的一样
                item[field] = result.get(field)#赋值
        yield item
        #获取粉丝的粉丝列表，关注者的关注列表
        yield Request(self.follows_url.format(user = result.get("url_token"),include=self.follows_query,offset=0,limit=20),callback=self.parse_follows)
        yield Request(self.followees_url.format(user = result.get("url_token"),include=self.followees_query,offset=0,limit=20),callback=self.parse_followees)


    def parse_follows(self, response):
        '''
        用户关注列表的解析，这里返回的也是json数据 这里有两个字段data和page，其中page是分页信息
        :param response:
        :return:
        '''

        results = json.loads(response.text)
        if 'data' in results.keys():

            for result in results.get('data'):

                yield Request(self.user_url.format(user=result.get("url_token"),include=self.user_query),callback=self.parse_user)

        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:

            next_page = results.get('paging').get('next')
            #获取下一页的地址然后通过yield继续返回Request请求，继续请求自己再次获取下页中的信息
            yield Request(next_page,self.parse_follows)

    def parse_followees(self, response):#粉丝
        '''
        这里其实和关乎列表的处理方法是一样的
        用户粉丝列表的解析，这里返回的也是json数据 这里有两个字段data和page，其中page是分页信息
        :param response:
        :return:
        '''
        results = json.loads(response.text)

        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user = result.get("url_token"),include=self.user_query),callback=self.parse_user)

        #这里判断page是否存在并且判断page里的参数is_end判断是否为False，如果为False表示不是最后一页，否则则是最后一页
        if 'paging' in results.keys() and results.get('is_end') == False:
            next_page = results.get('paging').get("next")
            #获取下一页的地址然后通过yield继续返回Request请求，继续请求自己再次获取下页中的信息
            yield Request(next_page,self.parse_followees)
