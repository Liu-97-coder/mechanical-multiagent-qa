# -*- coding: utf-8 -*-
"""
项目一入口：机械制造多Agent问答系统（命令行版）

运行：  python main.py
然后直接输入问题，比如：
  主轴异响是什么原因
  CNC选型要多大功率
  液压油多久换一次
输入 exit 退出。
"""
import os

from agents import IntentAgent, RetrieveAgent, GenerateAgent, VerifyAgent
from rag import KnowledgeIndex
from config import LLM_ENABLED

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")


def main():
    print("=" * 50)
    print("机械制造多Agent问答系统（本地演示版）")
    print("每个 Agent 都干了什么，会一步步打印给你看")
    print("=" * 50)

    # 装载知识库
    index = KnowledgeIndex(KNOWLEDGE_DIR)
    print(f"\n已载入知识库：{len(index.docs)} 条资料片段\n")

    # 初始化四个 Agent
    intent_agent = IntentAgent()
    retrieve_agent = RetrieveAgent(index)
    if LLM_ENABLED:
        from llm import LLMClient
        generate_agent = GenerateAgent(llm=LLMClient())
    else:
        generate_agent = GenerateAgent(llm=None)
    verify_agent = VerifyAgent()

    while True:
        try:
            question = input("\n你问：").strip()
        except EOFError:  # 按 Ctrl+C 或输入结束时正常退出
            print("\n再见！")
            break
        if not question:
            continue
        if question.lower() in ("exit", "quit", "退出"):
            print("再见！")
            break

        # ---- 1. 意图识别 ----
        qtype = intent_agent.run(question)
        print(f"[Agent1-意图识别] 问题类型 → {qtype}")

        # ---- 2. 检索 ----
        docs = retrieve_agent.run(question)
        print(f"[Agent2-检索] 找到 {len(docs)} 条相关资料")

        # ---- 3. 生成 ----
        answer = generate_agent.run(question, qtype, docs)

        # ---- 4. 质检 ----
        answer = verify_agent.run(question, answer, qtype, has_docs=bool(docs))

        print("\n" + "-" * 50)
        print(answer)
        print("-" * 50)

        # 展示检索到的来源
        if docs:
            print("\n[资料来源]")
            for d in docs:
                print(f"  · {d.source}")


if __name__ == "__main__":
    main()
