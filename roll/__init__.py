from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message
from nonebot.params import CommandArg
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
    roll    代表返回结果唯一
    rolls   代表返回多个结果       需要指定返回个数并且小于等于长度，默认等于长度
                                第一个参数会被尝试作为数字读取视为是数字
    
    分隔符：
        输入区间只支持空格
        输入自定义列表仅支持中文逗号、英文逗号（只要有分割符就视作一个单独选项）

    指令：
        roll: （如果无参数）随机 0-100 的数字
        roll *[文本]: 随机事件
        - 示例：roll 吃饭 睡觉 打游戏
        
        rolls: 输入一个列表返回随机顺序
            参数 -n 返回带标号的结果，-n0 标号从 0 开始
            参数 -a 定义数组区间 例如 (1,3) 为开区间 
                    注意：定义区间时不能有空格(懒得写更多的字符串代码了)
                        - 支持的写法：
                            [x,y] (x,y) [x,y) (x,y]
        - 示例：
            rolls -n xxx,xxx1,xxx2
            >>  1:「xxx」
                2:「xxx1」
                3:「xxx2」
            rolls -a [1,3] -n0
            >>  
        
""".format(__plugin_author__).strip()

__plugin_des__ = "犹豫不决吗？那就让我帮你决定吧"
__plugin_cmd__ = ["roll", "roll *[文本]", "rollNum [min, max]", "rolls", "rollsNum [-n] &cnt &[min, max] [| 排除项]"]
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

is_range_base = 0b10101
qupte =  0b10000
lopen =  0b00100
lclose = 0b01100
ropen =  0b00001
rclose = 0b00011
def is_range(s : str) -> int:
    # 设计位运算
    # 00000
    # 10000 表示只有一个逗号
    # 10100 表示左开区间
    # 11100 表示左闭区间
    # 11101 表示左闭右开区间
    # 11111 表示左右闭区间
    res = 0
    if s.startswith("[") :
        res |= lclose
    elif  s.startswith("("):
        res |= lopen
    if s.endswith("]"):
        res |= rclose
    elif s.endswith(")"):
        res |= ropen
    if s.count(',') == 1:
        res |= qupte
    return res

# 请确保为 range 格式，仅进行 isNumber 判断
def parse_range(s : str) -> list:
    res = []
    flag = is_range(s)
    n = s[1: len(s) - 1].split(',')
    
    for v in n:
        if is_number(v):
            res.append(int(v))
        else:
            return res
    if flag & lclose < lclose:
        res[0] -= 1
    if flag & rclose < rclose:
        res[1] -= 1

    return res

# roll >> 返回单个的随机结果
roll = on_command("roll", priority=5, block=True)
# rolls >> 返回指定个数的随机结果
rolls = on_command("rolls", priority=5, block=True)

@roll.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    """
    roll            返回 1 - 100 随机数
    roll [words]*   返回 选择输入文本项中随机一个
    """
    words = arg.extract_plain_text().strip().split()
    # 如果发现指令以后的参数只有一个，就认为不是以空格作为分隔符的，执行额外的字符串处理工作
    if len(words) == 1:
        words = words_split(words[0])
    if not words:
        await roll.finish(f"roll: {random.randint(0, 100)}", at_sender=True)
    
    user_name = event.sender.card or event.sender.nickname 
    await asyncio.sleep(1)
    x = random.choice(words)
    await roll.finish(f"roll: {x}", at_sender = True)

@rolls.handle()
async def _(event: MessageEvent, arg: Message=CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    flag = {"-n":False, "-a": False, "-n0": False}
    
    idx = 0

    while idx < len(msg):     
        if msg[idx] in flag:
            flag[msg[idx]] = True
            msg.pop(idx)
        else:
            idx += 1
    # logger.info(msg)
    
    cnt = 0
    if is_number(msg[0]):
        cnt = int(msg[0])
        if len(msg) > 1:
            msg.pop(0)
            # logger.info(f"cnt >> {cnt}")
    else: 
        cnt = 0xefffffff
    # 此时 msg 可能是区间 也可能是 序列
    words = []
    if flag["-a"]:
        if is_range(msg[0]) >= is_range_base:
            interval = parse_range(msg[0])
            if len(interval) == 2:
                words = [*range(interval[0], interval[1] + 1)]
            else : return
        else: 
            await rolls.finish(f"{msg[0]} 不是 range | 依据 { is_range(msg[0]) } >= {is_range_base} =  {is_range(msg[0]) >= is_range_base}")
    else:
        words = words_split(msg[0])

    # logger.info(f"{words}, {cnt}")

    if cnt < len(words):
        words = random.choices(words, k=cnt)
    else:
        random.shuffle(words)

    res = ""
    if not flag["-n"] and not flag["-n0"]:
        res = words
    else:
        des = 0
        if flag["-n"] :
            des = 1
        
            # self.tags = " ".join("{}"
            #             .format(self._tag_map["blue"].format(self.tags[idx]))
            #             for idx in range(len(self.tags)))
        res = "\n".join(f"{idx+des}:「{words[idx]}」" for idx in range(len(words)))

    await asyncio.sleep(1)
    await rolls.finish(f"rolls: \n{res}", at_sender=True)