"""Experience 演示：踩坑 → 审核 → 复用。

流程：
    1. 把一次真实的踩坑写成 Source（证据）
    2. propose 一条 Experience（情境 / 动作 / 结果 / 教训），进入 Review Inbox，状态 pending
    3. 审核通过（approve），生成不可变版本
    4. 用新提问验证：这条经验能被上下文召回

关键点：propose 不需要任何模型，审核是独立的一步，未审核的内容不会进入召回。

用法：
    python experience_demo.py [--scope S4]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8000").rstrip("/")
HERE = Path(__file__).resolve().parent


def post(path: str, payload: dict) -> dict:
    request = Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST {path} -> HTTP {error.code}: {detail}") from error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", default="S4")
    args = parser.parse_args()

    scopes = json.loads((HERE / "scopes.json").read_text(encoding="utf-8"))
    scope_id = scopes[args.scope]
    run_id = uuid.uuid4().hex[:8]
    print(f"Scope {args.scope} = {scope_id}\n")

    # 1. 证据：一次真实的踩坑
    source = post(
        "/v1/sources/content",
        {
            "scope_id": scope_id,
            "source_id": f"pitfall-{run_id}",
            "content": (
                "操作系统课设做 RR 调度时，把时间片设为 0，模拟器直接死循环，"
                "排查了两个小时才发现是时间片参数没做非零校验。"
            ),
            "metadata": {"origin": "experience-demo", "kind": "task-outcome"},
        },
    )
    source_id = source["source"]["source_id"] if "source" in source else source["source_id"]
    print(f"[1] 踩坑证据已记录：{source_id}")

    # 2. 提议一条经验（未审核）
    proposed = post(
        "/v1/experience/propose",
        {
            "scope_id": scope_id,
            "proposal": {
                "situation": "实现 RR 时间片轮转调度，需要为时间片设一个初始值",
                "action": "直接沿用示例代码里的常量，未做参数校验",
                "outcome": "时间片为 0 导致模拟器死循环，排查耗时两小时",
                "lesson": "时间片、并发数这类参数必须在入口做非零校验，并在注释里写明取值范围",
            },
            "source_refs": [{"name": "content", "source_id": source_id}],
            "artifact_refs": [],
        },
    )
    candidate = proposed.get("candidate") or proposed
    candidate_id = candidate.get("candidate_id") or candidate.get("id")
    version = candidate.get("version", 0)
    print(f"[2] 经验已进入待审队列：candidate={candidate_id} version={version}")

    # 3. 审核通过
    approved = post(
        "/v1/candidates/approve",
        {"scope_id": scope_id, "candidate_id": candidate_id, "expected_version": version},
    )
    print(f"[3] 审核通过：{json.dumps(approved, ensure_ascii=False)[:160]}...")

    # 4. 验证可召回
    prepared = post(
        "/v1/context/prepare",
        {
            "scope_id": scope_id,
            "query": "时间片应该设成多少，有什么要注意的？",
            "max_bytes": 4000,
        },
    )
    content = prepared.get("content") or ""
    hit = "非零校验" in content or "时间片" in content
    print(f"[4] 召回验证：status={prepared.get('status')} 命中={'是' if hit else '否'}")
    print("\n提示：未审核的经验不会进入召回；approve 之后才可见。")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
