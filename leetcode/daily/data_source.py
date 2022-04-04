# from utils.message_builder import image
# from datetime import datetime
from datetime import datetime
from pathlib import Path
import pkgutil
import jinja2
from sqlalchemy import true
from services.log import logger
from nonebot.adapters.onebot.v11 import MessageSegment
from typing import Optional, Tuple
from enum import Enum
import os

import json
import requests
import base64

from utils.message_builder import image 
from .._util_browser__ import get_new_page 

__plugin_version__ = 0.1
__plugin_author__ = "evlic@Github"

# 爬虫对应 URL
leetCodeCN_All_URL = "https://leetcode-cn.com/problemset/all/"
leetCodeCN_Data_URL = "https://leetcode-cn.com"

# 从模版目录中加载文件的方法
def load_file(name: str) -> str:
    return pkgutil.get_data(__name__, f"templates/{name}").decode()


# 加载 Html 模版
app = jinja2.Environment(enable_async=True)
day_tpl = app.from_string(load_file("app.html"))
app_css = load_file("app.css")
bootstrap_css = load_file("bootstrap.min.css")

# 定义多语言题目
class LanguageType(Enum):
    CN = 1
    EN = 2
    CN_MIX_EN = 3


# An algorithm Question
class AlgoQuestion:
    no: str
    title: str
    level: str
    context: str
    tags: Optional[list]

    _tag_map = {
        "gray": '<span class="label label-default">{}</span>',
        "green": '<span class="label label-success">{}</span>',
        "blue": '<span class="label label-info">{}</span>',
        "yellow": '<span class="label label-warning">{}</span>',
        "red": '<span class="label label-danger">{}</span>',
    }

    _levelMap = {"Easy": "green", "Medium": "yellow", "Hard": "red"}

    def __init__(
        self,
        no,
        title,
        level,
        context,
        tags,
        lang: LanguageType = LanguageType.CN,
    ) -> None:
        self.no = no
        self.title = title
        self.level = level
        self.context = context
        self.tags = tags
        self.Language_Type = lang
        self._rander_()

    # question 对象的 html 化
    def _rander_(self):
        # 渲染
        self.level = self._tag_map[self._levelMap[self.level]].format(self.level)
        # 渲染标签
        self.tags = " ".join("{}"
                        .format(self._tag_map["blue"].format(self.tags[idx]))
                        for idx in range(len(self.tags)))
        # for idx in range(len(self.tags)):
        #     self.tags[idx] = self._tag_map["blue"].format(self.tags[idx])

    async def _toHtml(self, tpl: jinja2.Template) -> str:
        html = await tpl.render_async(
            bootstrap_css=bootstrap_css,
            app_css=app_css,
            no=self.no,
            title=self.title,
            level=self.level,
            context=self.context,
            tags=self.tags,
            auth= __plugin_author__,
            version= __plugin_version__,
        )
        return html

    async def toImage(self, path=None):
        html = await self._toHtml(day_tpl)
        # logger.info(f"html >> /n {html}")
        try:
            # image = await 
            async with get_new_page(viewport={
                "width": 800,
                "height": 800
            }) as page:
                await page.set_content(html, timeout=0)
                await page.screenshot(full_page=True, path=path)
        except:
            raise "浏览器错误"

_url_cache = {}

async def get_leetcode_daily_question(path: Path) -> Optional[MessageSegment]:
    """
    先读取存储图片
    path: 存储路径
    """

    _data_from = "local"

    date = datetime.now().date()
    key = f"{date}"
    
    # 删除非今天的图片
    for file in os.listdir(path):
        if f"{key}.png" != file:
            file = path / file
            file.unlink()

    url = ""
    if not _url_cache.__contains__(key):
        if not do_get_daily_url(key):
            raise "获取 URL 失败"

    url = _url_cache[key]
            
    # 检查是否已经存在图片
    if not f"{date}.png" in os.listdir(path):
        _data_from = "net"
        question = do_get_leetcode_daily_question(LanguageType.CN, key)
        # 处理 question 对象生成 html >> 渲染成 html 后截图
        await question.toImage(f"{path}/{date}.png")
    
    return image(f"{date}.png", "leetcode/daily"), url, _data_from
    
def do_get_daily_url(key: str) -> Tuple[str, bool] :
    try:
        # 模拟登陆 leetCodeCN 官网的题目列表页面 >> 再请求每日一题接口
        _ = requests.get(url=leetCodeCN_All_URL)
        response = requests.post(
            leetCodeCN_Data_URL + "/graphql",
            json={
                "operationName": "questionOfToday",
                "variables": {},
                "query": "query questionOfToday { todayRecord {   question {     questionFrontendId     questionTitleSlug     __typename   }   lastSubmission {     id     __typename   }   date   userStatus   __typename }}",
            },
        )

        # 解析当天的「每日一题」接口返回数据，抓取 url
        leetCode_Daily_questionTitle_CN = (
            json.loads(response.text)
            .get("data")
            .get("todayRecord")[0]
            .get("question")
            .get("questionTitleSlug")
        )
        today_url = f"{leetCodeCN_Data_URL}/problems/{leetCode_Daily_questionTitle_CN}"
        
        do_cache(key, today_url)

        return today_url, true

    except Exception as ex:
        raise ex

