# PDF 导出辅助说明

本文件补充 PDF 交付方式，不改变 `SKILL.md` 的文献解读目标、结构或要求。使用时可将本说明与主技能一并提供给助手；单独调用技能名并不保证助手会自动读取新的辅助文件。

## 普通聊天窗口：粘贴总结，下载真实 PDF

如果聊天窗口不能执行代码或创建附件，skill 本身不能为它增加文件生成能力。此时不要把虚构路径、示例下载链接或 Markdown 文本冒充 PDF。

1. 让助手按照原 skill 生成完整总结。长文分段完成后，先合并全部章节。
2. 打开 [浏览器 PDF 导出工具](https://gcjack111.github.io/paper_skill/tools/pdf-export.html)。
3. 粘贴总结的完整正文或 Markdown，填写可选标题，点击“下载 PDF”。生成的文件保存在浏览器的下载目录。

总结只在浏览器本地处理，不向服务器上传。字体与 PDF 引擎随工具一起提供，不依赖电脑安装中文字体或 Python。

### 不方便访问在线工具时

下载整个仓库 ZIP，解压后用现代浏览器打开 `tools/pdf-export.html`，同样可以离线生成 PDF。单独保存这个 HTML 文件也可以离线使用；不要把 GitHub 的文件预览页面另存为网页来代替它。

## 能运行代码的助手：自动导出

先把最终完整总结写成 UTF-8 Markdown 文件，再调用随附脚本。以下路径按实际安装目录调整；自定义 `CODEX_HOME` 时使用对应位置。

首次准备独立 Python 环境：

```sh
python3 -m venv /tmp/paper-pdf-env
/tmp/paper-pdf-env/bin/python -m pip install -r ~/.codex/skills/paper-logic-simplifier/requirements.txt
```

导出：

```sh
/tmp/paper-pdf-env/bin/python ~/.codex/skills/paper-logic-simplifier/scripts/export_pdf.py \
  --input /absolute/path/summary.md \
  --output /absolute/path/summary.pdf
```

脚本将自动使用 `assets/fonts/` 内附的中文字体，并输出文件绝对路径、页数和文件大小。也可以用 `--font /path/to/font.ttf` 指定其他 TrueType 字体。

Windows 用户将虚拟环境解释器路径替换为 `环境目录\Scripts\python.exe`，技能路径改成实际安装位置。脚本本身使用跨平台 Python 路径处理。

## 给助手的交付检查

- 先识别当前环境是否具有文件写入、代码执行、文件附件交付能力；不要反复重试一个环境不支持的操作。
- 有这些能力时，运行导出脚本或环境原生 PDF 工具，确认文件真实存在、非空且能打开，检查中文及分页，再通过当前平台支持的文件附件/链接机制交付。
- 文件系统中的绝对路径只对能访问该文件系统的用户有效，不能在普通聊天窗口里当成公开下载链接。
- 只有正文输出能力时，提供完整总结和上面的浏览器导出工具链接，清楚说明粘贴步骤，不声称已经创建 PDF。
- 报错时保留总结原稿。缺依赖时安装 `requirements.txt`；字体缺失时恢复完整仓库；不要用英文默认字体强行导出中文。

## 支持范围

支持中文与英文、标题、段落、加粗、列表、链接、引用、表格和代码块，并自动分页。超宽/超长表格可能改为逐条记录以保证内容可读。图片在浏览器版保留说明文字，在脚本版保留说明及来源文字，不自动抓取远程图片；LaTeX 公式按文本保留，不保证数学排版。保留总结原稿便于继续修改。

## 重新获取更新

已经通过 Git 安装的用户，在技能目录执行 `git pull --ff-only`。通过 ZIP 安装的用户重新下载完整 ZIP；仅复制旧版 `SKILL.md` 不包含这些辅助功能。
