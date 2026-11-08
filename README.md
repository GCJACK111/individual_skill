# 公众号风格论文图文解读 PDF

**给出你自己的论文，调用一次 skill，得到一份包含原文图片、完整结果表图和详细 AI 结论的中文解读 PDF。**

不依赖固定论文库、特定学科或个人研究项目。统一的是写法与版式，内容来自你提供的论文。

## 调用示例

上传论文后输入：

> 使用 $paper-logic-simplifier，解读这篇论文，生成公众号风格图文 PDF，保留论文中的技术路线图、模型图和完整性能表图，最后给出详细、有参考价值的 AI 结论。

也支持：

> 使用 $paper-logic-simplifier，把这个文件夹中尚未解读的论文逐篇生成 PDF。

> 使用 $paper-logic-simplifier，扩写已有解读的 AI 结论，保留图片和实验表格。

助手自行阅读、选图、填写内部记录、生成并检查文件。用户不用写 JSON、手工截图或提供额外研究背景。需要完整原图表时，请提供原 PDF 或可访问的全文。

## 会得到怎样的 PDF

1. **问题与方法**：清楚连贯的公众号式短文，解释为什么做、难在哪里、如何解决。
2. **原文路线与模型图**：直接裁取你的论文图片，附中文读图说明、图号和页码。
3. **完整原文证据**：performance table、结果图、消融、效率或迁移实验，可保留多张与跨页续表。
4. **独立末页 AI 研读结论**：方法贡献、证据支持、适用边界、可借鉴的设计和场景、总体判断与下一步。

采用白底、红色标题、深灰文字、单栏图表与页码；通常每篇 4–5 页，证据多时按需增加。综述或没有性能表的论文按实际材料说明，不杜撰模型与实验。

## 安装

将仓库作为技能文件夹安装到宿主支持的目录，文件夹名为 `paper-logic-simplifier`，根目录包含 `SKILL.md`。例如在 Codex 中，若目标目录尚不存在：

```bash
git clone https://github.com/GCJACK111/paper_skill.git ~/.codex/skills/paper-logic-simplifier
```

已有安装请先保留本地修改再更新。按宿主要求重新加载技能，即可用 `$paper-logic-simplifier` 调用。仅粘贴仓库链接不等于已安装。

## 包内内容

- `SKILL.md`：完整自动工作流程与使用边界。
- `references/editorial.md`：公众号叙事、术语解释与五段详细结论的写法。
- `references/figures.md`：原 PDF 页码、图表定位、裁切坐标和完整性检查。
- `references/record-format.md`：助手内部使用的结构化记录。
- `references/runbook.md`：运行环境、字体、增量更新、验收和故障处理。
- `scripts/`：原文提取/裁图、记录验证、PDF 生成和逐页验收。
- `assets/record-template.json`：用于任何新论文的空模板，由助手完成。
- `tests/`：记录和输入来源边界的工具检查。

生成器经过实际 21 篇文献、96 页的回归验证；这只是开发验证覆盖，不限制用户提供的论文。仓库不携带这些论文或它们的解读内容。

## 运行说明

Python 3.10+，依赖见 `requirements.txt`；生成中文需要兼容的 CJK TrueType 字体。工具在助手完成审校记录后运行：

```bash
python scripts/render_review.py --papers /path/to/papers --records /path/to/reviews/_模板 --output /path/to/reviews
python scripts/check_reviews.py --records /path/to/reviews/_模板 --output /path/to/reviews --qa /path/to/qa
```

脚本负责排版，阅读与写作由使用 skill 的 AI 助手完成。不需要为这些脚本配置额外模型 API；不会上传你的论文。详细命令和字体配置见 [运行与验收](references/runbook.md)。

## 来源和许可

MIT 许可覆盖仓库中的代码、说明和模板，不替代原论文、图片或字体的许可。原图来自调用者提供的原 PDF，保留出处；不使用 AI 图片生成工具重画实验数据。
