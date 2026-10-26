# Experience 演示 · 踩坑到复用

> 脚本：`experiments/experience_demo.py` ｜ 全程不需要大模型

---

## 为什么做这个

课设里最贵的成本是**重复踩同一个坑**：这学期踩过，下学期换门课又踩一遍；你踩过，队友接着踩。
Experience 把"踩坑"变成一条**需要审核才能复用**的经验，而不是散落在聊天记录里的一句话。

---

## 流程与实测输出

| 步骤 | 调用 | 状态 |
|---|---|---|
| 1 | `POST /v1/sources/content`（kind=task-outcome） | 证据落库 `pitfall-edd4ac51` |
| 2 | `POST /v1/experience/propose` | 进入 Review Inbox，`pending`，`version=1` |
| 3 | `POST /v1/candidates/approve` | `status: approved`，生成不可变版本 |
| 4 | `POST /v1/context/prepare` | `status: ready`，经验被召回 |

终端输出：

```
[1] 踩坑证据已记录：pitfall-edd4ac51
[2] 经验已进入待审队列：candidate=cand_b0d539... version=1
[3] 审核通过：{"status": "approved", ...}
[4] 召回验证：status=ready 命中=是
```

---

## 三个设计要点

1. **生成与审核分离**
   `propose` 只负责提交，approve 才产生版本。未审核的内容**不进入召回**——这是有意为之：
   模型的推测不能直接变成团队共识。

2. **expected_version 防并发覆盖**
   审核时必须带上版本号。两个人同时审同一条，后到的会失败，而不是悄悄覆盖。

3. **经验的结构是固定的四段式**
   `situation / action / outcome / lesson`。强制结构让经验可比较、可检索，
   而不是一段散文。

---

## 复现

```powershell
cd ob-competition\experiments
..\.venv\Scripts\python.exe experience_demo.py
```

---

## 演示视频里怎么用

接在 Handoff 之后（约 1:30 处），作为"交接之后还会留下什么"：

> 交接完成不等于结束。这次踩的坑会被写成一条经验，审核通过后，下次任何人问起，它自己会浮上来。
