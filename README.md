# FameEX Figma to Code

这套 Skill 帮助 Codex 把 Figma 或产品需求落实到 FameEX 前端仓库。Agent 规则以 [`SKILL.md`](./SKILL.md) 为准；README 只保留使用入口。

## 这套 Skill 解决什么问题

- **找对页面**：先确认应用、路由和代码归属。
- **看懂设计**：结构化节点和同节点截图一起使用。
- **复用现有能力**：只在涉及组件、素材、Hook 或 API wrapper 时检查复用。
- **不替业务做决定**：Figma 不充当接口、权限或状态合同。
- **用真实结果验收**：检查真实路由、受影响视口和聚焦测试。

## 模式

- `targeted-change`：默认。已有页面的小范围 UI、样式、文案、素材、组件或弹窗调整；不创建完整视觉 manifest、回执或全视口矩阵。
- `strict-parity`：用户要求逐帧、逐像素、每个距离，或涉及新页面、多状态、复杂动效、Desktop/H5 联动时，启用 `visual-evidence.json`、RGBA、视口矩阵和回执。
- `feature-delivery`：提供完整需求和 Figma 总入口，先建立 Feature Manifest，再按业务切片开发。
- `slice-implementation` / `audit-existing`：分别用于已映射切片和已有分支审查。
- `release-readiness` / `post-release-validation`：仅在用户明确要求时使用；部署仍需明确授权。

模式细节见：

- [`references/exact-node-workflow.md`](./references/exact-node-workflow.md)
- [`references/product-delivery-workflow.md`](./references/product-delivery-workflow.md)
- [`references/release-readiness.md`](./references/release-readiness.md)

## FameEX 边界

- 页面可见文案、提示和可访问性标签进入 i18n，默认只改简体中文。
- Customer Web 的页面级 Meta 文案统一放在 `tdk`；其他语言只在已有资源或明确范围内验证。
- 真实查询、提交、上传或后端状态才读取 [`references/api-integration.md`](./references/api-integration.md)。
- Figma 只确认视觉；没有 PRD、接口或仓库证据时，不编造权限、资格、数据和成功状态。

## 能力与安装

日常只读 [`references/capability-index.md`](./references/capability-index.md)；能力缺失或触发时再读 [`references/capability-registry.md`](./references/capability-registry.md)。安装或修改配置前必须先取得用户确认。

当前唯一安装目录：

```text
/Users/julian/.codex/skills/fameex-figma-to-code
```

首次安装：

```bash
git clone ssh://git@github.com/woyaofei303/fameex-figma-to-code.git \
  /Users/julian/.codex/skills/fameex-figma-to-code
```

如果目录已存在，不覆盖；先检查来源、分支和本地改动。Skill 不会自动提交或推送。

Figma MCP 尚未配置且用户同意后：

```bash
codex mcp add figmaremotemcp --url https://mcp.figma.com/mcp
codex mcp login figmaremotemcp
codex mcp list
```

OAuth 授权需要用户确认。登录后仍需在当前任务读取精确节点结构和同节点截图；工具未出现时，重启 Codex 或新建任务。

## 快速使用

默认小改：

```text
使用 $fameex-figma-to-code 调整这个已有界面：
<Figma Design 链接或 node-id>
目标路由：<可选>
```

严格视觉还原：

```text
使用 $fameex-figma-to-code 按 strict-parity 逐帧、逐像素验收：
<Figma Design 链接或 node-id>
```

完整功能：

```text
使用 $fameex-figma-to-code 按 feature-delivery 梳理并实现：
产品文档：<Lark PRD 链接>
Figma 总入口：<Figma 文件或页面链接>
仓库/分支：<目标仓库和分支>
```

## 验证 Skill

```bash
cd /Users/julian/.codex/skills/fameex-figma-to-code
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover \
  -s scripts -p 'test_*.py'
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python \
  /Users/julian/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
git diff --check
git status --short
```

测试同时包含脚本行为测试和静态合同检查；静态合同检查不能代替真实 MCP、仓库和浏览器验证。验证数字以命令的当前输出为准。

## 进一步阅读

- [`references/fameex-web.md`](./references/fameex-web.md)：组件、素材、样式和 i18n 规则。
- [`references/visual-fidelity-loop.md`](./references/visual-fidelity-loop.md)：严格视觉证据链。
- [`references/verification-contract.md`](./references/verification-contract.md)：浏览器检查和交付格式。
- [`references/dependency-bootstrap.md`](./references/dependency-bootstrap.md)：经授权后的缺失能力修复。
