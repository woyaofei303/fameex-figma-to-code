# FameEX Figma to Code

将指定的 Figma 节点落地到 FameEX 前端工程，并按真实仓库规则完成组件复用、多语言、业务边界和浏览器验证。

这份 README 面向使用者。Codex 的执行规则仍以 [`SKILL.md`](./SKILL.md) 为准；README 可以和 Skill 共存，但不会被 Codex 自动加载，因此不会增加日常任务的上下文消耗。

## 适用场景

- 从带 `node-id` 的 Figma Design 链接实现新页面或组件。
- 重新审查已经完成的 Figma-to-Code 分支，校正视觉、交互和工程问题。
- 在 `fameex-web` 中判断 Input、Select、Button、Checkbox、Icon 和图片应该复用、适配、提升还是保留在页面内。
- 补齐前端文案的简体中文 i18n，并把其他语言交给翻译人员。
- 在接口或业务合同不完整时，避免伪造账号、资格、库存、提交成功或其他生产状态。

## 准备与安装

使用前需要：

- 可运行 Codex，并能发现本地 Skill。
- 能访问目标 FameEX Git worktree。
- 对目标 Figma 文件具有读取权限。
- 本机有 Python 3 和 `npx`。
- 运行时可用 `figma`、`figma-implement-design`、`playwright` 和 `verification-before-completion`；缺失时 Skill 会按安全顺序检查或补齐兜底依赖。

首次安装到 Codex：

```bash
git clone ssh://git@github.com/woyaofei303/fameex-figma-to-code.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/fameex-figma-to-code"
```

如果目标目录已经存在，不要覆盖。先检查来源、分支和本地改动，再决定更新方式。

当前维护环境区分两个路径：

```text
源码仓库：/Users/julian/fameex-figma-to-code
运行时 Skill：/Users/julian/.codex/skills/fameex-figma-to-code
```

在当前机器上先修改源码仓库，验证并提交后，再按需同步运行时文件。通过整仓 clone 安装时 README 会一起存在，但 Agent 只会按触发规则加载 `SKILL.md`。

## 快速使用

实现新页面：

```text
使用 $fameex-figma-to-code 实现这个界面：
<带 node-id 的 Figma Design 链接>
```

审查已有实现：

```text
使用 $fameex-figma-to-code 审查当前分支已有的 Figma-to-Code 实现：
<带 node-id 的 Figma Design 链接>

目标路由：<可选>
目标文件：<可选>
```

示例：

```text
使用 $fameex-figma-to-code 实现这个界面：
https://www.figma.com/design/...?...&node-id=12645-358
```

## Skill 会做什么

Skill 按七个阶段执行：

1. 确认仓库、worktree、分支、目标路由、Figma 节点和语言命名空间。
2. 获取同一节点的结构化设计信息和截图，并按需读取变量和原始素材。
3. 映射真实路由、相邻实现、组件库、Icon、服务、状态和 i18n。
4. 按可独立验证的切片实现，不从 Figma 猜测接口或业务状态。
5. 在真实浏览器中检查指定视口、响应式、交互、素材和控制台。
6. 对改动范围执行格式化、测试、类型检查、i18n 和 Git Diff 校验。
7. 汇总复用决策、验证结果、截图证据和待确认业务问题。

## FameEX 工程规则

### 组件优先复用

按以下顺序查找：

1. 当前应用的组件系统，例如 `@fameex/ui`。
2. 当前应用的共享组件、Hook 和状态实现。
3. 相邻业务页面的已有模式。
4. 页面内实现。

每个控件或资源归到一种处理方式：

- `reuse`：现有能力直接满足需求。
- `adapt`：复用现有能力，通过公开属性、组合或局部样式适配。
- `promote`：语义稳定并有跨页面复用价值，提升到共享包。
- `local`：业务或页面属性明显，保留在当前功能内。

### Icon 和图片

- 先检查 `packages/icon/output/icon-list.json` 和 `packages/icon/svg-files/**`。
- 已有合适 Icon 时直接复用。
- 找不到合适 Icon 时先使用 Figma 原始资源，不手画近似 SVG，也不引入第三方 Icon 包。
- 通用且可能跨页面复用的 Icon 可以提升到 `packages/icon`。
- Banner、插画、装饰图和强业务素材通常保留在页面资源目录。

### 多语言

- 页面可见文案、提示、校验、状态、无障碍标签和 Metadata 都进入 i18n。
- 默认只新增或修改简体中文 `zh-CN` / `zh_CN`。
- 不自动生成英文、机器翻译、其他语言占位文件或复制中文。
- 其他语言由翻译人员维护。

### 业务边界

Figma 用于确认视觉和交互意图，不作为接口或权限合同。

没有真实接口、PRD 或仓库合同支持时，不实现或伪造：

- 提交和变更结果。
- 用户等级、UID、资产或余额。
- 资格、库存、审核和发货状态。
- 权限、枚举和跳转目标。

