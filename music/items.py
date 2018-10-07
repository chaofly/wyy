# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from .models.es_types import CommentType,DiscussType
from elasticsearch_dsl.connections import connections
es = connections.create_connection(CommentType._doc_type.using)

def gen_suggests(index, info_tuple):
    #根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            #调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, params={'filter':["lowercase"]}, body={'text':text,'analyzer':"ik_max_word"})
            anylyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"])>1])
            new_words = anylyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({"input":list(new_words), "weight":weight})

    return suggests

class MusicItemLoader(ItemLoader):
    #自定义itemloader
    default_output_processor = TakeFirst()

class MusicItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    comment_date = scrapy.Field()
    singer = scrapy.Field()
    ablum = scrapy.Field()
    song_name = scrapy.Field()
    liked_count = scrapy.Field()
    user_avatar_url =scrapy.Field()
    user_nickname = scrapy.Field()
    comment = scrapy.Field()
    song_id = scrapy.Field()
    comment_id = scrapy.Field()
    #discuss = scrapy.Field()

    def save_to_es(self):
        comment_item = CommentType()
        comment_item.comment_date = self['comment_date']
        comment_item.singer = self["singer"]
        comment_item.ablum = self["ablum"]
        comment_item.comment = self["comment"]
        comment_item.liked_count = self["liked_count"]
        comment_item.song_name = self["song_name"]
        comment_item.user_avatar_url = self["user_avatar_url"]
        comment_item.user_nickname = self["user_nickname"]
        comment_item.meta.id = self["comment_id"]
        comment_item.song_id = self["song_id"]
        # if self["discuss"]:
        #     for i in self["discuss"]:
        #         comment_item.discuss.append(i)


       # article.suggest = gen_suggests(ArticleType._doc_type.index, ((article.title,10),(article.tags, 7)))
        comment_item.suggest = gen_suggests(CommentType._doc_type.index, ((comment_item.singer,5),(comment_item.song_name, 3),(comment_item.comment,10)))
        comment_item.save()

        #redis_cli.incr("jobbole_count")

        return