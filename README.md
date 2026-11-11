# 纵向 skill：单篇论文图文解读

**提供你自己的论文，得到按“两句原文 → 作者贡献 → 论文原图与解读 → 结语”组织的中文PDF。**

纵向skill负责单篇内部的深入解读；横向skill负责多篇文献综合与Introduction论证链。英文调用名称保持 `paper-logic-simplifier`。

## 调用示例

上传论文后输入：

> 使用 $paper-logic-simplifier 纵向解读这篇论文：先列出Abstract第一句及Introduction第一自然段最后一句，再展示Contribution原文及对应解释，随后按图号嵌入论文原图并讲解，最后保留结语，生成完整PDF。

也可以直接说“请用纵向skill解读这篇论文”。批量任务逐篇生成，每篇内容和图表均取自相应原文。

助手自行阅读、定位原句与贡献、提取原图、撰写解释、生成并检查文件。用户无需填写内部记录或手工裁图。

## 默认输出顺序

1. **基本信息**：标题、作者、年份、刊物及DOI。
2. **Abstract第一句**：原文、中文释义及其描述的研究主题。
3. **Introduction第一自然段最后一句**：原文、中文释义及其在该段中的作用。
4. **Contribution**：按作者顺序逐条摘录原文，提供对应解释和关联图表位置。
5. **论文原图与解读**：按主文图号呈现图片，解释方法、数据、实验与结果；相关原表完整保留。
6. **结语**：总结研究做法、主要证据及其意义。

开头直接用两句原文定位研究。图表保留子图、图例、单位、完整对照和脚注，并提供来源页码。最终交付完整中文图文PDF。

## Writing style

If a sentence serves only to preempt criticism rather than advance the argument, delete it.

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

旧版生成器曾完成 21 篇文献、96 页的回归验证；该数字属于历史覆盖，不代表当前纵向输出顺序已经完成同规模回归。新版需按当前记录格式运行校验，并逐页检查输出。仓库不携带这些论文或它们的解读内容，也不限制用户提供的论文数量。

## 运行说明

Python 3.10+，依赖见 `requirements.txt`；生成中文需要兼容的 CJK TrueType 字体。工具在助手完成审校记录后运行：

```bash
python scripts/render_review.py --papers /path/to/papers --records /path/to/reviews/_模板 --output /path/to/reviews
python scripts/check_reviews.py --records /path/to/reviews/_模板 --output /path/to/reviews --qa /path/to/qa
```

脚本负责排版，阅读与写作由使用 skill 的 AI 助手完成。不需要为这些脚本配置额外模型 API；不会上传你的论文。详细命令和字体配置见 [运行与验收](references/runbook.md)。

## 来源和许可

MIT 许可覆盖仓库中的代码、说明和模板，不替代原论文、图片或字体的许可。原图来自调用者提供的原 PDF，保留出处；不使用 AI 图片生成工具重画实验数据。
