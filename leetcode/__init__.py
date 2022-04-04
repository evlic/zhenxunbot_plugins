import nonebot

nonebot.load_plugins("plugins_ex/evlic_repo/leetcode")

# # 功能 cmd
# daily_cmd = "今日力扣"
# week_rank_cmd = "周赛排名"
# banding_user = "绑定力扣"

# # 用法说明，出现在 「详细帮助」
# __plugin_usage__ = """
# usage：
#     开卷！>> 快来学习辣！
#     指令：
#         今日力扣        抓取 leetCode 今日推荐题目
        
#         绑定力扣：uid  绑定用户「uid」
#                         示例 >> 绑定力扣：evlic
#                                     要求 uid 一定准确，详见个人空间的 URL 
#                                     这里的冒号是英文冒号和中文冒号均可
        
#         周赛排名        获取本周群内绑定过「uid」的群员周赛排名
# """.strip()