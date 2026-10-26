"""查询改写：把学生口语化的提问，扩展成记忆里可能出现的术语。

纯规则实现，不依赖任何模型，可解释、可审计、零成本。
这是"没有向量检索时"的折中方案：用一张课程域同义词表，把
"深搜" 扩成 "DFS"，把 "进程控制块" 扩成 "PCB"。
"""

from __future__ import annotations

SYNONYMS: dict[str, list[str]] = {
    "深搜": ["DFS", "递归"],
    "广搜": ["BFS"],
    "持久层框架": ["ORM"],
    "进程控制块": ["PCB", "结构体数组"],
    "第三方网络库": ["socket", "Web 框架"],
    "跑不完": ["时间片", "死循环"],
    "接收数据": ["recv", "粘包"],
    "接口调不通": ["域名", "HTTPS", "校验"],
    "后端": ["FastAPI"],
    "编译器版本": ["C++17"],
    "数据库版本": ["MySQL 8.0"],
}


def expand(query: str) -> str:
    """在原始提问后面追加同义术语，供全文检索匹配。"""

    extras: list[str] = []
    for phrase, terms in SYNONYMS.items():
        if phrase in query:
            extras.extend(term for term in terms if term not in query)
    if not extras:
        return query
    return query + " " + " ".join(dict.fromkeys(extras))


if __name__ == "__main__":
    for sample in ["为什么用深搜而不是广搜？", "进程控制块是怎么存的？", "今天天气怎么样"]:
        print(f"{sample}  ->  {expand(sample)}")
