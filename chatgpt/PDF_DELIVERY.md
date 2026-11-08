# ChatGPT 会话内 PDF 交付补充

仅补充 PDF 文件生成与交付；论文分析目标、事实依据、章节结构与篇幅继续遵循原版 `SKILL.md` 和用户的明确要求，不覆盖主技能。

## 运行前提

此流程面向普通 ChatGPT 聊天。用户不用安装软件、运行 Python 或复制总结到其他网页；Python 代码由具备数据分析/文件生成工具的 ChatGPT 在会话后台执行。

首先确认当前会话实际提供 Python 执行和生成文件的工具。有工具就主动调用，不要因为用户说“不会运行代码”就误认为 ChatGPT 不能执行。只有文本生成能力时，要尽早说明缺少文件生成能力，不能声称增加几个辅助文件就能开通工具，也不要虚构下载链接。

## 自动执行流程

1. 使用当前会话的 Python 工具，定位用户上传的辅助 ZIP 和论文文件，解压辅助包到会话工作目录。读取包内原版 `SKILL.md` 与本说明；不要把 ZIP、Python、字体只当成可检索知识文字。
2. 依原版主技能完成论文解读。把完整总结真实写入 UTF-8 `paper_summary.md`。长文可逐节追加，最终合并所有章节；PDF 必须包含最终完整总结，不得用提纲、摘要或占位文字代替长文。
3. 使用本包 `chatgpt/export_pdf.py` 导出 PDF。它只使用 Python 标准库和随包附带的中文 TrueType 字体，无须 `pip`、联网下载、浏览器、LaTeX 或系统中文字体。可先查看脚本 `--help`。字体默认位于包内 `assets/fonts/NotoSansSC-Regular.ttf`。
4. 示例调用（路径均以当前会话真实位置为准；`/mnt/data` 是常见工作目录，需先确认）：

```python
from pathlib import Path
import runpy
import sys

# root 指向刚解压的 paper-logic-simplifier 目录。
# summary_path 指向已经写完的完整总结，output_path 指向待交付 PDF。
script = root / "chatgpt" / "export_pdf.py"
old_argv = sys.argv[:]
try:
    sys.argv = [str(script), "--input", str(summary_path),
                "--output", str(output_path)]
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as result:
        if result.code not in (None, 0):
            raise
finally:
    sys.argv = old_argv
```

5. 导出后确认文件存在、以 `%PDF-` 开头且大小非零。若环境有 PDF 阅读/渲染工具，检查中文、分页和末尾章节。可以同时提供 Markdown 原稿供用户继续编辑。
6. 使用当前 ChatGPT 的原生文件附件机制交付真实 PDF。如果该会话支持 `sandbox:` 文件链接，只链接当前会话中确已生成并验证的文件，例如真实生成于 `/mnt/data/paper_summary.pdf` 后才能给出 `[下载完整总结 PDF](sandbox:/mnt/data/paper_summary.pdf)`。这是会话附件引用，不是对外永久网址；不能把示例路径直接当成已有文件。

## 失败处理

- 字体或脚本找不到：先检查 ZIP 是否完整解压，按实际目录修复路径，不要求用户手动运行代码。
- 缺少普通第三方包：直接使用本包的标准库导出脚本，不反复尝试联网安装依赖。
- 字体不支持某字符：脚本会明确报错。装饰性符号可改为普通编号；科学符号或正文实质内容不得悄悄删除，可用环境中确实可用且覆盖该字符的 TrueType 字体通过 `--font` 重试。
- 文件生成失败或原会话下载链接过期：保留/重新获取 Markdown 原稿，在当前可运行 Python 的会话重新导出并生成新附件。仅修改链接文本无法恢复旧文件。
- 没有 Python/文件生成工具：诚实告知当前会话不能完成自动 PDF 交付，需使用具备该能力的会话。不要把手动粘贴网页导出作为已完成自动交付的证明。

## 排版边界

为避免 ChatGPT 环境缺依赖，标准库导出器优先保证中文可读、完整内容和自动分页，支持基本标题层级；Markdown 表格、代码、链接和公式保留可读原文，不承诺复杂表格或数学公式的专业排版。它不下载图片，也不改变论文解读逻辑。
