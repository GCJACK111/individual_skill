# 公众号风格论文图文解读 PDF

**给出你自己的论文，调用一次 skill，得到一份包含原文图片、完整结果表图和简短准确结语的中文解读 PDF。**

不依赖固定论文库、特定学科或个人研究项目。统一的是写法与版式，内容来自你提供的论文。

## 调用示例

上传论文后输入：

> 使用 $paper-logic-simplifier，解读这篇论文，生成公众号风格图文 PDF，沿论文的方法流程组织图文，保留技术路线图、模型图和完整性能表图，最后用一段准确简短的结语总结。

也支持：

> 使用 $paper-logic-simplifier，把这个文件夹中尚未解读的论文逐篇生成 PDF。

> 使用 $paper-logic-simplifier，优化已有解读的图文组织，让方法解释紧挨对应原图，并把结尾压缩为总结性结语，保留完整实验表格。

助手自行阅读、选图、填写内部记录、生成并检查文件。用户不用写 JSON、手工截图或提供额外研究背景。需要完整原图表时，请提供原 PDF 或可访问的全文。

## 会得到怎样的 PDF

1. **引言**：从具体场景说明为什么做、难在哪里，以及论文的解决思路。
2. **方法图解**：沿关键步骤展开，标题写清该步做什么；解释后紧接对应原图、中文读图说明、图号与页码。
3. **实验验证**：交代数据、对照、指标和关键结果，配完整 performance table、结果图、消融、效率或迁移实验，保留跨页续表。
4. **结语**：一个自然段概括本文方案、关键机制和证据支持的价值，默认约 100–180 中文字、3–4 句。具体借鉴融入方法说明，结尾不再铺陈学习清单。

采用白底、红色标题、深灰文字、单栏图表与页码。篇幅、方法节数和分页服从论文内容，不强制给结语单独一页。综述或没有性能表的论文按实际材料说明，不杜撰模型与实验。

## 安装

将仓库作为技能文件夹安装到宿主支持的目录，文件夹名为 `paper-logic-simplifier`，根目录包含 `SKILL.md`。例如在 Codex 中，若目标目录尚不存在：

```bash
git clone https://github.com/GCJACK111/paper_skill.git ~/.codex/skills/paper-logic-simplifier
```

已有安装请先保留本地修改再更新。按宿主要求重新加载技能，即可用 `$paper-logic-simplifier` 调用。仅粘贴仓库链接不等于已安装。

## 包内内容

- `SKILL.md`：完整自动工作流程与使用边界。
- `references/editorial.md`：公众号图文组织、术语解释与简短准确的结语写法。
- `references/figures.md`：原 PDF 页码、图表定位、裁切坐标和完整性检查。
- `references/record-format.md`：助手内部使用的结构化记录。
- `references/runbook.md`：运行环境、字体、增量更新、验收和故障处理。
- `scripts/`：原文提取/裁图、记录验证、PDF 生成和逐页验收。
- `assets/record-template.json`：用于任何新论文的空模板，由助手完成。
- `tests/`：记录和输入来源边界的工具检查。

旧版生成器曾完成 21 篇文献、96 页的回归验证；该数字属于历史覆盖，不代表新版图文组织与结语排版已经完成同规模回归。新版需按当前记录格式运行校验，并逐页检查输出。仓库不携带这些论文或它们的解读内容，也不限制用户提供的论文数量。

## 运行说明

Python 3.10+，依赖见 `requirements.txt`；生成中文需要兼容的 CJK TrueType 字体。工具在助手完成审校记录后运行：

```bash
python scripts/render_review.py --papers /path/to/papers --records /path/to/reviews/_模板 --output /path/to/reviews
python scripts/check_reviews.py --records /path/to/reviews/_模板 --output /path/to/reviews --qa /path/to/qa
```

脚本负责排版，阅读与写作由使用 skill 的 AI 助手完成。不需要为这些脚本配置额外模型 API；不会上传你的论文。详细命令和字体配置见 [运行与验收](references/runbook.md)。

## 来源和许可

MIT 许可覆盖仓库中的代码、说明和模板，不替代原论文、图片或字体的许可。原图来自调用者提供的原 PDF，保留出处；不使用 AI 图片生成工具重画实验数据。
