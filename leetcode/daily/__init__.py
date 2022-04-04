from utils.utils import get_bot, scheduler
from nonebot import on_command
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent, MessageSegment
from services.log import logger
from configs.path_config import IMAGE_PATH
from utils.manager import group_manager
from configs.config import Config
from pathlib import Path

from .data_source import get_leetcode_daily_question

# 功能 cmd
cmd = "今日力扣"
cmd_aliases = {'leetcode', 'leetCode', 'LeetCode', '力扣', '开卷'}

# 插件名称
__zx_plugin_name__ = "每日LeetCode"
# 插件分类
__plugin_type__ = ("学习频道",)

# 帮助插件读出来的文本
__plugin_usage__ = """
usage：
    开卷！>> 快来学习辣！
    指令：
        今日力扣    抓取 leetCode 今日推荐题目
            （别名）
                {}
""".format(cmd_aliases).strip()

# 简介
__plugin_des__ = "让我看看今天能不能睡大觉"
__plugin_cmd__ = [cmd]

__plugin_version__ = 0.1
__plugin_author__ = "evlic"

__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": [cmd, __zx_plugin_name__],
}

# 添加任务
__plugin_task__ = {"leetCodeDaily": "leetCode每日推送"}

Config.add_plugin_config(
    "_task",
    "DEFAULT_LEETCODE_DAILY",
    True,
    help_=f"被动 leetCode推送 进群默认开关状态",
    default_value=True,
)

@scheduler.scheduled_job(
    "cron",
    hour=9,
    minute=30,
)
async def _():
    # 每日提醒
    bot = get_bot()
    if bot:
        gl = await bot.get_group_list()
        gl = [g["group_id"] for g in gl]
        today_img, today_url, get_from = await get_leetcode_daily_question(Daily_PATH)
        if today_img:
            get_from = 'leetCodeCN 官网'
            
            mes = "[[_task|leetCodeDaily]]" + today_img + f"\n「推送」\n>> 🌐URL「{today_url}」"  + f"\n>> 数据取自「{get_from}」"
            for gid in gl:
                if await group_manager.check_group_task_status(gid, "leetCodeDaily"):
                    await bot.send_group_msg(group_id=int(gid), message="" + mes)


leetCodeDaily_CMD = on_command("今日力扣", aliases= cmd_aliases, priority=5, block=True)

Daily_PATH = IMAGE_PATH / "leetcode" / "daily"
Daily_PATH.mkdir(parents=True, exist_ok=True)

@leetCodeDaily_CMD.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State): 
    today_img, today_url, get_from = await get_leetcode_daily_question(Daily_PATH)
    if today_img: 
        logger.info(
            f"User >> {event.user_id}, Group >> {event.group_id if isinstance(event, GroupMessageEvent) else ' private '}"
            f"by {get_from} 查看了{__zx_plugin_name__}"
        )
        get_from = 'leetCodeCN 官网实时数据' if get_from == 'net' else '服务器🖥缓存'
        await leetCodeDaily_CMD.send(today_img + f"\n>> 🌐URL「{today_url}」"  + f"\n>> 数据取自「{get_from}」")
        # 暂时作为文字输出
        # await leetCodeDaily_CMD.send(f"{today_img}")
    else:
        await leetCodeDaily_CMD.send(f"{__zx_plugin_name__}获取数据失败")