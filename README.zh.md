# PromptIQ

English | [中文](README.zh.md)

为重度 AI 协作用户提供严格的会话复盘工具。

## 功能

在工作会话结束后运行 `/score`，获得：

- 8 个协作维度的严格评分
- 带封顶规则的确定性总分（低复杂度、低置信度会话自动封顶）
- 直白的 **为什么没更高** 分析
- 一条下次会话的具体练习建议

在发送提示词之前运行 `/draft`，输入你的意图或草稿，得到一个更强的、可直接粘贴的版本，并附上改动说明。

## 安装

**一键安装（任意 AI 助手）：**

```
Read https://raw.githubusercontent.com/Explainix/promptiq/main/install.md and follow the instructions to install PromptIQ.
```

### Claude Code

```
/plugin marketplace add Explainix/promptiq
/plugin install promptiq@promptiq
/reload-plugins
```

或在终端直接运行：

```bash
claude plugin install promptiq@promptiq
```

安装后在任意会话结束时输入 `/score`。

### Codex

```bash
git clone https://github.com/Explainix/promptiq ~/.codex/skills/promptiq
```

安装后在任意会话结束时输入 `/score`。

## 使用方式

1. 正常完成一个工作会话。
2. 运行 `/score`。
3. 先看 **为什么没更高**，再看总分。
4. 下次会话应用 **下次练习建议**。
5. 发送提示词前运行 `/draft`，从一开始就写得更好。

## 适合谁用

- 频繁使用 Claude Code / Codex 的用户，想养成更好的提示词习惯
- 想要客观反馈而非鼓励性评价的人
- 觉得自己的提示词模糊但不知道问题在哪的人

不适合：简单的单行会话，或通用的人格测试类对话。

## 评分机制

本地引擎负责 N/A 过滤、总分计算、封顶规则、置信度和趋势追踪。模型负责判断会话质量，引擎保证结果严格且稳定。

校准规则：
- 短会话、低复杂度或低置信度会话会被封顶
- 7.5 分以上需要有具体证据支撑
- 8.5 分以上刻意设计为极少出现

## 示例输出

- [examples/sample-report.md](examples/sample-report.md) — `/score` 报告示例
- [examples/draft-sample.md](examples/draft-sample.md) — `/draft` 输出示例

## 隐私

历史记录存储在本地 `~/.promptiq/history.json`，不上传任何数据。

## 本地开发

```bash
python3 -m unittest discover -s tests -v
python skills/score/scripts/promptiq.py doctor
```

## 许可证

MIT
