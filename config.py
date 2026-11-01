# -*- coding: utf-8 -*-
"""
大模型接入配置（可选）。

默认不接大模型：项目用"模板生成"也能完整跑通，适合演示。
想接真实大模型时，填下面三项即可：
    LLM_ENABLED = True
    LLM_API_KEY = "你的key"
    LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 以通义千问为例
    LLM_MODEL = "qwen-plus"
"""

LLM_ENABLED = False
LLM_API_KEY = ""
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_MODEL = "qwen-plus"
