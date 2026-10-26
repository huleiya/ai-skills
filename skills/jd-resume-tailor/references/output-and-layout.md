# 内容源与排版

## 命令

脚本依赖 Python 3.10+、reportlab、pypdf。优先用宿主已安装依赖，不要求用户使用指定机器路径。

```text
python <skill>/scripts/render_resume.py resume.json --out-dir <output> --text-only
python <skill>/scripts/render_resume.py resume.json --out-dir <output>
```

第一次只写文字供语义审阅；第二次从同源生成 PDF，并确认已有文字与输入一致。已存在且不一致的输出需要新版本目录，或用户明确修改该版本时加 `--overwrite`。

可选参数：`--font <ttf/ttc>`、`--bold-font <ttf/ttc>`、`--body-size 10.2`、`--accent '#16324f'`、`--max-pages 2`。字体未安装或不包含所需字符会失败，不能静默输出缺字 PDF。

Windows 自动使用微软雅黑；macOS/Linux 自动尝试已知的可嵌入 TrueType 中文字体。自动查找失败时传入实际已安装、允许嵌入的字体。不要把操作系统字体复制进 Git。`--preview` 只用于样式测试，在页脚标注“样式预览 / 非投递简历”，正式导出不加它。

## JSON 结构

参考 [assets/sample-resume.json](../assets/sample-resume.json)，此文件为虚构排版样例，不能用作用户经历来源。

```json
{
  "name": "从原简历读取",
  "target": "求职方向",
  "contact": ["电话", "邮箱", "求职城市"],
  "summary": "可省略的简短定位",
  "sections": [
    {
      "title": "项目经历",
      "items": [
        {
          "title": "项目名称",
          "subtitle": "角色或合作性质",
          "period": "经确认的时间",
          "stack": "代码中使用的相关技术",
          "description": "简短业务背景",
          "bullets": [
            {"label": "检索链路", "text": "具体动作、方案和可验证价值。"}
          ]
        }
      ]
    }
  ]
}
```

`name`、`target`、`sections` 为必填；每节至少一个 item，item 至少有 `title` 或 bullets。其余字段可省略。bullets 也可直接使用字符串；label 以粗体显示。所有字符串是普通文本，HTML 会被转义。不往 JSON 放审阅证据或内部标签，因为其中的展示字段会进入 PDF。

单一阅读顺序适合中文技术简历。小标题与下一段绑定，短条目适当留白；长项目允许跨页，但每条 bullet 尽量不拆开。首选 2–3 个项目，保留教育和真实实习，按岗位调整章节顺序。技能列表以具体应用为主，不画熟练度进度条。

## 辅助文件

`evidence.md` 表格建议列：条目 ID、JD 要求、最终表述、仓库/版本、路径:行号与符号、当前可达性、验证情况。只记录和本次简历有关的最小证据，不搬运密钥/客户数据/完整私有源码。

`interview-prep.md` 逐条对应：30 秒讲法、2–3 个追问、要看的源码、实践准备动作。写“需要准备”不代表自动断言用户没做过。指标没有测量证据就从正式简历删掉，并说明以后如何实测，不预填理想数字。

## 验证与修复

脚本验证字段类型、中文字体覆盖、PDF 正文完整性、A4 和最大页数，失败不替换现有 PDF。它不会验证简历事实或像素排版。生成后用 pdfplumber/Poppler 渲染每页，逐页查看；如果行距、分页或强调色不合适，调整内容或模板再导出，再对最终 PDF 验收。
