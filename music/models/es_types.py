from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, analyzer, Completion, Keyword, Text, Integer,InnerObjectWrapper
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

from elasticsearch_dsl.connections import connections
connections.create_connection(hosts=["localhost"])

class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])

class DiscussType(InnerObjectWrapper):
    comment = Text(analyzer="ik_max_word")
    user_avatar_url = Keyword()
    user_nickname = Keyword()

class CommentType(DocType):
    #伯乐在线文章类型
    suggest = Completion(analyzer=ik_analyzer)

    comment_date = Date()
    singer = Text(analyzer="ik_max_word")
    ablum = Text(analyzer="ik_max_word")
    song_name = Text(analyzer="ik_max_word")
    liked_count = Keyword()
    user_avatar_url = Keyword()
    user_nickname = Keyword()
    comment = Text(analyzer="ik_max_word")
    song_id = Keyword()

    # discuss = Nested(DiscussType)

    class Meta:
        index = "music"
        doc_type = "comments"

if __name__ == "__main__":
    CommentType.init()