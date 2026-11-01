# -*- coding: utf-8 -*-
"""
项目一网页版入口：机械制造多Agent问答系统

运行：  python webapp.py
然后浏览器打开  http://localhost:8001  即可使用。

和项目二（8000端口）互不冲突，两个可以同时开。
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from agents import IntentAgent, RetrieveAgent, GenerateAgent, VerifyAgent
from rag import KnowledgeIndex
from config import LLM_ENABLED

PORT = 8001
WEB_ROOT = os.path.join(os.path.dirname(__file__), "static")
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")

# 启动时装载一次知识库和四个 Agent
index = KnowledgeIndex(KNOWLEDGE_DIR)
intent_agent = IntentAgent()
retrieve_agent = RetrieveAgent(index)
if LLM_ENABLED:
    from llm import LLMClient
    generate_agent = GenerateAgent(llm=LLMClient())
else:
    generate_agent = GenerateAgent(llm=None)
verify_agent = VerifyAgent()


def process(question):
    """走完整的多Agent流程，返回每一步的结果。"""
    qtype = intent_agent.run(question)
    docs = retrieve_agent.run(question)
    answer = generate_agent.run(question, qtype, docs)
    answer = verify_agent.run(question, answer, qtype, has_docs=bool(docs))
    return {
        "qtype": qtype,
        "doc_count": len(docs),
        "answer": answer,
        "sources": [d.source for d in docs],
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_file("index.html")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/ask":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            question = (body.get("question") or "").strip()
            result = process(question) if question else {
                "qtype": "", "doc_count": 0, "answer": "请输入问题。", "sources": [],
            }
            self._send_json(result)
        else:
            self.send_error(404)

    def _send_file(self, name):
        path = os.path.join(WEB_ROOT, name)
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"机械制造多Agent问答系统（网页版）已启动：http://localhost:{PORT}")
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
