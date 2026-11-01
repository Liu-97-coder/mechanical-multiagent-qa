# -*- coding: utf-8 -*-
"""
RAG 知识库：把资料读进来、建立索引、按问题检索。

针对落地做的三点加固（用纯标准库实现，无需装向量库）：
  1. 每个 .md/.txt 文件作为"一条完整知识"返回，保证回答有完整上下文。
  2. 用"字符 2-gram + IDF"做检索：像"主轴/异响"这种独特字组给高分，
     像"是什么/怎么办"这种每篇都有的通用字组权重≈0，天然避免假命中。
  3. 知识库确实没有相关内容时返回空列表，由上层明确说"没有"，
     而不是硬凑无关文档误导用户。

以后要换真正的向量数据库（Milvus/Faiss），只需替换 search 方法。
"""
import os
import re
import math


class KnowledgeDoc:
    """一条知识（对应一个知识文件）。"""
    def __init__(self, text, source=""):
        self.text = text.strip()
        self.source = source


class KnowledgeIndex:
    def __init__(self, knowledge_dir):
        self.docs = []
        self._load(knowledge_dir)
        self._build_index()

    def _load(self, directory):
        """读取目录下所有 .md/.txt 文件，每个文件作为一条知识。"""
        for fname in sorted(os.listdir(directory)):
            if not fname.endswith((".md", ".txt")):
                continue
            path = os.path.join(directory, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                self.docs.append(KnowledgeDoc(content, source=fname))

    def _build_index(self):
        """预计算每篇文档的 2-gram 集合，以及每个 2-gram 的 IDF。"""
        n = len(self.docs)
        self._doc_grams = []
        df = {}  # 2-gram -> 出现在几篇文档
        for d in self.docs:
            grams = self._bigrams(d.text)
            self._doc_grams.append(grams)
            for g in grams:
                df[g] = df.get(g, 0) + 1
        # IDF：只保留"不是每篇都有"的字组（每篇都有的通用字组权重直接省略=0）
        self._idf = {g: math.log(n / c) for g, c in df.items() if c < n}

    def search(self, query, top_k=3):
        """返回与 query 最相关的 top_k 条知识；没有相关内容时返回空列表。"""
        q_grams = self._bigrams(query)
        scored = []
        for i, d in enumerate(self.docs):
            # 找出问题里、在本文档出现、且不是通用字组的 2-gram
            hits = [g for g in q_grams if g in self._doc_grams[i] and g in self._idf]
            # 至少命中 2 个独特字组，才认为这篇文档和问题相关（避免单字误命中）
            if len(hits) >= 2:
                scored.append((sum(self._idf[g] for g in hits), d))

        if not scored:
            return []  # 知识库里没有相关内容

        scored.sort(key=lambda x: x[0], reverse=True)
        # 按来源去重（一个文件只返回一次）
        seen, result = set(), []
        for _, d in scored:
            if d.source in seen:
                continue
            seen.add(d.source)
            result.append(d)
            if len(result) >= top_k:
                break
        return result

    @staticmethod
    def _bigrams(text):
        """相邻两个字符作为特征集合。"""
        chars = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]", text)
        return {chars[i] + chars[i + 1] for i in range(len(chars) - 1)}
