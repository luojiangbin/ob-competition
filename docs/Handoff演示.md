# Handoff 演示 · 队友交接四步流程

> 脚本：`experiments/handoff_demo.py` ｜ 全程不需要任何大模型

---

## 为什么做这个

课设交接是学生协作里最痛的一环：队友接手时，你嘴上说的"就那样，你看着办"，等于没说。
PowerContext 的 Handoff 把交接变成**有边界、有版本、可确认**的四步流程。

---

## 流程与实测输出

| 步骤 | 调用 | 作用 | 实测结果 |
|---|---|---|---|
| 0 | `POST /v1/sources/content` | 写入"交接时的状态"作为边界证据 | `handoff-boundary-7cdfd845` |
| 1 | `POST /v1/work/contracts/create` | 工作契约：目标、边界、完成标准、授权范围 | 创建成功 |
| 2 | `POST /v1/work/handoffs/prepare-current` | 生成**临时**交接包（未固化） | 生成成功 |
| 3 | `POST /v1/handoff/commit` | 固化成不可变版本 | `handoff/handoff@3` |
| 4 | `POST /v1/handoff/continue` + `acknowledge` | 接手方读取并确认（状态/能力/授权三项检查） | `status: resolved` |
| 5 | `POST /v1/work/outcomes/record` | 记录结果与未完成项 | `partial` |

终端输出：

```
[0] 边界证据写入 Source：handoff-boundary-7cdfd845
[1] 工作契约已创建
[2] 临时交接包已生成（未固化）
[3] 交接已固化：handoff/handoff@3
[4] 接手方已确认：{"resolution": {"status": "resolved", ...}}
[5] 结果已记录：{"kind": "task-outcome", ...}
四步流程完成：Work Contract -> Prepared -> Committed -> Ack -> Outcome
```

---

## 三个设计要点（答辩可讲）

1. **临时 vs 固化分离**
   `prepare` 只生成临时包，`commit` 才产生不可变版本。避免"随手一存就成了里程碑"。

2. **接手方必须确认，且要过三项检查**
   `receiver_checks` 要求 `live_state` / `capability` / `authorization` 都为 `confirmed`，
   否则确认会被拒绝。这防止"我以为你能接手"的误判。

3. **结果不等于成功**
   `status` 支持 `succeeded / partial / blocked / failed / cancelled / unknown`。
   本例故意记成 `partial`，并留下 `remaining_work`——真实课设很少一次做完。

---

## 复现

```powershell
cd ob-competition\experiments
..\.venv\Scripts\python.exe handoff_demo.py
```

每次运行会生成新的 `run_id`，所以可以反复跑而不冲突。

---

## 演示视频里怎么用

放在 0:50–1:30 那段之前，作为"不只是问答"的证据：

> 这是队友接手时发生的事——不是甩一句"你看着办"，而是一份带边界、带完成标准、带确认回执的交接单。

现场跑一次 `handoff_demo.py`，终端刷出五个步骤，比讲十句都有说服力。
