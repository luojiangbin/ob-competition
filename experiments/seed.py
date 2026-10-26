"""把 5 个课设场景灌入 PowerContext（每个场景一个 Scope）。

用法：
    python seed.py
    python seed.py --dry-run      # 只校验数据，不联网

环境变量：
    POWERCONTEXT_URL    默认 http://127.0.0.1:8000
    POWERCONTEXT_TOKEN  服务端开了认证时填

输出：
    scopes.json   场景 key -> scope_id 映射，后续 evaluate.py 要用
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN = os.environ.get("POWERCONTEXT_TOKEN")
HERE = Path(__file__).resolve().parent


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    return headers


def post(path: str, payload: dict) -> dict:
    request = Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=_headers(),
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST {path} -> HTTP {error.code}: {detail}") from error


def get(path: str) -> dict:
    request = Request(f"{BASE_URL}{path}", headers=_headers(), method="GET")
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只校验数据，不联网")
    parser.add_argument("--data", default=str(HERE / "seed_data.json"))
    args = parser.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    scopes = data["scopes"]
    version = data.get("version", 1)
    total = sum(len(s["memories"]) for s in scopes)
    print(f"场景 {len(scopes)} 个，记忆 {total} 条（数据版本 v{version}）")

    if args.dry_run:
        for scope in scopes:
            print(f"  {scope['key']}: {scope['title']} ({len(scope['memories'])} 条)")
        print("dry-run 通过，数据格式没问题。")
        return 0

    try:
        get("/health/live")
    except (URLError, OSError) as error:
        print(f"连不上 Server（{BASE_URL}）：{error}", file=sys.stderr)
        print("先另开一个终端跑：powercontext server run --env-file .env", file=sys.stderr)
        return 2

    mapping: dict[str, str] = {}
    for scope in scopes:
        created = post(
            "/v1/scopes",
            {
                "title": scope["title"],
                "summary": scope["summary"],
                "idempotency_key": f"ob-competition-v{version}-{scope['key'].lower()}",
            },
        )
        scope_id = created["scope_id"]
        mapping[scope["key"]] = scope_id

        for memory in scope["memories"]:
            post(
                "/v1/memory/remember",
                {
                    "scope_id": scope_id,
                    "kind": memory["kind"],
                    "text": memory["text"],
                    "reason": memory["reason"],
                },
            )
        print(f"  {scope['key']} -> {scope_id}  写入 {len(scope['memories'])} 条")

    (HERE / "scopes.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("已写出 scopes.json")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
