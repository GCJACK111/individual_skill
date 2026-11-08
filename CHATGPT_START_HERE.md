# 普通 ChatGPT：直接生成可下载 PDF

适用于“把技能上传或粘贴到普通 ChatGPT 聊天”的使用方式。原版 `SKILL.md` 完全不变；新辅助包只补齐 ChatGPT 后台生成 PDF 的流程。

## 一次准备

1. 下载 [ChatGPT 专用辅助包](https://github.com/GCJACK111/paper_skill/raw/refs/heads/main/chatgpt/paper-logic-simplifier-chatgpt.zip)。
2. 在提供数据分析/文件生成工具的 ChatGPT 会话中，上传这个 ZIP 和要解读的论文。
3. 复制下面的启动语。GPT 会在后台运行生成代码，用户不需要自己编程或使用网页转换器。

```text
请读取我上传的 paper-logic-simplifier-chatgpt.zip，使用 Python 工具解压，阅读其中原版 SKILL.md 和 chatgpt/PDF_DELIVERY.md。

按原版技能完整解读我上传的论文，篇幅和重点遵循我提出的要求。只补充 PDF 交付流程，不改变原版分析结构。

请把最终完整总结保存成 Markdown，再由你在当前会话后台运行包内 chatgpt/export_pdf.py，生成真实 PDF，检查文件存在、中文可读并包含全部章节，最后提供本会话中可点击下载的 PDF 附件。不要只输出代码、虚构文件链接，或要求我把正文复制到网页转换器。

如果本会话没有 Python/文件生成工具，请在开始前明确说明缺少的能力。
```

需要约 20000 字时，在启动语末尾加上“目标篇幅约 20000 字，按主技能结构完整展开”。字数和论文分析要求由原技能及用户明确指令决定。

## 为什么仍然需要检查会话能力

“用户不运行代码”和“ChatGPT 没有代码工具”是两回事。普通用户可以让具备数据分析工具的 ChatGPT 在后台执行 Python、创建文件并交付附件；但上传 ZIP 或粘贴 skill 本身不会为会话增加工具权限。

只粘贴 `SKILL.md` 时，模型看不到配套的脚本和字体，也不一定会读取辅助说明。请上传完整专用 ZIP，并明确要求读取包内补充说明；不要仅在聊天里发送 GitHub 仓库网址就假设 Python 环境已经下载了全部文件。

本包不需要第三方 Python 依赖或网络安装，避免因 `pip` 不可用、缺中文字体而导出失败。原 ChatGPT 会话附件过期时，需要在当前有文件生成能力的会话重新运行生成，不能仅修饰旧链接。

## 专用包内容

- 原版 `SKILL.md`，保持字节一致。
- `chatgpt/PDF_DELIVERY.md`，会话内自动生成与交付说明。
- `chatgpt/export_pdf.py`，仅依赖 Python 标准库的中文 PDF 导出器。
- `assets/fonts/NotoSansSC-Regular.ttf` 与 `OFL.txt`，中文字体及许可。
- `LICENSE`。

专用包由维护者运行 `python3 scripts/build_chatgpt_bundle.py` 构建。使用者无需运行此命令。

## 能力与验证说明

辅助包能解决文件生成方法、Python 依赖和中文字体的缺失；不能代替 ChatGPT 的工具权限、工作区政策或下载会话权限。本仓库的脚本测试不代表已经验证每一位用户的 ChatGPT 会话。发布后应让一名使用者按上述流程上传论文试用，确认最终出现真实可下载附件。

## 官方依据

- [OpenAI：GPT Actions 介绍](https://developers.openai.com/api/docs/actions/introduction)：说明 ChatGPT 数据分析可生成并执行 Python。
- [OpenAI：Skills 与 Plugins](https://learn.chatgpt.com/docs/skills-and-plugins)：说明技能封装工作指令与辅助资源。
- [OpenAI：GPT 工作流与工具能力](https://learn.chatgpt.com/docs/migrate-custom-gpts)：说明工具可用性取决于产品体验与工作区设置，并应实际测试文件输出。
