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

## 在普通 ChatGPT 中自动生成 PDF

主要通过上传或粘贴在 ChatGPT 使用的用户，请看 [ChatGPT 专用使用说明](CHATGPT_START_HERE.md)。

1. 下载 [ChatGPT 专用辅助包](https://github.com/GCJACK111/paper_skill/raw/refs/heads/main/chatgpt/paper-logic-simplifier-chatgpt.zip)。
2. 把辅助 ZIP 和论文上传到具备数据分析/文件生成工具的 ChatGPT 会话。
3. 使用说明中的启动语，让 GPT 读取原版主技能和 PDF 补充流程，在会话后台运行导出脚本，最后交付真实 PDF 附件。

用户不需要编程、安装 Python 或手动把总结复制到转换网页。专用包自带中文字体，导出器只依赖 Python 标准库，无须联网安装第三方库。主 `SKILL.md` 保持原样；需要同时提供辅助 ZIP 与启动语，单独粘贴旧版主技能不会自动载入新文件。

**前提：当前 ChatGPT 会话必须实际具备 Python/文件生成工具。** 上传文件和 skill 指令不会开启工具权限；无法创建附件时，应明确报告，不能输出虚构下载地址。附件失效后需在当前可运行工具的会话重新生成。

## 其他环境的 PDF 辅助工具

- 支持运行代码的助手可使用 `scripts/export_pdf.py`（依赖见 `requirements.txt`），或使用无需第三方依赖的 `chatgpt/export_pdf.py`。
- 排错见 [PDF_HELP.md](PDF_HELP.md)。[浏览器导出工具](https://gcjack111.github.io/paper_skill/tools/pdf-export.html) 仅为可选的手动工具，不是 ChatGPT 自动交付方案。

## 仓库文件

- `SKILL.md`：技能入口和工作规范。
- `agents/openai.yaml`：Codex 界面显示信息与默认提示。
- `CHATGPT_START_HERE.md`、`chatgpt/`：普通 ChatGPT 专用上传包、启动语与自动导出流程。
- `PDF_HELP.md`：其他环境的 PDF 导出与排错说明。
- `tools/pdf-export.html`：可在线或离线使用的浏览器 PDF 导出工具。
- `scripts/export_pdf.py`、`requirements.txt`：代码环境的 PDF 导出脚本与依赖。
- `assets/fonts/`：中文字体与独立的 OFL 字体许可证。

## 许可证

本项目采用 [MIT License](LICENSE)，允许使用、修改与再分发。
