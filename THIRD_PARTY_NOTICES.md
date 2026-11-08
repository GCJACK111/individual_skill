# PDF 辅助工具的第三方组件

主技能与辅助工具代码沿用仓库 MIT 许可证。以下第三方组件分别适用其原始许可证；完整离线 HTML 内也嵌有相应许可文本。

| 组件 | 来源与版本 | 许可证 |
| --- | --- | --- |
| pdfmake | npm `pdfmake@0.2.23`，https://github.com/bpampuch/pdfmake | MIT，见 `tools/vendor/pdfmake-LICENSE.txt` |
| markdown-it | npm `markdown-it@14.1.0`，https://github.com/markdown-it/markdown-it | MIT，见 `tools/vendor/markdown-it-LICENSE.txt` |
| Noto Sans SC | https://github.com/google/fonts/tree/main/ofl/notosanssc | SIL Open Font License 1.1，见 `assets/fonts/OFL.txt` |

字体上游变量文件 `NotoSansSC[wght].ttf` 的 SHA-256 为 `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da`。附带的 Regular 与 Bold 是使用 fontTools 将其 `wght` 轴分别实例化为 400 和 700 的静态 TrueType 文件，未修改字形；未使用许可中的保留名称 “Source” 命名字体。

`tools/pdf-export.html` 是可直接运行的离线成品。维护者修改 `tools/pdf-export.template.html` 后运行 `python3 scripts/build_browser_helper.py`，即可由仓库内依赖和字体重建，不必联网。Python 命令行工具使用 `requirements.txt` 列出的依赖。