涉及地址、账号、证明材料等敏感信息时，如果提交合同尚未确认，先停止提交能力并报告缺失合同。继续完成视觉页面时，只能依据设计证据、仓库约定或用户确认选择隐藏或禁用输入和 CTA；不得留下只能失败或伪造成功的操作。

## 内置检查脚本

### 组件和资源复用候选

```bash
SKILL_DIR="/Users/julian/fameex-figma-to-code"

/usr/bin/python3 "$SKILL_DIR/scripts/audit_reuse.py" \
  --repo-root /Users/julian/fameex-web \
  --limit 40 \
  /Users/julian/fameex-web/apps/web/src/apps/VipGift
```

脚本只负责列出候选，最终仍需结合语义判断 `reuse`、`adapt`、`promote` 或 `local`。

### i18n 引用完整性

```bash
SKILL_DIR="/Users/julian/fameex-figma-to-code"

/usr/bin/python3 "$SKILL_DIR/scripts/audit_i18n_lookups.py" \
  --namespace-json /absolute/path/to/zh-CN/namespace.json \
  --source /absolute/path/to/page.tsx \
  --source /absolute/path/to/feature-directory \
  --key explicit.dynamic.key \
  --json
```

动态或模板 key 不会被猜测，需要用可重复的 `--key` 参数显式补充。

### 缺失依赖补齐

```bash
SKILL_DIR="/Users/julian/fameex-figma-to-code"
/usr/bin/python3 "$SKILL_DIR/scripts/bootstrap_dependencies.py" \
  --dependency <fallback-name> \
  --json
```

脚本不会覆盖已存在的 Skill 目录。只有四项能力全部缺失时才省略 `--dependency`。详细规则见 [`references/dependency-bootstrap.md`](./references/dependency-bootstrap.md)。

## PR-01982 实际案例

这个 Skill 已用于重新审查 FameEX Web 的 VIP 页面，包括：

```text
/zh-CN/VIP
/zh-CN/VIP/gift
/zh-CN/VIP/manager
```

礼包页审计前视觉已经接近设计，但存在以下问题：

- 无用户数据时默认显示 VIP3。
- 达到 VIP3 被直接解释为已获得礼包资格。
- 没有真实提交接口时仍收集姓名、电话、地址和 Telegram。
- 前端本地状态模拟提交成功。

审计后：

- 访客显示 VIP0。
- VIP3 只表示达到等级门槛，资格和发放仍待确认。
- 五个敏感信息输入和 CTA 从可交互改为禁用。
- Input 继续复用 `@fameex/ui`，原生 CTA 改为共享 `Button`。
- 新文案只补充简体中文。
- VipGift 自身测试为 4/4；完整 VIP 聚焦测试为 29/29，Skill 自测为 29/29。

Figma 案例：

[「FameEX 三期」WEB - VIP 实物礼包](https://www.figma.com/design/KzvWxAYxqfgpoiYuKdxMAE/%E3%80%8CFameEX%E4%B8%89%E6%9C%9F%E3%80%8D----WEB?node-id=12645-358&m=dev)

分享文档：

[FameEX Figma-to-Code Skill 分享](https://qfglxo2m3dc.sg.larksuite.com/docx/JeEPdRRmEoQecexKjKbl3lsDg4e)

## 验证 Skill

先运行脚本单元测试：

```bash
cd /Users/julian/fameex-figma-to-code
/usr/bin/python3 -m unittest discover -s scripts -p 'test_*.py'
```

当前测试覆盖：

- 复用候选扫描。
- i18n 静态引用扫描。
- 依赖补齐和不覆盖保护。

再检查运行环境：

```bash
test -f /Users/julian/.codex/skills/fameex-figma-to-code/SKILL.md
command -v npx
```

最后在一个新的 Codex 任务中使用“快速使用”的提示词和一个已知 `node-id`。端到端 smoke test 应确认：Skill 被触发、Figma 节点可读取、真实路由可定位，并能启动浏览器验证。脚本单测通过不能代替这四项检查。

## 仓库结构

```text
SKILL.md                 Agent 执行入口
README.md                人类使用说明，不作为 Agent 执行入口
agents/openai.yaml       Skill 列表和默认提示词元数据
references/              FameEX 规则、已有实现审计与验收合同
scripts/                 复用、i18n 和依赖检查脚本及测试
assets/fallback-skills/  缺失依赖的安全兜底
```

## 进一步阅读

- [`SKILL.md`](./SKILL.md)：完整执行流程。
- [`references/fameex-web.md`](./references/fameex-web.md)：FameEX Web 组件、Icon、多语言和验证规则。
- [`references/existing-implementation-audit.md`](./references/existing-implementation-audit.md)：已有分支的审计流程。
- [`references/verification-contract.md`](./references/verification-contract.md)：浏览器证据与最终交付合同。
