# 屎山贡献指南 / Shoveling Manual

感谢你准备为山区增加新的地质灾害。

本项目欢迎**有教育价值的坏代码**，不欢迎没有说明、不能复现或带有真实危害的代码。

## 1. 展品目录

每个正式案例使用独立目录：

```text
exhibits/<language>/<number>-<slug>/
├── exhibit.json
├── README.md
├── bad/
└── fixed/
```

推荐编号从现有最大编号继续递增。目录名使用小写英文和连字符。

## 2. 展品声明

`exhibit.json` 是展品的唯一机器可读信息源，必须声明：

- 展品编号、slug 和语言；
- `catalog.title`、`catalog.summary`、`catalog.smells` 与 `catalog.status`；
- 坏版与修复版的源码目录和入口；
- 1 到 30 秒的运行时限；
- `equal-output`、`expected-difference` 或 `expected-failure` 行为合同；
- 必要的预期输出或稳定失败诊断。

目录页、README 概览和 SMI 文档均从展品声明与代码自动生成。不要在多个 Markdown 文件中重复手工维护展品表格。

完整合同格式见 [`docs/exhibit-contracts.md`](docs/exhibit-contracts.md)。路径必须位于展品目录内，禁止绝对路径和 `..` 路径穿越。

执行器会为每个版本创建独立临时目录、限制运行时间和输出量，并清理大部分环境变量。它不是操作系统级沙箱，因此仍然禁止网络探测、过度资源消耗和破坏性代码。

## 3. 展品牌必须写什么

展品自己的 `README.md` 至少包括：

- **案发现场**：代码试图解决什么问题；
- **主要罪名**：具体的代码异味或反模式；
- **爆炸姿势**：需求变化时，它会怎样失控；
- **铲屎路线**：建议的重构步骤，而不只是“全部重写”；
- **运行方法**：如何编译、执行或验证；
- **行为合同**：为什么属于保持行为、修复缺陷或预期失败；
- **屎山指数解读**：解释自动评分中最主要的异味来源。

根 README 不再收录每个展品的详细介绍。详细内容应留在展品目录中。

## 4. 坏代码的质量标准

坏代码也要有职业道德：

- 可以难读，但应当能运行或明确标记为 `expected-failure`；
- 可以有魔法数字，但不能包含真实密钥；
- 可以模拟事故，但不能破坏用户机器、网络或数据；
- 可以展示安全反模式，但必须使用无害、隔离的示例；
- 不得上传个人信息、第三方私有代码或来源不明的大段复制内容；
- 不得提交明显消耗计算、内存、磁盘或网络资源的代码。

## 5. 生成项目文档

新增或修改展品后，统一执行：

```bash
python3 scripts/docs_generator.py --write
```

该命令维护：

- README 中固定长度的景区概览；
- [`docs/EXHIBITS.md`](docs/EXHIBITS.md) 完整展品目录；
- [`docs/SMI.md`](docs/SMI.md) 计分规则与完整排行榜。

提交前检查生成结果没有漂移：

```bash
python3 scripts/docs_generator.py --check
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

`python3 scripts/smi.py --write` 与 `--check` 保留为兼容入口，内部同样维护全部生成文档。

SMI 是透明的启发式评分，只用于教育、娱乐和代码审查训练。不得使用分数羞辱贡献者，也不得为了冲榜加入没有教学价值的噪声。

## 6. 注册新的 SMI 语言适配器

SMI 将语言无关逻辑放在 `scripts/smi_engine/core.py`，语言指标放在独立适配器中：

```text
scripts/smi_engine/
├── core.py
├── java.py
├── python.py
└── registry.py
```

新增语言适配器时：

1. 实现稳定的 `language`、`display_name` 与 `extensions`；
2. 提供 `legacy_exhibits(root)`；没有历史展品时返回空元组；
3. 提供 `analyze_sources(sources)`，返回“指标名称 → 非负分值”的字典；
4. 只在适配器中使用语言专用解析、AST 或正则，禁止把语言规则塞进 `core.py`；
5. 在 `registry.py` 注册适配器；注册结果按语言名稳定排序；
6. 为语言专用异味、现有基准分和排行榜语言列增加回归测试；
7. 在 [`docs/SMI.md`](docs/SMI.md) 中公开指标、权重和单项上限。

核心层负责展品发现、总分封顶、危险等级和稳定排序。适配器不得自行修改文档，也不得调用网络、外部 AI 或付费分析服务。

## 7. 注册新的语言检查器

多语言安检使用目录注册机制：

```text
scripts/validators/
├── java.sh
└── python.sh
```

新增语言时，在该目录创建 `<language>.sh`。`scripts/validate.sh` 会按文件名排序发现并执行所有检查器，不需要修改中央 `case` 或维护硬编码入口列表。

每个检查器必须：

1. 可以通过 `bash scripts/validators/<language>.sh` 独立执行；
2. 使用 `set -euo pipefail`，并从脚本位置解析仓库根目录；
3. 在运行前检查必要运行时，缺失时给出明确安装提示；
4. 运行语言基础设施测试，然后调用 `scripts/exhibit_runner.py --language <language>`；
5. 使用 `[language]`、`[language:error]`、`[language:ok]` 格式输出；
6. 不使用管道下载或执行远程脚本；
7. 不下载或执行来源不明的二进制文件与代码。

检查器可以有自己的景区广播，但错误必须指出失败的命令、文件或修复方式。搞怪文案不能覆盖真正的诊断输出。

## 8. PR 命名

请选择一种景区通行证：

- `[展品] add callback pyramid disaster`
- `[铲屎] refactor the volcanic discount calculator`
- `[景区建设] add CI mountain inspection`
- `[紧急封山] fix a dangerous example`

## 9. 提交前验山

```bash
bash scripts/validate.sh
```

并确认：

- [ ] 展品有说明文档和 `exhibit.json`；
- [ ] `catalog` 元数据能够准确概括展品；
- [ ] `bad/` 的问题不是只靠故意拼错变量名制造的；
- [ ] `fixed/` 或重构路线确实改善了问题；
- [ ] 行为合同类型和预期输出准确；
- [ ] README、完整目录与 SMI 文档已经重新生成；
- [ ] 没有真实密钥、恶意载荷、过度资源消耗或破坏性命令；
- [ ] 新增源码能在独立临时目录和声明时限内通过对应语言检查器；
- [ ] 新增语言适配器有独立测试，且核心层没有语言专用规则；
- [ ] 新增语言检查器可以独立执行，并有清晰的运行时缺失提示。

## 10. Review 原则

Review 时优先讨论：

1. 反模式是否真实、清晰、有代表性；
2. 示例是否足够小，读者能快速理解；
3. 修复版本是否只是把屎移动到了另一个目录；
4. 行为合同是否准确表达“保持、修复或预期失败”；
5. 自动评分是否与人工解释大致一致；
6. 目录元数据是否适合公开索引；
7. 搞怪文案是否帮助理解，而不是掩盖技术内容。

最后一条山规：**可以笑代码，不要羞辱写代码的人。**
