from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message
from nonebot.params import CommandArg
from sqlalchemy import false, true
from services.log import logger
from configs.config import NICKNAME
from utils.utils import is_number
import random
import asyncio

cmds = ["roll", "rollNum", "rolls", "rollsNum"]
seps = [",", "，"]

__zx_plugin_name__ = "roll"
__plugin_author__ = "evlic"
__plugin_version__ = 0.1

__plugin_usage__ = """
usage：
    随机数字 或 随机选择事件
    roll    代表返回结果唯一    (提醒词有些羞耻，不是「{}」干的)
    rolls   代表返回多个结果
    
    分隔符：
        输入区间只支持空格
        输入自定义列表仅支持中文逗号、英文逗号（只要有分割符就视作一个单独选项）

    指令：
        roll: （如果无参数）随机 0-100 的数字
        roll *[文本]: 随机事件
        - 示例：roll 吃饭 睡觉 打游戏
        
        rolls: 输入一个列表返回随机顺序
            参数 -n 返回带标号的结果，-n0 标号从 0 开始
        - 示例：
            rolls -n xxx,xxx1,xxx2
            >>  1:「xxx」
                2:「xxx1」
                3:「xxx2」
        rollNum: 指定 1-x 的数字
        rollsNum: 指定 1-x 中的 多个数字（不会重复） << 有没有可能班上需要抽人
        
""".format(__plugin_author__).strip()

__plugin_des__ = "犹豫不决吗？那就让我帮你决定吧"
__plugin_cmd__ = ["roll", "roll *[文本]", "rollNum", "rolls", "rollsNum"]
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["roll"],
}

# 尝试用所有分隔符分隔字符串
def words_split(words : str) -> list:
    r = []
    for s in seps:
        r. append(words.split(s))
    
    r.sort(key=lambda s : len(s), reverse=True)
    return r[0]


roll = on_command("roll", priority=5, block=True)
@roll.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    """
    roll            返回 1 - 100 随机数
    roll [words]*   返回 选择输入文本项中随机一个
    """
    msg = arg.extract_plain_text().strip().split()
    words = []
    if len(msg) == 1:
        words = words_split(msg[0])
    if not words:
        await roll.finish(f"roll: {random.randint(0, 100)}", at_sender=True)
    
    user_name = event.sender.card or event.sender.nickname
    await roll.send(
        random.choice(
            [
                "转动命运的齿轮，拨开眼前迷雾...",
                f"启动吧，命运的水晶球，为{user_name}指引方向！",
                "嗯哼，在此刻转动吧！命运！",
                f"在此祈愿，请为{user_name}降下指引...",
            ]
        )
    )
    await asyncio.sleep(1)
    x = random.choice(words)
    await roll.send(
        random.choice(
            [
                f"让{NICKNAME}看看是什么结果！答案是：‘{x}’",
                f"根据命运的指引，接下来{user_name} ‘{x}’ 会比较好",
                f"祈愿被回应了！是 ‘{x}’！",
                f"结束了，{user_name}，命运之轮停在了 ‘{x}’！",
            ]
        )
    )
    logger.info(
        f"(USER {event.user_id}, "
        f"GROUP {event.group_id if isinstance(event, GroupMessageEvent) else 'private'}) 发送roll：{msg}"
    )

rollNum = on_command("rollNum", priority=5, block=True)
@rollNum.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    if not msg:
        await rollNum.finish("需要指定数的范围, 可以输入两个整数, 分别为上下界")
    
    n = len(msg)
    if n == 1 and is_number(msg[0]):
        await rollNum.finish(f"roll: {random.randint(1, int(msg[0]))}", at_sender=True)
    elif n == 2 and (is_number(msg[0]) and is_number(msg[1].is_integer())):
        a, b = int(msg[0]), int(msg[1])
        if a > b: 
            a, b = b, a
        await rollNum.finish(f"roll: {random.randint(a, b)}", at_sender=True)
    else:
        rollNum.finish(f"需要指定数的范围, 可以输入最多两个整数, 分别为上下界。输入有误 >> len = {n}")
        ...
    await asyncio.sleep(1)
    x = random.choice(msg)
    await rollNum.finish(f"roll: {x}", at_sender=True)


rolls = on_command("rolls", priority=5, block=True)
@rolls.handle()
async def _(event: MessageEvent, arg: Message=CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    # 把 msg 的最后一位视作 words
    # 支持的定制参数
    # -n 带序号(高优先级) ，-n0 序号从 0 开始
    words = words_split(msg[len(msg) - 1])
    msg = msg[:len(msg) - 1]
    
    # 解析自定义参数
    flag, cnt, res = "", len(words), []
    for i in msg:
        if is_number(i):
            cnt = i
            break
    
    if "-n" in msg:
        flag = 'n'
    elif '-n0' in msg:
        flag = 'n0'
    
    if cnt < len(words) - 1:
        words = random.choices(words, k=cnt)
    else:
        random.shuffle(words)

    res = ""
    if flag == "":
        res = words
    else:
        des = 0
        if flag == "n" :
            des = 1
        
            # self.tags = " ".join("{}"
            #             .format(self._tag_map["blue"].format(self.tags[idx]))
            #             for idx in range(len(self.tags)))
        res = "\n".join(f"{idx+des}:「{words[idx]}」" for idx in range(len(words)))

    await asyncio.sleep(1)
    await rolls.finish(f"rolls: \n{res}", at_sender=True)


# l h cnt [exclude [num in range(l, h)]]
rollNums = on_command("rollsNum", priority=5, block=True)
@rollNums.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()

    n = len(msg)

    if n < 3: 
        for s in msg: 
            if not is_number(s):
                return 
        if n == 2:
            a, b = int(msg[0]), int(msg[1])
            if a > b:
                a, b = b, a
            array = list(range(a, b + 1))
            await asyncio.sleep(1)
            random.shuffle(array)
            await rollNums.finish(f"rolls: {array}", at_sender=True)

        else:
            pass

    else:
        flag = true
        exclude = false
        
        for s in msg[: 3]:
            if not is_number(s):
                flag = not flag
                break
        
        if flag:
            # ab 之间取 c 个 (公平随机)
            a, b, c = int(msg[0]), int(msg[1]), int(msg[2])

            if a > b: 
                a, b = b, a
            
            if c >= b - a - (n - 4):
                flag = not flag

            choice_list = list(range(a, b + 1))
            if n > 3 and msg[3] in ["|", "｜", "exclude"]:
                exclude = not exclude
                for s in msg[4:]:
                    if is_number(s): 
                        choice_list.remove(int(s))
            
            if flag:
                res = random.choices(choice_list, k=c)
            else:
                random.shuffle(choice_list)
                res = choice_list

            await asyncio.sleep(1)
            await rollNums.finish(f"rolls: {res}", at_sender=True)
    
    await rollNums.finish(f"输入有误请自行查阅文档", at_sender=True)
