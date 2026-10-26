"""规模压测：记忆变多以后，召回还准吗？还快吗？

做法：
    1. 建一个专用 Scope
    2. 先埋 10 条"目标记忆"（带唯一标识，如 ZC-7734）
    3. 逐步加入干扰记忆，分别在 25 / 100 / 200 / 400 条时测试
    4. 每个规模下问 10 个只能靠目标记忆回答的问题

指标：命中率、p50 延迟、p95 延迟。

用法：
    python stress.py
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8000").rstrip("/")
HERE = Path(__file__).resolve().parent

TARGETS = [
    ("ZC-7734", "数据结构课设的迷宫项目代号是 ZC-7734。"),
    ("8.0", "数据库课设要求 MySQL 8.0 版本，字符集 utf8mb4。"),
    ("socket", "网络实验只允许用 socket API，禁止使用任何 Web 框架。"),
    ("时间片", "RR 调度把时间片设成 0 会导致死循环。"),
    ("fastapi", "二手交易项目的后端使用 FastAPI。"),
    ("B+ 树", "B+ 树的阶数设为 4 时，插入第 5 个键就会分裂。"),
    ("mvcc", "事务部分用 MVCC 而不是两阶段锁，因为读多写少。"),
    ("utf8mb4", "字符集必须是 utf8mb4，否则 emoji 会乱码。"),
    ("死锁", "两个事务按相反顺序加锁会产生死锁。"),
    ("SSH 隧道", "部署用 SSH 隧道连内网数据库，不走公网。"),
]

QUESTIONS = [
    ("ZC-7734", "迷宫项目的代号是什么？"),
    ("8.0", "数据库课设要求什么版本？"),
    ("socket", "网络实验能用 Web 框架吗？"),
    ("时间片", "RR 时间片设成 0 会怎样？"),
    ("fastapi", "二手交易项目的后端用什么？"),
    ("B+ 树", "B+ 树阶数为 4 时什么时候分裂？"),
    ("mvcc", "事务部分为什么用 MVCC？"),
    ("utf8mb4", "为什么字符集必须是 utf8mb4？"),
    ("死锁", "什么情况会产生死锁？"),
    ("SSH 隧道", "怎么连内网数据库？"),
]

COURSES = ["数据结构", "数据库", "计算机网络", "操作系统", "软件工程", "编译原理", "创新项目"]
TOPICS = ["实验报告", "课堂笔记", "小组讨论", "作业订正", "参考书", "代码注释", "调试记录"]


def post(path: str, payload: dict) -> dict:
    request = Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST {path} -> HTTP {error.code}: {detail}") from error


def add_memory(scope_id: str, text: str, kind: str = "fact") -> None:
    post("/v1/memory/remember", {"scope_id": scope_id, "kind": kind, "text": text})


def fillers(count: int) -> list[str]:
    out = []
    for i in range(count):
        course = COURSES[i % len(COURSES)]
        topic = TOPICS[(i // len(COURSES)) % len(TOPICS)]
        out.append(f"{course}课的第 {i + 1} 条{topic}：这部分内容与本次提问无关，属于背景材料。")
    return out


def measure(scope_id: str) -> tuple[int, float, float]:
    hits = 0
    latencies = []
    for token, question in QUESTIONS:
        start = time.perf_counter()
        prepared = post(
            "/v1/context/prepare",
            {"scope_id": scope_id, "query": question, "max_bytes": 4000},
        )
        latencies.append((time.perf_counter() - start) * 1000)
        if token.lower() in (prepared.get("content") or "").lower():
            hits += 1
    p50 = statistics.median(latencies)
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    return hits, p50, p95


def main() -> int:
    run_id = uuid.uuid4().hex[:8]
    scope = post(
        "/v1/scopes",
        {
            "title": f"规模压测 {run_id}",
            "summary": "记忆数量对召回的影响",
            "idempotency_key": f"stress-{run_id}",
        },
    )
    scope_id = scope["scope_id"]
    print(f"压测 Scope：{scope_id}")

    for token, text in TARGETS:
        add_memory(scope_id, text, "fact")
    print(f"已写入 {len(TARGETS)} 条目标记忆\n")

    print(f"{'记忆总数':>8} {'命中':>6} {'p50(ms)':>9} {'p95(ms)':>9}")
    print("-" * 36)

    added = len(TARGETS)
    for size in (25, 100, 200, 400):
        need = size - added
        if need > 0:
            for text in fillers(need):
                add_memory(scope_id, text)
            added = size
        hits, p50, p95 = measure(scope_id)
        print(f"{size:>8} {hits:>4}/10 {p50:>9.1f} {p95:>9.1f}")

    print("\n说明：目标记忆始终存在，理论上应全部命中；命中下降说明干扰项淹没了信号。")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
