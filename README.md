# 文献逻辑梳理与简化总结

一个面向初学者的中文 Codex skill：把论文的研究背景、问题、方法、数据与结果串成易于理解的逻辑，并在最后生成完整总结的 **PDF 文件**。

## 功能

- 基于用户提供的 PDF、论文正文或章节摘录进行精读。
- 梳理背景 → 挑战 → 方法与数据集 → 实验 → 结果 → 结论。
- 解释关键术语，保留重要指标与原文定位信息。
- 区分论文结论、作者提及的未来方向与模型提出的延伸建议。
- 提供学术思考和至少 5 个后续问题及回答。
- 支持长文分段处理，最终汇总并生成 PDF。

## 安装

克隆本仓库到 Codex 的个人技能目录：

```sh
git clone https://github.com/GCJACK111/paper_skill.git ~/.codex/skills/paper-logic-simplifier
```

如使用自定义 `CODEX_HOME`，请安装到该目录下的 `skills/paper-logic-simplifier`。也可以下载仓库 ZIP，将包含 `SKILL.md` 的文件夹放到技能目录。

## 使用

在支持 skills 的 Codex 环境中调用，并附上论文文件或正文：

```text
使用 $paper-logic-simplifier 解读这篇论文，面向初学者，约 20000 字，最后生成完整总结的 PDF 文件。
```

可自行指定篇幅、目标读者及重点。仅提供摘要或部分章节时，总结会注明材料范围与缺失内容。

## 输出结构

1. 基本信息（标题、作者、年份、刊物/会议）
2. 引言（背景和意义）
3. 内容及结构（论文结构）
4. 正文（背景、挑战、方法、数据、实验与结果）
5. 结论
6. 未来研究方向
7. 学术思考
8. 至少 5 个后续问题及回答
9. 完整总结 PDF 文件

## PDF 无法下载时

普通聊天窗口如果没有文件生成能力，单靠 skill 指令无法创建附件。现在附带独立的 PDF 导出辅助工具，原有 `SKILL.md` 和文献解读功能保持不变。

- **无需编程：** 打开 [浏览器 PDF 导出工具](https://gcjack111.github.io/paper_skill/tools/pdf-export.html)，粘贴完整总结，点击“下载 PDF”。也可以下载仓库后双击 `tools/pdf-export.html` 离线使用。
- **代码助手：** 使用 `scripts/export_pdf.py` 将完整 Markdown 总结导出为 PDF，依赖见 `requirements.txt`，中文字体已随仓库提供。
- 安装、操作与排错详见 [PDF_HELP.md](PDF_HELP.md)。工具在本地浏览器处理正文，不上传内容。

未提供或无法读取的论文内容不会被视为已读。普通聊天窗口请交付完整正文与浏览器导出链接，不要声称存在并未生成的 PDF 附件。

## 仓库文件

- `SKILL.md`：技能入口和工作规范。
- `agents/openai.yaml`：Codex 界面显示信息与默认提示。
- `PDF_HELP.md`：PDF 导出与排错说明。
- `tools/pdf-export.html`：可在线或离线使用的浏览器 PDF 导出工具。
- `scripts/export_pdf.py`、`requirements.txt`：代码环境的 PDF 导出脚本与依赖。
- `assets/fonts/`：中文字体与独立的 OFL 字体许可证。

## 许可证

本项目采用 [MIT License](LICENSE)，允许使用、修改与再分发。
