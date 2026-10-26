---
name: zenmux-model-integration
description: 通过Zenmux(OpenRouter)集成新AI模型到CoachAI平台。处理数据库定价、Edge Function路由、前端配置、图标、积分计算等全流程。当用户说"集成模型"、"新增模型"、"接入模型"时触发。
---

# Zenmux 模型集成 Skill

通过 Zenmux (OpenRouter) 将新 AI 模型集成到 CoachAI 平台的完整工作流。

## 执行指南

本 Skill 的操作步骤以下面两份指南文档为权威依据：

**主指南 — 模型集成全流程：**
```
D:\Study\MakerOS\Devbook\模型新增\通过Zenmux集成模型指南.md
```

**子指南 — 推理内容显示适配（推理模型必做）：**
```
D:\Study\MakerOS\Devbook\模型新增\推理模型开启推理内容显示指南.md
```

**执行前必须先读取主指南的完整内容**，然后严格按照指南中的步骤顺序执行。如果模型支持推理输出，还需读取子指南并执行推理适配步骤。不要凭记忆操作，每次都要读取最新版本。

## 触发方式

用户会提供类似以下格式的模型信息：

```
集成 x-ai/grok-4 模型，要求如下：
  模型名称: x-ai/grok-4
  模型价格: 输入$3/输出$15.00 → 1K tokens输入150积分/1K tokens输出600积分
  model_provider: x-ai
  model_display_name: Grok 4
  min_plan_required: plus
  model_category: advanced
  模型图标: '/Users/todaylab/Dev/xingeti/public/logos/grok.svg'
```

如果用户只给了模型名称没给完整信息，主动询问缺失的字段。

## 必需输入字段

| 字段 | 说明 | 示例 |
|------|------|------|
| 模型名称 (model_name) | Zenmux 上的模型 ID | `x-ai/grok-4` |
| 模型价格 | USD 价格和对应积分 | 输入$3/输出$15 → 150/600积分 |
| model_provider | 模型提供商 | `x-ai` |
| model_display_name | 前端显示名称 | `Grok 4` |
| min_plan_required | 最低订阅等级 | `free` / `plus` / `pro` |
| model_category | 模型类别 | `basic` / `advanced` |
| 模型图标路径 | SVG 图标文件路径 | `/logos/grok.svg` |

## 可选输入字段

| 字段 | 说明 | 默认值 |
|------|------|--------|
| provider 限定 | Zenmux provider 限制 | 不限定（自动选择） |
| sortOrder | 前端排序顺序 | 根据现有模型顺序递增 |
| outputRatio | 输出 token 倍率估算 | `2.0` |
| 推理强度 (reasoning effort) | 推理模型的思考深度 | `low` / `medium` / `high`，默认不设置 |

## 执行流程

收到用户的模型集成请求后，按以下流程执行：

### 第一步：读取指南
读取 `D:\Study\MakerOS\Devbook\模型新增\通过Zenmux集成模型指南.md` 的完整内容。

### 第二步：确认信息
向用户确认所有必需字段是否齐全，列出将要执行的改动计划。

### 第三步：按指南顺序执行

严格按照指南中的步骤顺序：

1. **数据库配置**（指南步骤2）
   - 添加 `model_credit_pricing` 记录
   - 获取最新触发器代码，添加兜底定价后更新
   - 验证配置

2. **Edge Function 更新**（指南步骤3）
   - 读取 `supabase/functions/chat/index.ts` 当前代码
   - 添加模型路由逻辑（在模型判断 if 链中添加新模型前缀）
   - 如需 provider 限定，添加对应配置
   - 更新 `StreamContentCollector` 兜底估算
   - 更新兜底积分计算

3. **前端配置更新**（指南步骤4/5）
   - 更新 `src/config/models.ts`
   - 更新 `src/services/modelService.ts`
   - 更新 `supabase/functions/shared/credit-calculation.ts`（三个方法）
   - 更新 `src/components/credits/CreditRecords.tsx` 模型名称映射
   - 更新 `src/components/settings/panels/CreditsPanel.tsx` 模型名称映射
   - 更新 `src/services/agentService.ts` 模型名称映射
   - 更新 `src/components/shared/ModelShowcase.tsx` 模型展示墙（价目/模型清单）
   - 更新 `src/pages/CreditsRulePage.tsx` 积分规则页 MODEL_CREDITS（价格须与数据库一致）

