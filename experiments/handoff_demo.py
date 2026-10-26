"""Handoff 演示：队友接手一个课设的完整四步流程。

流程：
    1. 写一份工作契约（Work Contract）——这次交接要做什么、边界在哪
    2. prepare-current 生成临时交接包（Prepared Handoff）
    3. commit 把交接包固化成不可变版本（里程碑）
    4. 接手方 continue + acknowledge（确认收到）
    5. 记录结果（Task Outcome）

全程不需要任何大模型，内容由调用方给出，服务端只做校验、版本和留痕。

用法：
    python handoff_demo.py
    python handoff_demo.py --scope S3
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


def claim(text: str) -> dict:
    return {"text": text, "basis": "declared", "evidence": []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", default="S3")
    args = parser.parse_args()

    scopes = json.loads((HERE / "scopes.json").read_text(encoding="utf-8"))
    scope_id = scopes[args.scope]
    run_id = uuid.uuid4().hex[:8]
    print(f"Scope {args.scope} = {scope_id}\n")

    # 0. 边界证据：交接发生在什么状态下
    boundary = post(
        "/v1/sources/content",
        {
            "scope_id": scope_id,
            "source_id": f"handoff-boundary-{run_id}",
            "content": "单线程 HTTP 服务器已跑通 GET/200/404，接下来要加并发和压力测试。",
            "metadata": {"origin": "handoff-demo"},
        },
    )
    boundary_id = (
        boundary["source"]["source_id"] if "source" in boundary else boundary["source_id"]
    )
    print(f"[0] 边界证据写入 Source：{boundary_id}")

    # 1. 工作契约
    contract = post(
        "/v1/work/contracts/create",
        {
            "scope_id": scope_id,
            "source_id": f"work-contract-{run_id}",
            "contract": {
                "schema": "powercontext.work-contract.v1",
                "trust": "untrusted_input",
                "objective": "把单线程 HTTP 服务器改造成并发版本，并通过压测",
                "facts": [claim("GET、200、404 三个功能已通过验收")],
                "in_scope": ["并发模型改造", "压测脚本"],
                "exclusions": ["不改动 HTTP 解析逻辑"],
                "completion_criteria": ["并发 100 连接下无请求丢失", "压测报告含 QPS 与错误率"],
                "authorization_notes": ["可以修改 server 模块", "不要动 parser"],
                "open_questions": [],
            },
        },
    )
    print(f"[1] 工作契约已创建：{json.dumps(contract, ensure_ascii=False)[:120]}...")

    # 2. 生成临时交接包
    prepared = post(
        "/v1/work/handoffs/prepare-current",
        {
            "scope_id": scope_id,
            "source_id": f"handoff-{run_id}",
            "handoff": {
                "schema": "powercontext.current-work-handoff.v1",
                "trust": "untrusted_input",
                "objective": "把单线程 HTTP 服务器改造成并发版本，并通过压测",
                "state": [
                    claim("单线程版本已跑通 GET/200/404"),
                    claim("recv 粘包问题已定位，尚未修复"),
                ],
                "disposition": "continuable",
                "next_action": claim("引入线程池，每个连接一个 handler 线程"),
                "omissions": [],
            },
        },
    )
    print("[2] 临时交接包已生成（未固化）")

    # 3. 固化成里程碑
    committed = post(
        "/v1/handoff/commit",
        {"scope_id": scope_id, "handoff": prepared["handoff"]},
    )
    reference = committed["reference"]
    print(f"[3] 交接已固化：{reference['family']}/{reference['artifact_id']}@{reference['revision']}")

    # 4. 接手方继续并确认
    continued = post(
        "/v1/handoff/continue",
        {"scope_id": scope_id, "selection": "exact", "revision": reference},
    )
    ack = post(
        "/v1/work/handoffs/acknowledge",
        {
            "scope_id": scope_id,
            "source_id": f"ack-{run_id}",
            "receiver": "队友-李四",
            "status": "accepted",
            "selection": "exact",
            "revision": reference,
            "receiver_checks": {
                "live_state": "confirmed",
                "capability": "confirmed",
                "authorization": "confirmed",
            },
            "message": "已理解边界，开始改并发",
        },
    )
    print(f"[4] 接手方已确认：{json.dumps(ack, ensure_ascii=False)[:120]}...")

    # 5. 记录结果
    outcome = post(
        "/v1/work/outcomes/record",
        {
            "scope_id": scope_id,
            "source_id": f"outcome-{run_id}",
            "outcome": {
                "schema": "powercontext.task-outcome.v1",
                "trust": "untrusted_observation",
                "objective": "把单线程 HTTP 服务器改造成并发版本，并通过压测",
                "status": "partial",
                "summary": "线程池版本跑通，100 并发下丢 2 个请求，待修",
                "observations": [
                    claim("线程池版本已跑通，100 并发下丢失 2 个请求"),
                ],
                "checks": [
                    {
                        "name": "并发 100 连接无请求丢失",
                        "status": "failed",
                        "basis": "declared",
                        "evidence": [],
                    }
                ],
                "produced_artifacts": [],
                "remaining_work": ["修复高并发下的连接丢失"],
            },
        },
    )
    print(f"[5] 结果已记录：{json.dumps(outcome, ensure_ascii=False)[:120]}...")

    print("\n四步流程完成：Work Contract -> Prepared -> Committed -> Ack -> Outcome")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
