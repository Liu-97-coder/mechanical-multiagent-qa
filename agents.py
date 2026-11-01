# -*- coding: utf-8 -*-
"""
多Agent问答系统 —— 四个分工明确的小模块

设计原则：每个 Agent 只做一件事，串起来就是一个完整回答流程，
方便看懂，也方便在面试里讲清楚。

流程：
  用户提问
    -> IntentAgent   : 判断这是哪一类问题（故障诊断 / 参数选型 / 维护保养）
    -> RetrieveAgent : 去知识库里找相关资料
    -> GenerateAgent : 把资料组织成能用的回答
    -> VerifyAgent   : 最后自查一遍，看回答够不够
"""


class IntentAgent:
    """判断用户的问题属于哪一类。"""

    # 用几个关键词来判断问题类型，简单直观
    TYPE_KEYWORDS = {
        "故障诊断": ["故障", "异响", "报警", "报错", "漏油", "不启动", "异常", "过热", "过载", "震动"],
        "参数选型": ["选型", "参数", "规格", "多大", "扭矩", "功率", "转速", "型号", "匹配"],
        "维护保养": ["保养", "维护", "多久换", "更换", "润滑", "加注", "检查周期", "清洁"],
    }

    def run(self, question):
        """返回问题类型。都匹配不到就归为'其他'。"""
        for qtype, keywords in self.TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in question:
                    return qtype
        return "其他"


class RetrieveAgent:
    """从知识库检索与问题相关的资料片段。"""
    def __init__(self, index):
        self.index = index

    def run(self, question, top_k=3):
        """返回最相关的 top_k 条知识片段。"""
        return self.index.search(question, top_k=top_k)


class GenerateAgent:
    """
    把检索到的资料组织成回答。

    有两种模式：
      - 无大模型（默认）：直接提取资料里的要点，拼成回答。
        这样不花一分钱也能跑通整个流程，用来演示和讲解足够。
      - 有大模型：调用外部大模型，把资料当参考，生成更自然的话。
    """
    def __init__(self, llm=None):
        self.llm = llm  # 传入 llm 对象就启用大模型模式，否则用模板模式

    def run(self, question, qtype, docs):
        if self.llm is not None:
            return self.llm.generate(question, qtype, docs)
        return self._template_answer(question, qtype, docs)

    def _template_answer(self, question, qtype, docs):
        """没有大模型时，把资料要点整理成回答。"""
        if not docs:
            return "知识库里暂时没有找到相关的资料，请换个说法试试。"

        lines = []
        for i, d in enumerate(docs, 1):
            lines.append(f"{i}. {d.text.strip()}")

        head = f"根据知识库，关于「{qtype}」的问题，查到以下相关信息：\n"
        tail = "\n（以上内容来自知识库检索，若有具体设备型号请补充后再查更准。）"
        return head + "\n".join(lines) + tail


class VerifyAgent:
    """最后质检：检查回答是否覆盖了问题里的实质内容（用 2-gram，避免误报）。"""

    # 通用虚词 2-gram：出现频率高、不承载领域含义，质检时不作为"必须覆盖"项
    VAGUE_GRAMS = {
        "是什", "什么", "么原", "原因", "怎么", "么办", "如何", "为什么",
        "问题", "处理", "检查", "一个", "这个", "那个", "需要", "是否",
        "应该", "可能", "一般", "进行", "出现", "情况", "时候", "多少",
        "多久", "几种", "哪些", "帮忙", "一下",
    }

    def run(self, question, answer, qtype, has_docs=True):
        # 知识库没命中时，答案本身就是"没有相关"，无需自查
        if not has_docs:
            return answer
        core = [g for g in self._grams(question) if g not in self.VAGUE_GRAMS]
        if not core:
            return answer
        covered = sum(1 for g in core if g in answer)
        if covered / len(core) < 0.5:
            return answer + "\n\n[自查] 回答可能没覆盖到你问的核心内容，建议补充设备型号或更详细现象。"
        return answer

    @staticmethod
    def _grams(text):
        """相邻两个字符作为特征集合。"""
        import re
        chars = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]", text)
        return {chars[i] + chars[i + 1] for i in range(len(chars) - 1)}