4. **视觉（图片识别）能力核实与配置**（必做，勿凭前代推测）
   - 用 ZenMux 官方 API 查模型输入模态（这是唯一可信来源，模型详情网页是 SPA 抓不到数据）：
     ```bash
     curl -s https://zenmux.ai/api/v1/models | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{const m=JSON.parse(s).data.find(x=>x.id==='<模型ID>');console.log(m.input_modalities, m.capabilities)})"
     ```
   - `input_modalities` 含 `"image"` → 开启视觉，改两处：
     - 后端 `supabase/functions/chat/index.ts` 的 `supportsVision` 数组（注意它用 `includes` 子串匹配，如已有 `'grok-4'` 会自动覆盖 `grok-4.5`，覆盖到就不用加）
     - 前端 `src/config/models.ts` 的 `VISION_MODEL_IDS`（精确匹配 Set，**必须显式加新 ID**，不存在子串覆盖）
   - 仅 `"text"` → 两处都不加，且 `modelService.ts` / `ModelShowcase.tsx` 的描述文案不得出现"支持图片识别 / 多模态"
   - 教训（2026-07-17）：Qwen 3.5 Plus 支持视觉，但替代它的 Qwen 3.7 Max 仅文本；前代能力不可继承，必须逐个查 API
   - 顺带记录 API 返回的 `capabilities.reasoning`，供下面推理适配步骤判断

5. **图标配置**（指南步骤5/6）
   - 在 `src/components/icons/ModelIcons.tsx` 添加内联 SVG
   - 如需要，添加图标预加载

6. **推理内容显示适配**（指南步骤8，推理模型必做）
   - 读取子指南 `D:\Study\MakerOS\Devbook\模型新增\推理模型开启推理内容显示指南.md`
   - 检查新模型 ID 是否已被现有前缀匹配覆盖（如 `openai/gpt-5.4` 被 `openai/gpt-5` 覆盖）
   - 如已覆盖：仅按需调整推理强度（effort）
   - 如未覆盖：按子指南完整执行 6 个步骤
   - 涉及文件：`chat/index.ts`、`agentService.ts`、`ChatPage.tsx`

7. **构建验证**（指南步骤7）
   - 执行 `npm run build` 验证无错误

### 第四步：部署
- 提醒用户部署 Edge Function：`supabase functions deploy chat --project-ref hkgavesxckhwrcnmpkkc`
- 提醒用户提交代码

### 第五步：输出验证清单
按指南中的检查清单，输出待验证项目供用户逐项确认。

### 第六步：同步到 xhsnote
本技能**只在母版 xingeti 上执行**。母版验证通过后，用 `model-lineup-sync` 技能把模型阵容推到副本 xhsnote（含数据库定价行与触发器分支）。不要在 xhsnote 上直接跑本技能——两个仓库已分叉，且 xhsnote 有刻意豁免的模型清单，详见 `~/.Codex/skills/model-lineup-sync/SKILL.md`。

## 关键注意事项

1. **先数据库后代码** — 数据库配置必须在代码修改前完成
2. **触发器必须读最新版** — 每次都要先查询当前触发器代码，不能直接用指南中的示例
3. **两个积分记录文件都要更新** — `CreditRecords.tsx` 和 `CreditsPanel.tsx` 各自维护独立的映射表
   - **另有两处价目/模型清单易漏** — `ModelShowcase.tsx`（展示墙）和 `CreditsRulePage.tsx`（积分规则页）也要同步添加新模型，价格须与数据库一致
4. **消息历史不重复** — 新模型使用完整 messageHistory，不额外添加用户消息
5. **生产数据库写操作** — 执行 SQL 前必须先告知用户具体内容，等确认后再执行
6. **每次执行都读指南** — 指南可能已更新，不要依赖缓存的记忆
7. **视觉能力必须查 ZenMux API** — `https://zenmux.ai/api/v1/models` 的 `input_modalities` 是唯一依据，禁止按前代模型或厂商惯例推测（Qwen 3.7 Max 就是前代有视觉、新代没有的反例）
8. **兜底定价的 if/CASE 链顺序** — 新模型 ID 是旧 ID 的"延长串"时（如 `grok-4.5` 含 `grok-4`、`glm-5.2` 含 `glm-5`），新分支必须插在旧的模糊匹配**之前**，涉及 `credit-calculation.ts` 两个方法和数据库触发器 CASE
