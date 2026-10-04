# 高性价比人生指南Skills

把《高性价比人生指南》的知识用到眼前的一次具体选择：**做不做、买不买、选哪个、先处理什么。**

这个 Skill 会结合你的目标、预算、时间和可承受风险，查阅完整书中条目，再给出有条件的建议、依据和下一步。适用于借钱担保、辞职转行、培训消费、租房等生活选择。

这是独立制作的决策助手，**不是原书作者的官方版本**。原书由 [eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter) 维护，感谢原作者及贡献者。

## 快速开始

以 Codex 为例，将本仓库克隆到个人技能目录，并保留目录名 `life-decision-assistant`：

Windows PowerShell：

```powershell
git clone https://github.com/anshuyi/how-to-live-better-skills.git "$env:USERPROFILE/.codex/skills/life-decision-assistant"
```

macOS / Linux：

```bash
git clone https://github.com/anshuyi/how-to-live-better-skills.git "$HOME/.codex/skills/life-decision-assistant"
```

如果设置了 `CODEX_HOME`，使用该目录下的 `skills/life-decision-assistant`。已有同名目录时先检查本地改动，不要覆盖。也可以下载仓库 ZIP，解压后将含 `SKILL.md` 的目录命名为 `life-decision-assistant`，放到对应技能目录。

安装后开启新会话；如果技能列表尚未刷新，重启 Codex。显示名称是“高性价比人生指南Skills”，调用标识是 `$life-decision-assistant`。

直接说：

> 请用 $life-decision-assistant 帮我判断：我想辞职报一个培训班，但不知道值不值得。

或者一次提供条件：

> 用高性价比人生指南Skills分析这件事。我的目标是……，目前有 A、B 两个选择，预算是……，需要在……之前决定，最不能接受的是……。请告诉我更适合哪个、决定前要确认什么、现在先做哪一步。

## 它怎么工作

**明确决定 → 必要时补条件 → 查完整条目 → 判断适用性与时效 → 比较选择 → 给建议和下一步。**

- 信息够用就直接分析；必要时集中问一至三个关键问题。
- 先看用户条件和适用范围，再比较成本收益。
- 区分书中依据、已核实的最新信息和针对用户情况的判断。
- 结果可以是选择一个方案、暂缓、补充信息或先做可退出的小试验。
- 用户补充条件后重新判断；默认不会替用户转账、签约、报名或联系他人。

例如，用户给出两个租房方案：A 每月 2500 元、单程通勤 70 分钟；B 每月 3200 元、单程 20 分钟。若每月通勤 22 天、两个方案都在预算内，且用户最重视陪孩子，助手可比较“每月多付 700 元，少通勤约 36.7 小时”。这是用户数据与偏好的计算，不冒充原书结论；合同和其他总支出仍需核对。

## 本地资料与依赖

- 内置原书 **34 章、654 条建议**，以及相关长文和作者核实笔记。
- 取材日期：**2026-10-04**；固定提交：`bd25430e9a380bdd3b9af728fcfc39daff31f8d2`。
- 原文按字节保留，来源文件哈希记录在 [snapshot.json](references/snapshot.json)。
- 本地检索脚本需要 **Python 3.9+**，只用标准库，不需要 API Key。没有 Python 时，助手可使用文件工具读取和搜索正文。
- 运行本 Skill 的 AI 服务仍使用你自己的模型环境。政策、价格、金额、期限等需要时效核实；离线时明确标注待核实项。

## 文件结构

```text
SKILL.md                       主流程、适用场景和输出要求
agents/openai.yaml             Codex 展示名称和启动提示
scripts/search_book.py         本地搜索、全文读取与完整性检查
references/decision-method.md  比较方法、必要追问和条件变化后的复判
references/book-index.md       场景与章节索引
references/source-policy.md    来源、引用和版本更新办法
references/book/               原书章节
references/docs/               原书长文与核实笔记
references/snapshot.json       固定版本和来源文件 SHA-256
tests/test_retrieval.py         检索与完整性回归测试
ATTRIBUTION.md                  署名与改动说明
```

## 检索与验证

在仓库根目录执行：

```bash
python scripts/search_book.py search 培训 证书 --chapter 23 --limit 6
python scripts/search_book.py read 23:8
python scripts/search_book.py check
python -m unittest discover -s tests -v
```

搜索仅返回条目位置；`read` 才返回完整条目、备注和章节说明。每个结果提供固定版本的 GitHub 原文链接。搜索次序是文字相关性，不是建议优先级。

已通过 17 项自动测试，覆盖原文提取和引用、限制条件、中文路径、空输入、无命中、文件缺失及内容校验；并完成人工场景走查。自动测试不代表所有生活判断已通过独立模型评测，也不代表全书每条医学或法律结论均已独立复核。

## 贡献与更新

欢迎提交可复现的问题或改进建议。描述输入、期望行为和实际差异即可，请去掉个人隐私信息。修改检索程序后运行上述测试。更新原书快照时，按 [来源规则](references/source-policy.md) 同步正文、索引、版本与哈希，不混合多个版本。

## 开源许可

- **本项目新增代码、Skill 指令、索引和说明文档：MIT**，见 [LICENSE](LICENSE)。
- **原书内容**（`references/book/`、`references/docs/`、`references/README.md`）：沿用 **CC BY 4.0**，见 [原书许可](references/LICENSE)。转载或改编时保留原书署名、来源、许可证链接并注明改动。
- 上游 Skill 的 MIT 许可及版权声明保存在 [references/LICENSE-CODE](references/LICENSE-CODE)。

更多来源和改动说明见 [ATTRIBUTION.md](ATTRIBUTION.md)。根目录 MIT 许可不替代原书的 CC BY 4.0。
