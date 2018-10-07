# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request,FormRequest
import re
import time
from urllib.parse import unquote
from urllib import parse
import os, json
import base64
from Crypto.Cipher import AES
import random 
import requests
from music.items import MusicItem,MusicItemLoader

class WyySpider(scrapy.Spider):
    name = 'wyy'
    allowed_domains = ['http://music.163.com']
    start_urls = ['http://music.163.com/']
    COMMENT_COUNT_LET = 1000
    headers = {
        'Cookie': 'appver=1.5.0.75771;',
        'Referer': 'http://music.163.com/',
        'Accept-Language':"zh-CN,zh;q=0.9,en;q=0.8",
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'
    }

    first_param = "{rid:\"\", offset:\"0\", total:\"true\", limit:\"20\", csrf_token:\"\"}"
    second_param = "010001"
    forth_param = "0CoJUm6Qyw8W8jud"

    def parse(self, response):
        aList = response.css(".tit.f-thide.s-fc0::attr(href)").extract()
        for list_url in aList:
            url=parse.urljoin(response.url, list_url)
            yield Request(url,callback=self.parse_list,dont_filter=True)

    def get_params(self,first_param):
        iv = "0102030405060708"
        first_key = self.forth_param
        second_key = 16 * 'F'
        h_encText = self.AES_encrypt(self.first_param, first_key, iv)
        h_encText = self.AES_encrypt(h_encText, second_key, iv)
        return h_encText


    def get_encSecKey(self):
        encSecKey = "257348aecb5e556c066de214e531faadd1c55d814f9be95fd06d6bff9f4c7a41f831f6394d5a3fd2e3881736d94a02ca919d952872e7d0a50ebfa1769a7a62d512f5f1ca21aec60bc3819a9c3ffca5eca9a0dba6d6f7249b06f5965ecfff3695b54e1c28f3f624750ed39e7de08fc8493242e26dbc4484a01c76f739e135637c"
        return encSecKey

    def AES_encrypt(self,text, key, iv):
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        encrypt_text = encryptor.encrypt(text)
        encrypt_text = base64.b64encode(encrypt_text)
        encrypt_text = str(encrypt_text, encoding="utf-8")
        #encrypt_text = encryptor.encrypt(text)
        #encrypt_text = str(base64.b64encode(encrypt_text))[2:-1]
        return encrypt_text

    def parse_list(self,response):
        song_list = response.css("ul.f-hide li a::attr(href)").extract()
        for song_id in song_list:
            query = { 
                'rid': 'R_SO_4_{}'.format(song_id), 
                'offset': '0',
                 'total': 'true', # 第一页时为true，其他页为false 
                'limit': '20',
                'csrf_token': '' 
            }
            params = self.get_params(query)
            encSecKey = self.get_encSecKey()
            data = {
                "params": params,
                "encSecKey": encSecKey
            }
            song_obj = re.match(r".*?(\d+)",song_id,re.S)
            song_str = song_obj.group(1)
            api_url = 'weapi/v1/resource/comments/R_SO_4_' + song_str + '/?csrf_token='
            url = parse.urljoin(response.url, api_url)
            yield scrapy.FormRequest(url,headers=self.headers,meta={'song_id':song_str},formdata=data,callback=self.parse_song,dont_filter=True)

    def parse_song(self,response):
        json_dict = json.loads(response.text)
        if json_dict['total']>=1000 and len(json_dict['hotComments'])!=0:
            name_url = "https://music.163.com/song?id="+response.meta['song_id']
            name_text = requests.get(name_url,headers=self.headers).text
    
            singer_obj = re.match('.*?歌手：(.*?)。',name_text,re.S)
            ablum_obj = re.match('.*?所属专辑：(.*?)。',name_text,re.S)
            song_obj = re.match('.*?<title>(.*?)-',name_text,re.S)
            singer = singer_obj.group(1)
            ablum = ablum_obj.group(1)
            song_name = song_obj.group(1)
            print (json_dict['total'])
            for item in json_dict['hotComments']:
                music_item = MusicItem()
                item_loader = MusicItemLoader(item=MusicItem(), response=response)
                item_loader.add_value("comment_id",item["commentId"])
                item_loader.add_value("comment_date", item['time'])
                item_loader.add_value("singer", singer)
                item_loader.add_value("ablum",ablum)
                item_loader.add_value("song_name", song_name)
                item_loader.add_value("liked_count", item['likedCount'])
                item_loader.add_value("user_avatar_url", item['user']['avatarUrl'])
                item_loader.add_value("user_nickname",item['user']['nickname'])
                item_loader.add_value("comment",item['content'])
                item_loader.add_value("song_id",response.meta["song_id"])
                # discuss = []
                # if len(item['beReplied'])!=0:
                #     for comment in item['beReplied']:
                #         data = {
                #             "comment":comment['content'],
                #             "user_avatar_url":comment['user']['avatarUrl'],
                #             "user_nickname":comment['user']['nickname']
                #         }
                #         discuss.append(data)
                # item_loader.add_value("discuss",discuss)
                music_item = item_loader.load_item()
                yield music_item
                #print(item['content'].encode('gbk', 'ignore'))

        
    def start_requests(self):
        pageMax = 42
        for i in range(1, pageMax + 1):
            url = 'http://music.163.com/discover/playlist/?order=hot&cat=全部&limit=35&offset=' + str(i * 35)
            yield Request(url,callback=self.parse)