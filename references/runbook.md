# 运行、增量更新与验收

## 环境与路径

技能目录可以位于任何位置，脚本不从当前工作目录猜原论文路径。使用可用的 Python 3.10+；在 Codex 桌面环境中先用 `load_workspace_dependencies` 发现运行时。已有依赖则直接使用，不为文档编排修改用户的训练环境。

```bash
python -m venv .venv
.venv/bin/python -m pip install -r "$SKILL_DIR/requirements.txt"
```

仅在需要独立环境时执行以上命令。测试过的版本见 requirements 注释。默认使用 ReportLab + pypdfium2 + Pillow；验收优先使用 Poppler `pdftoppm`，否则可使用隔离进程中的 PDFium 渲染。

变量使用任务专用名称或以下名称，避免改写 HOME/CODEX_HOME：

```bash
SKILL_DIR="/path/to/paper-logic-simplifier"
PAPERS="/path/to/project/paper"
OUTPUT="$PAPERS/论文解读"
RECORDS="$OUTPUT/_模板"
WORK="/path/to/project/tmp/paper-review"
QA="$WORK/qa"
```

用户已有指定输出目录时使用其目录，例如已有“技术先进度”则沿用；新用户默认使用“论文解读”。文件夹名称不构成添加先进性评级的理由。只传入输入论文根目录，避免对生成的解读或 literature review 再做二次总结。

## 中文字体和一致性

标准版正文 Arial Unicode、标题 Songti；500 pt 页宽、36 pt 左右边距、428 pt 栏宽、白底、深灰正文和红色标题。页高按内容变化，适合屏幕阅读，不是固定 A4，也不复制公众号广告或浏览器黑色背景。

macOS 自动发现：
- `/System/Library/Fonts/Supplemental/Arial Unicode.ttf`
- `/System/Library/Fonts/Supplemental/Songti.ttc`

其他环境指定已许可的 CJK TrueType 字体：

```bash
python "$SKILL_DIR/scripts/render_review.py" --papers "$PAPERS" --records "$RECORDS" --output "$OUTPUT" --body-font "/path/to/chinese.ttf" --heading-font "/path/to/chinese-heading.ttf"
```

或设置 `CJK_FONT`、`CJK_HEADING_FONT`。脚本也尝试 WenQuanYi Micro Hei 和 Windows 微软雅黑路径。部分 OTF/TTC 使用 CFF 轮廓，ReportLab TTFont 可能不支持；改用兼容 TTF/TTC，不能静默退回不支持中文的西文字体。换字体会改变换行，因此不能承诺跨机器像素相同。不将系统商业字体拷入仓库。

## 新论文全过程

1. `inventory` 盘点顶层原 PDF，显示源指纹、已登记编号及相同字节文件。对不同版本另按 DOI/题名人工排重。不要覆盖旧编号空缺，也不要恢复已被用户排除的论文。
2. 用 `inspect` 保存逐页文本与 source.json；看完整方法、结果、附录及图表页。扫描件文本为空时使用环境可用 OCR 并目视核验；脚本本身不内置 OCR，不伪称已读全文。
3. 选图、裁图、看裁图。按 editorial 标准写 JSON。可复制空模板到工作目录；不要修改安装包内的示例作为新论文。
4. 完整校验后生成选定编号：

```bash
python "$SKILL_DIR/scripts/validate_record.py" --records "$RECORDS" --papers "$PAPERS" --ids 23
python "$SKILL_DIR/scripts/render_review.py" --papers "$PAPERS" --records "$RECORDS" --output "$OUTPUT" --ids 23
python "$SKILL_DIR/scripts/check_reviews.py" --records "$RECORDS" --output "$OUTPUT" --qa "$QA" --ids 23
```

5. 打开最终 PNG；必要时修改记录与裁图，重新生成并检查受影响页。最终交付对应 PDF。

生成脚本使用临时文件写入后替换对应 PDF，保留稳定文件名；不会修改原 PDF，也不会自动删除未登记旧文件。末尾提示未建档原论文，但不会凭空为它们生成文章。调用本 skill 的助手应继续阅读和建档，而非把提示当作任务完成。

## 批量与后续更新

无 `--ids` 时重建记录目录中的全部文章。只新增或修改少数论文时，用 `--ids`；不需要重跑训练、仿真或所有文献的文字分析。`render_manifest.json` 记录本次输出的源/记录/渲染器/成品哈希、页数和字体，便于追踪；它只描述本次调用，不是累计数据库。

输入源哈希变化时脚本会拒绝继续：先检查是否换了预印本/出版版、页码或图号；重新确认所有裁图，再更新指纹。不得为了让校验通过而无检查地替换哈希。

## 自动与人工验收分工

`check_reviews.py` 检查：正文与五段结论存在；原文页码说明、全部性能标题/说明存在；预期图像数量；页脚当前页/总页数；页面尺寸。它逐文档隔离渲染，避免本地字体缓存影响检查。可以用 `PDFTOPPM` 指向指定 Poppler；缺失时选择 PDFium。

人工必须继续检查：
- 中文无乱码/缺字，标题、段落、页脚不重叠；长英文题名和 DOI 不越界。
- 路线图/模型图清楚，所有图表与原文对应；没有裁掉表格列、脚注、图例、误差条或续页。
- 数字、单位、数据划分和模型名与原文一致，原文事实与研究建议分开。
- 原文没有性能表时说明原因，综述不冒充新模型实验；没有无出处的评级或建议实验结果。
- 新增论文不重复；现有记录中每项 performance 都已进入成品。

长图默认最多 650 pt 高，短表在约 900 pt 内容高度内合并；单页超过 1440 pt 会要求精简或拆分，不靠无限缩小字号。极长表可按原文连续范围拆为清楚标注的续页，保留表头与完整内容。

自动通过只是结构验收，`report.json` 会明确仍需要视觉检查。最终回复讲清改了哪些内容、生成多少篇、尚有什么真实缺失，提供实际可打开链接；无需列出内部临时文件。
