# JSON 记录格式 v2

每篇一个 JSON，文件名通常 `01.json`。记录放在调用者的 `<输出目录>/_模板/`，不写回安装包。编号和 `topic` 决定稳定输出名 `{id} {topic}.pdf`；改变中文标题用 `article.headline`，不随意改旧文件名。

| 字段 | 内容 |
|---|---|
| `schema_version` | 新记录为 2；旧版 1 仅保留原样重建能力 |
| `id`, `topic` | 唯一编号和稳定短文件名，不含路径分隔符 |
| `source` | 相对 `--papers` 的原 PDF 路径，不能是解读成品 |
| `source_sha256` | 原 PDF 指纹；版本变化后先核验裁图再更新 |
| `kind` | `research` 或 `review`；综述用真实汇总证据，不杜撰自有实验 |
| `series` | 页脚专题或空串 |
| `title`, `author`, `journal`, `doi` | 原文信息；无 DOI 留空，未知刊物/年份如实说明 |
| `reference` | 方法、实验、附录和图表出处 |
| `article.headline`, `byline` | 公众号式中文标题、作者/机构简写 |
| `article.figures` | 原文方法、数据及结果图和需就近解释的原表列表；每项为裁图字段加 `caption`、`guide` |
| `article.route_missing_reason` | 没有路线/机制图时填写核查后的真实原因 |
| `narrative.sections` | 正文顺序：两句原文定位、作者贡献原文与解释、按主文图号组织的逐图解读；每节含 `heading`、`paragraphs`、`figure_indices` |
| `narrative.result_heading` | 对应论文实验证据的具体标题 |
| `narrative.result_paragraphs` | 说明实验对象、参照、评价口径和关键结果的短段落列表 |
| `narrative.closing` | 一段精确结语，概括方案、关键机制和证据支持的价值；不分条、不塞入实验建议 |
| `technical.location` | 实验与模型的详细原文位置 |
| `technical.performance` | 全部选定性能证据列表；裁图字段加 `title`、`guide`，可加 `paragraphs` |
| `technical.performance_missing_reason` | 没有任何定量表图时的真实原因 |

## 图文顺序

新记录的前三个正文节依次为“Abstract第一句”“Introduction第一自然段最后一句”“Contribution原文与解释”。前两节在paragraphs中分别写原文、中文释义和简明解释；第三节按作者顺序逐条写贡献原文、释义、解释与出处。随后按原图顺序创建图文小节，由figure_indices连接相应图片。

原文摘录直接存为原文字符串，不用中文改写代替。章节或明确贡献陈述缺失时，只记录该项真实的材料状态，继续解读。


`paragraphs` 是非空字符串列表，用自然段推进一个问题。`figure_indices` 是 `article.figures` 的 **1 起始索引**；每张所列图表必须且只能出现在一个正文节。先读该节文字，再展示对应原图及紧邻的 `guide`。需要图文交替推进时拆成不同小节，不在一个小节里堆全部图片。

每幅图的 `caption` 给中文图名，`guide` 说明图中的模块/箭头怎样支撑这一节的解释。图名和说明放在每张图自己的对象中，不再使用 `caption1/2` 的固定位置。

性能条目按正文论证顺序排列。每项可用 `paragraphs` 放该组实验的设定与关键结果，显示在图前，图后紧跟 `guide`。多组实验分别填写各自的 `paragraphs`，不要把所有分析集中在 `result_paragraphs`；后者只做整体引入。同一图表只放一次，不同时放进方法图和性能列表。跨页表须保留所有部分，图号标成“表 A1（续）”等独立标识；不得因页数或文字精简删掉已核验的性能证据。

```json
{
  "heading": "先求各个来源的投影，再合并重叠区域",
  "paragraphs": ["此处由助手根据原文写出该步骤做了什么，以及为什么需要它。"],
  "figure_indices": [2]
}
```

该段只说明结构，不能照搬到其他论文。标题、内容、索引均由助手依据本次原文填写。

单幅裁图对象：

```json
{
  "page": 4,
  "number": "图 2",
  "box": [0.1, 0.1, 0.9, 0.4],
  "caption": "原文技术流程",
  "guide": "说明这张图展示的输入、处理和输出。"
}
```

性能对象使用 `title` 代替 `caption`。坐标只是格式示例，必须针对原 PDF 实际观察后填写。所有图保留原图号和实际 PDF 页码；正文保留指标单位、参照条件与统计范围。

`narrative.closing` 通常约 100–180 中文字、3–4 句，长度是写作指导而非校验限额。不要用换行或编号模拟旧学习清单。结语通常接在最后一个证据块后；排版仅在空间不够时换页，不专门预留一页。

可加 `evidence_notes` 保存关键主张的原文出处与核验状态，供助手审校；不进入成品。字段校验只能验证结构，不能证明内容准确。

## 更新旧记录

版本 1 的 `wechat.problem/method/result/conclusion` 可按旧版布局原样重建，防止未经阅读自动改变历史内容。要应用新版，助手必须阅读原文后：

1. 保留编号、文件名、原 PDF 和经核验的图表；将每幅方法图的 `captionN/guideN` 移入图对象。
2. 将正文重新组织为 `narrative.sections`，先两句原文及作者贡献，再按图号逐图解释；逐节对应原图。
3. 核对结果表的实际比较对象、单位和范围，填写实验段与各证据说明。
4. 重新写一段结语，设 `schema_version: 2`；工作副本可移除过时 `wechat` 字段。
5. 运行生成与验收，逐页检查。

脚本不拼接、截断或自动总结旧结论；缺少新版正文时会拒绝按 v2 生成。这样保留原事实和图表，不把过时建议当作新结语。
