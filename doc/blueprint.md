# T-skills 技能体系蓝图（Blueprint）

> 面向「独立开发者做产品」的个人技能集 **T-skills**（🐯）。
> T-skills 由 [Waza](https://github.com/tw93/Waza) 整体改造而来，已自带 8 个技能并发布 v0.1.0。
> 本文是 T-skills 的**前进计划**：在已有 8 技能的基础上补齐独立开发者的缺口。

---

## 0. 现状（v0.1.0 已上线）

仓库：https://github.com/tanglei168/T-skills · 安装：`npx skills add tanglei168/T-skills -a claude-code -g -y`

- **已自带 8 技能**（源自 Waza，已改名 T-skills + 🐯 标记，可自由编辑）：`think` `design` `check` `hunt` `write` `learn` `read` `health`。
- **完整 1-7 层机制**（源 / 技能 / 规则 / 校验 / 生成 / 打包 / CI）全部保留，见 [waza-anatomy.md](waza-anatomy.md)。
- **首行标记**：🐯（原 Waza 是 🥷），由 `verify_skills.py` 的 `TIGER_PREFIX` 检查强制。

### 策略变更（重要）

最初设想是「做一个**独立层去引用** Waza、只新建缺口」。实际落地时改为 **整体 fork Waza 为 T-skills**。差别：

| | 旧设想（已弃） | 现状 |
|---|---|---|
| 8 个通用技能 | 安装 Waza，外部引用 | **T-skills 自己拥有**，可直接改 |
| 新增技能 | 放在独立层 | 直接加进 T-skills 的 `skills/` |
| 维护 | 跟随 Waza 升级 | 自己掌控，按需从 Waza 同步 |

好处：完全自主，改 prompt / 加技能 / 调规则都不受上游约束。代价：要自己维护，且上游 Waza 的更新需手动合并。

---

## 1. 设计 DNA（继承自 Waza，T-skills 照此扩展）

| # | 原则 | 含义 |
|---|------|------|
| 1 | **Outcome-first** | `SKILL.md` 开头先写 Outcome Contract（目标产出 / 何为完成 / 凭什么证据 / 产出长什么样），流程放后面。 |
| 2 | **Fat skill vs script/rule** | 需要判断、追问、随上下文变化 → skill；同入同出、只校验列举 → script 或 rule。 |
| 3 | **具体可路由的 frontmatter** | `description` 具体、可触发、带 `Not for …`；配 `when_to_use`、`dispatch_intent`。 |
| 4 | **🐯 输出标记** | 每个技能首行内联带 🐯，不单起一段。 |
| 5 | **Mode 升降档** | 轻量默认，复杂升档；多模式先 Mode Picker。 |
| 6 | **Gotchas 表** | 每行 = 一次真实翻车 → 一条规则。 |
| 7 | **Durable Context Preflight** | 记忆只作背景；当前代码/日志/实测/远端状态永远覆盖记忆。 |
| 8 | **证据 > 自信** | 引用 `file:line`、跑命令贴输出。 |
| 9 | **硬停 / 安全闸** | 破坏性、对外动作需当回合显式授权。 |
| 10 | **手动串联** | 技能做完就停，等用户决定下一步。 |

> `rules/anti-patterns.md` 的 35 条跨技能护栏整套保留，作为 always-on 行为底座。

---

## 2. 已自带的 8 技能（源自 Waza）

> 这 8 个现在是 T-skills 自己的技能。下表给定位、流程要点，以及在独立开发者工作流里的角色。

| 技能 | 核心目标（一句话） | 流程/模式要点 | 工作流角色 |
|---|---|---|---|
| **think** | 把粗想法变成决策完整、可交接的方案 | Lightweight / Full / **Evaluation（Kill-Keep-Pivot）** 三档；攻击角度压测；handoff 无占位符 | 思考 + **商业决策**（配 business-frameworks，§5.4） |
| **design** | 有主张的生产级 UI，不出通用模板 | Quick-Fix / 截图迭代 / 锁方向（5 问）/ 审美复查 | 设计 |
| **check** | 基于 diff 与实证的评审 / 发布 / 维护者动作 | 工作树安全 preflight → Mode Picker → 范围漂移检查 → 签收 | 验证 |
| **hunt** | 先用一句话定位根因，再动手修 | 根因门槛 → 证据阶梯 → bisect → 爆破搜同类 | 运维调试（调试半） |
| **write** | 去 AI 味、保留本意 | 双语 / release notes / 公开回复 / 连贯性 / 推文 | 写作 |
| **learn** | 六阶段把材料沉淀成成稿 | collect→digest→outline→fill→refine→publish | 市场研究的沉淀底座 |
| **read** | 抓任意 URL/PDF，按意图产出 | 隐私优先抓取级联；抓回内容当不可信数据 | 市场研究的抓取底座 |
| **health** | 审 AI agent 配置与 AI-coding 可维护性 | 五层框架；预算感知，summary 先行 | 运维调试（配置半） |

**结论**：写作 / 思考 / 设计 / 验证 / 调试 / 配置审计 已被这 8 个覆盖；read/learn 作为研究底座。独立开发者还缺：**市场研究、实现编排、生产运维**，外加给 think 补一份**商业框架**。

---

## 3. Persona 与主工作流

**Persona**：一个人（或极小团队）从想法到上线再到运营一个软件产品。重心是「做出并运营一个产品」。

```
                    ┌────── 横切：think（想清楚 + 商业判断）· write（说清楚）──────┐
                    │                                                            │
   想法 ──▶ survey ──▶ think ──▶ design ──▶ build ──▶ check ──▶ 上线 ──▶ ops
         (市场研究)  (决策)     (设计)    (实现)    (验证)            (运维)
            │                                          │                  │
         read/learn 做底座                          check 把关          hunt 回根因 · health 审配置
```

斜体的 `survey` / `build` / `ops` 是待新增技能；其余已自带。

---

## 4. 待新增的缺口

| 缺口 | 技能 | 形态 | 一句话 |
|---|---|---|---|
| 市场研究 | **`survey`** | 🆕 新技能（read/learn 作底座） | 把「值不值得做」变成有来源的判断，不是资讯综述 |
| 实现编排 | **`build`** | 🆕 新技能（薄约束，非编码配方） | 守范围、小步验证、忠实计划地落地 |
| 生产运维 | **`ops`** | 🆕 新技能（平台无关） | 部署/监控/事故/回滚/成本，调试仍回 hunt |
| 商业决策 | `think` + reference | 📄 一份 reference | 给 think 补商业弹药，不另起技能 |

加 3 个技能会让 T-skills 从 8 → 11，触及继承自 Waza 的「8 技能硬上限」——见 §6 待拍板。

---

## 5. 新技能一页草案

### 5.1 `survey` — 市场研究 ✅

- **定位**：把「这个市场 / 需求 / 竞品值不值得做」变成**有证据的判断**。产出是**决策**，不是综述（区别于 `learn`/`gather`）。
- **Outcome Contract**：市场规模与结构、真实需求信号、竞品格局与空位、付费意愿、进入壁垒与分发路径。**完成标准**：能支撑一个 go/no-go 或定位决策，每个关键结论有来源。
- **触发**：市场调研 / 竞品分析 / 有没有人做过 / 有没有需求 / 这个赛道 / TAM / 定价参考 / competitor teardown。
- **Modes**：需求验证（只验真伪）/ 竞品拆解（定位·定价·分发·弱点矩阵）/ 市场结构（TAM·增长·渠道）/ 全景 go/no-go。
- **底座**：用 `read` 抓取，套 `learn` 的 digest 纪律（关键结论 ≥2 独立来源交叉）。
- **Not for**：可发表文章（→ `learn`/`write`）；纯资讯速览；技术方案（→ `think`）。

### 5.2 `build` — 实现编排（薄约束 ⚠️）

- **哲学约束**：Waza 故意不做 implement 技能——「每条规则都是天花板」。`build` 只装**执行纪律**，不写编码配方。
- **Outcome Contract**：按计划交付、每步可验证、范围无漂移的实现过程。**完成标准**：计划项全落地、每增量跑过验证、交 `check` 前自检通过。
- **核心约束**：范围纪律（只做计划内）/ 增量-验证节奏（每小步跑验证，不攒大 diff）/ 计划忠实（不重新争论方向）/ 停止条件（触 3+ 文件方法选择 → `think`；反复修不好 → `hunt`；完成 → `check`）。
- **串联**：`think` → `build` → `check`。

### 5.3 `ops` — 生产运维（平台无关 🔒）

- **边界**：`hunt`=可复现 bug；`health`=AI agent 配置；`ops`=在线产品运行态（部署/密钥/监控/事故/回滚/成本）。
- **Outcome Contract**：可观测、可回滚、事故有预案的运行态。**完成标准**：部署路径/密钥来源/监控信号/回滚步骤明确且经过验证。
- **Modes**：部署就绪（上线前清单）/ 事故响应（先止血回滚，再把根因交给 `hunt`）/ 可观测性 / 成本配额。
- **平台无关**：运行时从 CI 配置、部署脚本、manifest、README 提取实际部署方式，不绑定具体平台。

### 5.4 商业决策 — 并入 think + `references/business-frameworks.md` 📄

`think` 的 Evaluation Mode 已做 Kill/Keep/Pivot 的商业判断，前向选择落在 Propose Approaches。只缺商业弹药。新增一份 reference 供 think 在商业语境引用：单位经济、LTV/CAC、定价模型与实验、build-vs-buy 清单、分发渠道与获客成本、留存/流失判读。

---

## 6. 待拍板：8 技能硬上限

T-skills 的 `AGENTS.md`（继承自 Waza）写着「Eight skills is the hard cap. Do not propose a 9th skill」。加 `survey`/`build`/`ops` 会到 11，与此冲突。这是 Waza 的**编辑约束**，不是技术约束（校验器不强制技能数量，只是 AGENTS.md 的文字）。三个选项：

| 选项 | 做法 | 评价 |
|---|---|---|
| (a) **放开上限**（推荐） | 改 T-skills 的 AGENTS.md，把上限提到 11 或改为「核心 8 + 扩展」 | 最直接；T-skills 是个人工具集，不必守 Waza 的极简主义 |
| (b) 替换 | 用 survey/build/ops 顶掉 8 个里用得少的 | 保持 8，但会丢掉通用能力 |
| (c) 不新建技能 | survey/build/ops 降级为 references/rules | 最省，但丢了自动路由与独立触发 |

推荐 (a)：放开上限并更新 AGENTS.md 的技能清单、`skills/RESOLVER.md`、`rules/t-skills-routing.md`、marketplace（`make regenerate`）。

---

## 7. 落地路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 0 | 搞懂 Waza 机制 + 拆解可复用件 → [waza-anatomy.md](waza-anatomy.md) | ✅ |
| Phase 1 | 整体 fork → T-skills（8 技能 + 🐯 + 全机制），发布 v0.1.0 | ✅ |
| **Phase 2** | 拍板 §6（建议放开 8 上限），改 AGENTS.md / RESOLVER / routing | ⏳ 下一步 |
| Phase 3 | 写 **`survey`** 完整 `SKILL.md` + 三份 reference | 待 |
| Phase 4 | 写 **`build`**（薄约束版） | 待 |
| Phase 5 | 写 **`ops`**（平台无关，部署就绪 + 事故响应） | 待 |
| Phase 6 | 写 `references/business-frameworks.md`，接进 think | 待 |

**每个新技能验收**：能被 `description` 自动路由；有 Outcome Contract；Gotchas 来自真实翻车；与现有技能边界清晰；🐯 标记到位；`python3 scripts/verify_skills.py --root .` 过；`make regenerate` 后 `make verify-generated` 无漂移。

---

## 8. 已确认决策

1. **商业决策**：复用 `think` Evaluation + `business-frameworks.md` reference，不新建技能。✅
2. **市场研究技能定名 `survey`**。✅
3. **`ops` 平台无关**，运行时提取部署方式。✅
4. **形态：整体 fork 为独立仓库 T-skills**（不是引用 Waza 的外部层）。✅
5. **首行标记 🐯**，owner tanglei168，已发布 v0.1.0。✅
6. **后续计划在 T-skills 仓库内推进。** ✅

> 下一步（Phase 2）：先就 §6 的 8 技能上限拍板，再开始写 `survey`。
