# -*- coding: utf-8 -*-
"""
可选的大模型客户端：调用 OpenAI 兼容接口（通义/豆包/OpenAI 都行）。

只用标准库 urllib 发请求，不需要装 openai 库。
"""
import json
import urllib.request

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


class LLMClient:
    def __init__(self, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, model=LLM_MODEL):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, question, qtype, docs):
        """让大模型参考检索到的资料，回答用户问题。"""
        context = "\n".join(f"- {d.text}" for d in docs)
        prompt = (
            f"你是机械制造领域的设备问答助手。\n"
            f"用户问题（类型：{qtype}）：{question}\n\n"
            f"以下是知识库中检索到的参考资料，请据此给出简洁、可操作的回答：\n{context}\n\n"
            f"如果资料不足，请明确说明。"
        )
        return self._chat(prompt)

    def _chat(self, prompt):
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")

        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
