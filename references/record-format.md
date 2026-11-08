# JSON 记录格式 v1

每篇一个 JSON，文件名通常 `01.json`。默认记录目录 `<输出目录>/_模板/`，也可传入任意 `--records` 路径。编号和 `topic` 决定稳定输出名：`{id} {topic}.pdf`。修改文章标题请改 `article.headline`，不随意更改已有文件名。

| 字段 | 内容 |
|---|---|
| `schema_version` | 当前为 1 |
| `id`, `topic` | 唯一编号、稳定短文件名；不含路径分隔符 |
| `source` | 相对 `--papers` 的原 PDF 路径；不得指向生成的解读 |
| `source_sha256` | `inspect`/`inventory` 返回的原文件哈希，新增记录应填写；变更后先重验裁图 |
| `kind` | `research` 或 `review`，综述提示由此决定，不能按编号硬编码 |
| `series` | 页脚专题，示例为“城市能源”；其他领域改为对应专题或空串 |
| `title`, `author`, `journal`, `doi` | 原文信息；无 DOI 用空串，刊物/年份未知时如实标注 |
| `reference` | 主要方法、实验、附录和图表定位，供末页溯源 |
| `article.headline`, `byline` | 中文文章标题，作者/机构简写 |
| `article.figures` | 0–2 个原文路线/模型图条目，每项 `page`, `number`, `box` |
| `article.caption1/2`, `guide1/2` | 对应中文图名、读图说明；只填实际图的索引 |
| `article.route_missing_reason` | 无原文路线/机制图时必须给出真实原因；不以空白代替调查 |
| `technical.location` | 模型与结果的详细出处 |
| `technical.performance` | 原性能/综述证据列表，每项除裁图字段外还含 `title`, `guide` |
| `technical.performance_heading` | 可选，综述通常为“综述证据” |
| `technical.performance_missing_reason` | 性能证据列表为空时必须说明原因 |
| `wechat.problem`, `method`, `result` | 公众号风格的三个短段落 |
| `wechat.conclusion` | 3–5 项列表，每项 `{ "title": "…", "text": "…" }`，对应末页的具体学习要点；title 用具体做法命名，text 解释学什么、为什么有效和怎么用 |

可选增加 `evidence_notes`，记录关键主张、章节/PDF 页码、事实或推断类型及核验状态，供审稿使用；不会直接进入 PDF。最终内容仍由原文核验，字段校验不证明事实正确。

单个性能条目示例：

```json
{
  "page": 13,
  "number": "表 4",
  "box": [0.05556, 0.20139, 0.94444, 0.36574],
  "title": "八种模型的完整性能对照",
  "guide": "最后一行是 SAGNN。先选屋顶或外墙，再选单位面积强度或整面总量；同一组列内，RMSE 越小、R² 越高越好。"
}
```

上述只是坐标和说明的格式示例，不能套到调用者的论文。模板中的空字符串由执行 skill 的助手阅读论文后填写，校验失败是预期行为；不让用户手填 JSON，也不把未完成模板生成成品。

## 兼容已有工作记录

若调用者已经有旧版解读记录，保留稳定编号、topic 和经核验的图表，按本次要求更新正文或结论即可。`wechat.conclusion` 字段名保持兼容，但内容必须改写为 3–5 条具体学习要点；不能只换总标题，保留旧版“贡献／边界／下一步”的段落。条数由论文可借鉴的实质内容决定，不为凑满五条重复。

路线/模型图最多占两个位置；其他确实需要的结果图放 technical.performance。相同页码和图号的第二图若已经在性能列表出现，生成器只在性能区展示一次。跨页续表必须使用不同的 number（例如“表 A1（续）”），避免误判。

这些记录存放在调用者自己的输出目录，不写回安装包，也不会自动上传给任何人。
