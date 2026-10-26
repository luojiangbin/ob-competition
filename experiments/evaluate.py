"""跑 20 条跨会话召回用例，计算召回准确率。

原理：PowerContext 的 /v1/context/prepare 返回的是"新会话能看到的上下文"。
如果期望关键词全部出现在这段上下文里，就算召回成功——不需要任何大模型，结果可复现。

用法：
    python evaluate.py
    python evaluate.py --dry-run        # 只读文件，不联网
    python evaluate.py --max-bytes 8000

前置：先跑 seed.py，生成 scopes.json。

输出：
    results.csv    每条用例的明细
    终端打印总准确率、分类准确率
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from expand import expand as expand_query

BASE_URL = os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN = os.environ.get("POWERCONTEXT_TOKEN")
HERE = Path(__file__).resolve().parent


def post(path: str, payload: dict) -> dict:
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST {path} -> HTTP {error.code}: {detail}") from error


def load_cases(path: Path) -> list[dict]:
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-bytes", type=int, default=4000)
    parser.add_argument("--cases", default=str(HERE / "cases.jsonl"),
                        help="用例文件；留出集用 cases_holdout.jsonl")
    parser.add_argument("--expand", action="store_true",
                        help="开启查询改写（同义词扩展）")
    parser.add_argument("--out", default=str(HERE / "results.csv"))
    args = parser.parse_args()

    scopes_path = HERE / "scopes.json"
    if scopes_path.exists():
        scopes = json.loads(scopes_path.read_text(encoding="utf-8"))
    else:
        # 还没跑过 seed.py：dry-run 用假的 scope 映射，只校验用例本身
        if not args.dry_run:
            print("缺少 scopes.json，请先运行 seed.py", file=sys.stderr)
            return 2
        seed = json.loads((HERE / "seed_data.json").read_text(encoding="utf-8"))
        scopes = {scope["key"]: f"dry-{scope['key']}" for scope in seed["scopes"]}
    cases = load_cases(Path(args.cases))
    print(f"用例 {len(cases)} 条，Scope {len(scopes)} 个")

    if args.dry_run:
        missing = [c["id"] for c in cases if c["scope"] not in scopes]
        if missing:
            print(f"这些用例的 Scope 不存在：{missing}")
            return 1
        print("dry-run 通过。")
        return 0

    rows = []
    hits = 0
    by_category: dict[str, list[int]] = {}

    for case in cases:
        scope_id = scopes[case["scope"]]
        try:
            prepared = post(
                "/v1/context/prepare",
                {
                    "scope_id": scope_id,
                    "query": expand_query(case["question"]) if args.expand else case["question"],
                    "max_bytes": args.max_bytes,
                },
            )
        except (URLError, OSError) as error:
            print(f"连不上 Server（{BASE_URL}）：{error}", file=sys.stderr)
            return 2

        content = (prepared.get("content") or "").lower()
        missing_keywords = [
            keyword for keyword in case["expected_keywords"] if keyword.lower() not in content
        ]
        ok = len(missing_keywords) == 0
        hits += int(ok)

        by_category.setdefault(case["category"], []).append(int(ok))
        rows.append(
            {
                "id": case["id"],
                "scope": case["scope"],
                "category": case["category"],
                "status": prepared.get("status", ""),
                "bytes": len(content.encode("utf-8")),
                "hit": int(ok),
                "missing": ";".join(missing_keywords),
                "question": case["question"],
            }
        )
        mark = "OK  " if ok else "MISS"
        print(f"[{mark}] {case['id']} {case['scope']}  {case['question']}"
              + ("" if ok else f"  缺：{', '.join(missing_keywords)}"))

    with open(args.out, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    print()
    print(f"总召回准确率：{hits}/{total} = {hits / total:.1%}")
    for category, values in sorted(by_category.items()):
        print(f"  {category}: {sum(values)}/{len(values)} = {sum(values) / len(values):.0%}")
    print(f"明细已写入 {args.out}")
    return 0 if hits == total else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
