# 屎山贡献指南 / Shoveling Manual

感谢你准备为山区增加新的地质灾害。

本项目欢迎**有教育价值的坏代码**，不欢迎没有说明、不能复现或带有真实危害的代码。

## 1. 展品目录

每个案例使用独立目录：

```text
exhibits/<language>/<number>-<slug>/
├── README.md
├── bad/
└── fixed/
```

推荐编号从现有最大编号继续递增。目录名使用小写英文和连字符。

## 2. 展品牌必须写什么

展品的 `README.md` 至少包括：

- **案发现场**：代码试图解决什么问题。
- **主要罪名**：具体的代码异味或反模式。
- **爆炸姿势**：需求变化时，它会怎样失控。
- **铲屎路线**：建议的重构步骤，而不只是“全部重写”。
- **运行方法**：如何编译、执行或验证。
- **屎山指数解读**：解释自动评分中最主要的异味来源。

## 3. 坏代码的质量标准

坏代码也要有职业道德：

- 可以难读，但应当能运行或明确标记为 `expected-failure`。
- 可以有魔法数字，但不能包含真实密钥。
- 可以模拟事故，但不能破坏用户机器、网络或数据。
- 可以展示安全反模式，但必须使用无害、隔离的示例。
- 不得上传个人信息、第三方私有代码或来源不明的大段复制内容。

## 4. 屎山指数

新增或修改 `bad/` 代码后，更新 README 排行榜：

```bash
python3 scripts/smi.py --write
```

提交前确认生成结果没有漂移：

```bash
python3 scripts/smi.py --check
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

SMI 是透明的启发式评分，只用于教育、娱乐和代码审查训练。不得使用分数羞辱贡献者，也不得为了冲榜加入没有教学价值的噪声。

## 5. 注册新的 SMI 语言适配器

SMI v2 将语言无关逻辑放在 `scripts/smi_engine/core.py`，语言指标放在独立适配器中：

```text
scripts/smi_engine/
├── core.py
├── java.py
├── python.py
└── registry.py
```

新增语言适配器时：

1. 实现稳定的 `language`、`display_name` 与 `extensions`。
2. 提供 `legacy_exhibits(root)`；没有历史展品时返回空元组。
3. 提供 `analyze_sources(sources)`，返回“指标名称 → 非负分值”的字典。
4. 只在适配器中使用语言专用解析、AST 或正则，禁止把语言规则塞进 `core.py`。
5. 在 `registry.py` 注册适配器；注册结果按语言名稳定排序。
6. 为语言专用异味、现有基准分和排行榜语言列增加回归测试。
7. 在 README 中公开指标、权重和单项上限。

核心层负责展品发现、总分封顶、危险等级、稳定排序和 README 生成。适配器不得自行修改 README，也不得调用网络、外部 AI 或付费分析服务。

## 6. 注册新的语言检查器

多语言安检使用目录注册机制：

```text
scripts/validators/
├── java.sh
└── python.sh
```

新增语言时，在该目录创建 `<language>.sh`。`scripts/validate.sh` 会按文件名排序发现并执行所有检查器，不需要修改中央 `case` 或维护硬编码列表。

每个检查器必须：

1. 可以通过 `bash scripts/validators/<language>.sh` 独立执行。
2. 使用 `set -euo pipefail`，并从脚本位置解析仓库根目录。
3. 在运行前检查必要运行时，缺失时给出明确安装提示。
4. 发现该语言的源文件，并在未发现文件时给出可诊断信息。
5. 运行语法、编译、测试或行为合同中适用的检查。
6. 使用 `[language]`、`[language:error]`、`[language:ok]` 格式输出。
7. 不使用 `curl | sh`、`wget | bash` 或其他远程脚本执行方式。
8. 不下载或执行来源不明的二进制文件与代码。

检查器可以有自己的景区广播，但错误必须指出失败的命令、文件或修复方式。搞怪文案不能覆盖真正的诊断输出。

## 7. PR 命名

请选择一种景区通行证：

- `[展品] add callback pyramid disaster`
- `[铲屎] refactor the volcanic discount calculator`
- `[景区建设] add CI mountain inspection`
- `[紧急封山] fix a dangerous example`

## 8. 提交前验山

```bash
bash scripts/validate.sh
```

并确认：

- [ ] 展品有说明文档。
- [ ] `bad/` 的问题不是只靠故意拼错变量名制造的。
- [ ] `fixed/` 或重构路线确实改善了问题。
- [ ] README 中的 SMI 排行榜已重新生成。
- [ ] 没有真实密钥、恶意载荷或破坏性命令。
- [ ] 新增源码能通过对应语言检查器。
- [ ] 新增语言适配器有独立测试，且核心层没有语言专用规则。
- [ ] 新增语言检查器可以独立执行，并有清晰的运行时缺失提示。

## 9. Review 原则

Review 时优先讨论：

1. 反模式是否真实、清晰、有代表性。
2. 示例是否足够小，读者能快速理解。
3. 修复版本是否只是把屎移动到了另一个目录。
4. 自动评分是否与人工解释大致一致。
5. 搞怪文案是否帮助理解，而不是掩盖技术内容。

最后一条山规：**可以笑代码，不要羞辱写代码的人。**
