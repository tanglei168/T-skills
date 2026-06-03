# 机制解剖：T-skills 继承自 Waza 的工程流水线

> T-skills 由 [Waza](https://github.com/tw93/Waza) 整体改造而来，**完整保留了下文 1-7 层全部机制**（不是裁剪版）。
> 本文记录这套机制的原理，作为 T-skills 的工程参考：知道每个文件是源还是产物、校验器在守什么、改东西要跑什么。

---

## 0. 这份文档给你什么

- 一张**六层结构图**和**数据流**：知道每个文件是源还是产物。
- 一份**可复用 SKILL.md 骨架**（照抄即用）。
- 校验器 `verify_skills.py` 的 **19 项契约**，逐条说明在守什么、T-skills 里怎么改名适配。
- T-skills 的**实际目录结构**与改技能时的校验闭环。

---

## 1. 六层结构

T-skills 不是「8 个 Markdown」，而是一条「源 → 校验 → 生成 → 打包 → 分发」的流水线。

```
① 源（source of truth）          VERSION  +  skills/*/SKILL.md(frontmatter)  +  rules/*.md
        │
② 技能层（latent 判断）          skills/<name>/{SKILL.md, references/, agents/, scripts/}
        │
③ 规则层（always-on 行为）        rules/{anti-patterns, durable-context, english, chinese, t-skills-routing}.md
        │
④ 校验层（确定性契约）            scripts/verify_skills.py  ← skill_checks.py + skill_frontmatter.py
        │                        scripts/check_routing_drift.py（路由一致性 tripwire）
        │
⑤ 生成层（codegen，防漂移）       scripts/build_metadata.py
        │                          └─▶ marketplace.json · package.json · README 安装URL · 安装脚本 TSKILLS_REF · dispatcher.md
        │
⑥ 打包/分发层                    scripts/package-skill.sh + packaging_filter.py + validate_package.py
        │                          └─▶ dist/t-skills.zip（把 8 个 SKILL.md 内联进一个 root SKILL.md）
        │                        npx skills / npm @tanglei168/t-skills / Claude Desktop zip / 插件 marketplace
        │
⑦ CI 门禁                        .github/workflows/{test,release}.yml → 跑 `make test`，发布时 `make package` 上传
```

**核心思想**：凡是「同一份元数据出现在多个分发文件里」，一律用 **codegen 从 VERSION + frontmatter 生成**，再用 `--check` 做漂移检测，而不是靠人肉同步。

---

## 2. 数据流：谁是源，谁是产物

| 文件 | 角色 | 由谁决定 |
|---|---|---|
| `VERSION` | **源** | 人手改（单一版本号源，当前 `0.1.0`） |
| `skills/*/SKILL.md` frontmatter | **源** | 人手写 |
| `rules/*.md` | **源** | 人手写 |
| `.claude-plugin/marketplace.json` | **产物** | `build_metadata.py` 从 VERSION + frontmatter 生成 |
| `package.json`（version / pi.skills） | **产物** | 同上 |
| `README.md` 安装 URL、`setup-*.sh` 的 `TSKILLS_REF` | **产物**（局部） | 同上，pin 到 `vX.Y.Z` |
| `scripts/dispatcher.md` 路由表 | **产物** | 从各 skill 的 `dispatch_intent` 生成 |
| `dist/t-skills.zip` | **产物** | `package-skill.sh` 打包 |

改完源 → `make regenerate` 重写产物 → `make verify-generated` 确认无漂移 → CI 再卡一道。

---

## 3. 一个 SKILL.md 的解剖（照抄骨架）

每个技能都是同一套骨架，顺序固定：

```markdown
---
name: <skill-name>                # 必须等于目录名
description: "<动词开头，40–500 字符，含 'Use when …' 触发线索，含 'Not for …' 排除>"
when_to_use: "<逗号分隔的触发词，中英双语>"
dispatch_intent: "<一句话，给路由表用>"
---

# <Skill>: <一句话目标>

<🐯 首行内联，不单起一段>          # Waza 原本用 🥷，T-skills 用 🐯

## Outcome Contract           # ← 校验器强制：必须含下面四个字段
- Outcome: <目标产出>
- Done when: <何为完成，可执行的判定>
- Evidence: <凭什么证据>
- Output: <产出长什么样>

## <Lightweight / Mode Picker> # 轻量默认，复杂升档；多模式先 Mode Picker
...每个 Mode 有明确激活条件...

## Durable Context Preflight   # ← 链接 rules/durable-context.md + 本技能的覆盖规则

## Gotchas                     # ← 每行 = 一次真实翻车 → 一条规则
| What happened | Rule |
|---|---|

## Output                      # 产出模板（签收格式 / 裁决格式 等）
```

**校验器对它的硬要求**：frontmatter 四字段齐全且无裸冒号、无 `version` 字段；`description` 40–500 字符、动词开头、含 use-when + not-for；正文有 `## Outcome Contract` 且含四字段；提到的子路径真实存在；首行有 🐯（`TIGER_PREFIX`）；链接不悬空、表格管道数正确。

---

## 4. 校验契约：verify_skills.py 的 19 项检查

> T-skills **保留了全部 19 项**（含分发层），把 Waza 专属的几项改名适配。下表标注每项在守什么。

| # | 检查 | 作用 | T-skills 适配 |
|---|---|---|---|
| 1 | `check_skill_files` | 解析 frontmatter、校 🐯、收集描述与触发词 | `TIGER_PREFIX` |
| 2 | `check_description_conformance` | 描述 40–500 字符、动词开头、含 use-when/not-for | 原样 |
| 3 | `check_outcome_contract` | 强制四字段 Outcome Contract | 原样 |
| 4 | `check_durable_context_and_paths` | 指定技能需 Durable Context 段；禁个人家目录路径 | 原样 |
| 5 | `check_references` | SKILL 里提到的子路径必须存在 | 原样 |
| 6 | `check_markdown_links` | 相对链接不悬空 | 原样 |
| 7 | `check_table_pipes` | 表格管道数正确 | 原样 |
| 8 | `check_trigger_overlap` | 跨技能触发词重叠告警 | 原样 |
| 9 | `check_resolver` | 每个技能在 RESOLVER.md 有行 | 原样 |
| 10 | `check_no_root_skill` | 仓库内不得有 root SKILL.md（只打包时生成） | 原样 |
| 11 | `check_rules_files_present` | 必备 rules 文件齐全 | `t-skills-routing.md` |
| 12 | `check_anti_patterns_contract` | anti-patterns 连续编号、措辞通用、无项目名 | 守 `\bT-skills\b` |
| 13 | `check_attribution_leak` | 禁 `Co-Authored-By: Claude` 等 AI 署名 | 原样 |
| 14 | `check_marketplace` | marketplace.json 形状/版本/源路径 | bundle `t-skills`、`t-skills-<skill>` |
| 15 | `check_*_routing_skills` | 路由表枚举所有技能 | `t-skills-routing.md` |
| 16 | `check_*_routing_triggers` | 路由触发词必须在描述里有据 | 同上 |
| 17 | `check_readme_install_command` | README 含 `npx skills add tanglei168/T-skills …` | 已改 |
| 18 | `check_english_coaching_guard` | english.md 约束描述写法 | 原样 |
| 19 | `check_portable_skill_surface` | 扫私有上下文/Sparkle/Homebrew 等泄漏 | 守 `\bT-skills\b` |

> 加新技能时，这 19 项一条都不许破。`make verify-docs` 一次跑全。

---

## 5. 可复用件（T-skills 已全部采纳）

当初为「最小独立仓库」分了「必拿 / 建议拿 / 按需拿」三档；T-skills 直接 fork，**三档全拿了**：

- 🟢 **契约层**：SKILL.md 骨架、`rules/anti-patterns.md`、`rules/durable-context.md`、Outcome-first + Gotchas 写法。
- 🟡 **校验层**：`skill_frontmatter.py`、`skill_checks.py`（全 19 项）、`verify_skills.py`、Makefile 的 smoke 发现、`tests/test_helpers.sh` 工厂。
- 🔵 **分发层**：`build_metadata.py` codegen + marketplace/package.json、`package-skill.sh` + `packaging_filter.py` + `validate_package.py`、`check_routing_drift.py`、`.github/workflows/{test,release}.yml`、`packaging.allowlist`。

---

## 6. T-skills 实际目录结构

```
T-skills/
├── VERSION                       # 0.1.0
├── Makefile                      # test / regenerate / package
├── AGENTS.md (CLAUDE.md 软链)     # 项目指南（含 8 技能上限——见 blueprint §6 待放开）
├── skills/
│   ├── RESOLVER.md
│   └── {think,design,check,hunt,write,learn,read,health}/SKILL.md
├── rules/
│   ├── anti-patterns.md · durable-context.md · english.md · chinese.md
│   └── t-skills-routing.md
├── scripts/                      # 校验 + 生成 + 打包（全套）
├── tests/                        # 各 surface 一个 smoke + python 单测
├── doc/                          # ← 本规划文档（blueprint.md + 本文）
└── .github/workflows/            # test.yml + release.yml
```

> `doc/` 不进打包产物（`packaging.allowlist` 默认拒绝），也不被 `verify_skills.py` 扫描，是纯开发期文档。

---

## 7. 改技能时的校验闭环

```bash
python3 scripts/verify_skills.py --root .   # 19 项契约
make regenerate && make verify-generated     # codegen 无漂移
make verify-routing                          # 路由一致
make package                                 # 打包 + validate（动分发时）
make test                                    # 全套（CI 同款，需 jq/shellcheck/pytest）
```

后续计划（写 `survey`/`build`/`ops` + 放开 8 技能上限）见 [blueprint.md](blueprint.md) §6–§7。
