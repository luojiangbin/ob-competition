# experiments · 召回实验

三个文件构成一条可复现的实验链：

```
seed_data.json   5 个课设场景 × 5 条记忆（约束/决策/踩坑/下一步）
seed.py          建 Scope + 写入记忆，输出 scopes.json
evaluate.py      用 20 条跨会话问题测召回，输出 results.csv
```

## 前置

Server 必须在跑（另开一个终端，别关）：

```powershell
cd $HOME\powercontext-demo
powercontext server run --env-file .env
```

## 跑实验

```powershell
cd ob-competition\experiments

# 1. 灌数据（幂等，重复跑不会重复建 Scope）
python seed.py

# 2. 测召回
python evaluate.py
```

## 输出怎么看

```
总召回准确率：18/20 = 90.0%
  constraint: 10/10 = 100%
  decision: 5/5 = 100%
  pitfall: 3/5 = 60%
```

- `constraint` 低 → 约束类记忆没被召回，检查写入的 `kind` 和措辞
- `pitfall` 低 → 踩坑记录太口语化，和问题的字面重合度不够
- 某条一直 MISS → 看 `results.csv` 的 `missing` 列，缺哪个关键词

## 为什么不用大模型

`/v1/context/prepare` 返回的就是"新会话能看到的上下文"。
只要期望关键词出现在这段文本里，就证明**信息被正确召回了**——这一步不需要任何模型 API，
判定完全确定，重复跑结果一致。这也是答辩时最有说服力的一点：**指标可复现，不靠调参**。

## 对照组（A 组）怎么跑

A 组 = 不给上下文，靠人肉复述。两种做法：

1. 人工：新开一个空白会话，凭记忆回答 20 题，记录答对数和耗时（最真实，答辩可信度高）
2. 脚本：把 `--max-bytes 1` 传给 evaluate.py，等价于"上下文为空"

建议至少手工跑一遍 A 组并录屏，比纯数字更有说服力。

## 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `连不上 Server` | Server 没起 | 先 `powercontext server run` |
| 全部 MISS | 写到了不同 Scope | 删掉 `scopes.json` 重新 `seed.py` |
| `status: empty` | 查询词和记忆没有字面重合 | 换更贴近记忆原文的提问，或配置向量检索 |
| 中文乱码 | 控制台编码 | 已用 `PYTHONIOENCODING=utf-8` 兜底 |
