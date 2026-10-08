# 时间线数据契约

这是自定义的策划数据，不是 HyperFrames 原生 schema。Agent 把它转换为当前 HyperFrames 工程与场景时间。该分离让更换文案、素材和片长时仍可复用场景。

## 字段

根字段包含 `product`、`fps`、`width`、`height`、`durationFrames`、`language`、`music`、`scenes`。

`music` 可以为 `null`，或者包含本地 `path` 与 `beatFrames`。没有音乐时不宣称自动卡点。若用户给出音轨，先分析该音轨，再写拍点；不得从示例拷贝伪拍点。

每个 scene 包含：

- `id`：稳定唯一标识，修改其他场景时保持不变。
- `type`：opening、brand、kinetic-title、orbit、chapter、ui-demo、value-card、landscape-card、reveal 或 end-card。brand 用于品牌揭示，orbit 用于品牌能力概览，value-card 用于价值总结。
- `startFrame`、`durationFrames`：非负整数起点与正整数时长。
- `copy`：要实际出现的画面文字。
- `assets`：本地素材路径列表；没有素材时为空。
- `sourceIds`：事实或素材记录中对应的 ID；纯叙事连接句可为空。
- `action`：可选的镜头／点击说明，如目标归一化坐标与缩放倍率。

主场景使用相邻而不重叠的区间，切换特效发生在场景内部。若实现改为重叠转场，显式记录重叠帧数并修订时长计算，不能靠隐式延长场景解决。

## 90 秒演示时间线

| 起始帧 | 时长帧 | 秒区间 | 类型 | 内容建议 |
|---:|---:|---|---|---|
| 0 | 120 | 0–4 | opening | 用户产品名 |
| 120 | 150 | 4–9 | kinetic-title | 一个核心价值 |
| 270 | 60 | 9–11 | chapter | 能力一 |
| 330 | 360 | 11–23 | ui-demo | 动作一与真实结果 |
| 690 | 60 | 23–25 | chapter | 能力二 |
| 750 | 360 | 25–37 | ui-demo | 动作二与真实结果 |
| 1110 | 60 | 37–39 | chapter | 能力三 |
| 1170 | 360 | 39–51 | ui-demo | 动作三与真实结果 |
| 1530 | 330 | 51–62 | landscape-card | 结果与价值 |
| 1860 | 240 | 62–70 | reveal | 压轴主张 |
| 2100 | 330 | 70–81 | ui-demo | 压轴主张的证据 |
| 2430 | 270 | 81–90 | end-card | 品牌与 CTA |

这是完整性示例，不是固定分镜，也没有根据特定配乐卡点。

## 数据验收

每个 ID 唯一；场景按起始帧排序；首场从 0 开始；最后一场结束等于 `durationFrames`；默认场景之间没有空隙。素材路径实际存在；每项功能、数字或性能主张都有 source ID；音乐覆盖成片时长或有明确的剪裁／淡出方案。

每个 scene 单独保留内部相对时间，主时间线只负责放置。访问场景局部时间时使用 `globalFrame - startFrame`，不要把绝对帧数重复传给局部动画。

## 配乐版本记录

music 可额外记录 title、artist、source、license、bpmEstimate、bpm、tempoMethod、cueFrames 与 editPath。beatFrames 应由实际音轨得出；若音轨已按网格处理，记录源估算速度、目标速度与相位，不能只写一个假定 BPM。复杂源区间／增益包络放 music-edit.json，editPath 指向它。

内部 UI 焦点宜记录实际素材与裁切矩形、局部时间、归一化坐标和缩放倍率。案例完整时间线见 mole-english-case.md。