def do_cache(key ,url: str):
    global _url_cache
    for k in _url_cache.keys():
        if k != key:
            _url_cache.pop(k)

    _url_cache[key] = url

# 请求 Question 数据 >> Question 对象，存有对应的数据
def do_get_leetcode_daily_question(lang: LanguageType, key: str) -> AlgoQuestion:
    try:
        today_url = ""
        if _url_cache.__contains__(key):
            today_url = _url_cache[key]
        else:
            raise "获取 url 失败"

        # 模拟登陆 leetCodeCN 官网的题目列表页面 >> 再请求每日一题接口
        _ = requests.get(url=leetCodeCN_All_URL)
        response = requests.post(
            leetCodeCN_Data_URL + "/graphql",
            json={
                "operationName": "questionOfToday",
                "variables": {},
                "query": "query questionOfToday { todayRecord {   question {     questionFrontendId     questionTitleSlug     __typename   }   lastSubmission {     id     __typename   }   date   userStatus   __typename }}",
            },
        )

        # print(json.loads(response.text)) >>
        """ 
        {
            'data': {
                'todayRecord': [
                    {
                        'question': {
                            'questionFrontendId': '1984',
                            'questionTitleSlug': 'minimum-difference-between-highest-and-lowest-of-k-scores',
                            '__typename': 'QuestionNode'
                        },
                        'lastSubmission': None,
                        'date': '2022-02-11',
                        'userStatus': None,
                        '__typename': 'DailyQuestionNode'
                    }
                ]
            }
        } 
        """

        # 获取今日每日一题的所有信息
        _ = requests.get(
            url=today_url
        )

        leetCode_Daily_questionTitle_CN = today_url[len(f"{leetCodeCN_Data_URL}/problems/"):]
        # print(">>>>>>>>>>>>>>>> ",leetCode_Daily_questionTitle_CN)
        response = requests.post(
            leetCodeCN_Data_URL + "/graphql",
            json={
                "operationName": "questionData",
                "variables": {"titleSlug": leetCode_Daily_questionTitle_CN},
                "query": "query questionData($titleSlug: String!) {  question(titleSlug: $titleSlug) {    questionId    questionFrontendId    boundTopicId    title    titleSlug    content    translatedTitle    translatedContent    isPaidOnly    difficulty    likes    dislikes    isLiked    similarQuestions    contributors {      username      profileUrl      avatarUrl      __typename    }    langToValidPlayground    topicTags {      name      slug      translatedName      __typename    }    companyTagStats    codeSnippets {      lang      langSlug      code      __typename    }    stats    hints    solution {      id      canSeeDetail      __typename    }    status    sampleTestCase    metaData    judgerAvailable    judgeType    mysqlSchemas    enableRunCode    envInfo    book {      id      bookName      pressName      source      shortDescription      fullDescription      bookImgUrl      pressImgUrl      productUrl      __typename    }    isSubscribed    isDailyQuestion    dailyRecordStatus    editorType    ugcQuestionId    style    __typename  }}",
            },
        )

        # 转化成json格式
        jsonText = json.loads(response.text).get("data").get("question")

        # print(jsonText)

        # 题目题号
        no = jsonText.get("questionFrontendId")

        # 题名
        leetCode_Daily_questionTitle_CN = jsonText.get("translatedTitle")
        leetCode_Daily_questionTitle_EN = jsonText.get("title")

        # 题目难度级别
        level = jsonText.get("difficulty")

        # 题目内容
        contextCN = jsonText.get("translatedContent")
        contextEN = jsonText.get("content")

        # 题目标签
        tags = jsonText.get("topicTags")
        tagsCN = []
        tagsEN = []
        for tag in tags:
            tagsCN.append(tag.get("translatedName"))
            tagsEN.append(tag.get("name"))

        if lang == LanguageType.CN:
            question = AlgoQuestion(
                no, leetCode_Daily_questionTitle_CN, level, contextCN, tagsCN, lang
            )
            return question
        elif lang == LanguageType.EN:
            return [
                no,
                leetCode_Daily_questionTitle_EN,
                level,
                contextEN,
                lang,
            ]
        elif lang == LanguageType.CN_MIX_EN:
            # TODO 单独处理格式
            pass
            # return [
            #     no,
            #     leetCode_Daily_questionTitle_CN,
            #     leetCode_Daily_questionTitle_EN,
            #     level,
            #     contextCN,
            #     contextEN,
            #     tagsCN,
            #     tagsEN,
            # ]

    except Exception as ex:
        raise ex