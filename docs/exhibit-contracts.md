# 展品合同与受限执行

每个正式展品必须在展品根目录提供 `exhibit.json`。该文件描述语言、坏版和修复版入口、运行时限以及行为合同。语言检查器不再维护具体类名或脚本路径。

## 最小声明

```json
{
  "schema_version": 1,
  "id": "001",
  "slug": "if-else-volcano",
  "language": "java",
  "timeout_seconds": 5,
  "bad": {
    "source_dir": "bad",
    "entrypoint": "ShitDiscountCalculator"
  },
  "fixed": {
    "source_dir": "fixed",
    "entrypoint": "CleanDiscountCalculator"
  },
  "contract": {
    "type": "equal-output",
    "expected": "70"
  }
}
```

路径必须是展品目录内的相对路径。绝对路径和 `..` 路径穿越会被拒绝。默认超时为 5 秒，允许范围为 1 到 30 秒。

## 入口规则

### Java

- `source_dir` 指向包含 Java 源码的目录。
- 执行器会递归发现该目录内的 `.java` 文件。
- 坏版和修复版分别编译到独立 classpath。
- `entrypoint` 是包含 `public static void main` 的完整类名。

### Python

- `source_dir` 指向该版本的源码目录。
- 整个目录会复制到一次性临时工作区。
- `entrypoint` 是相对于 `source_dir` 的脚本路径。
- 执行前先运行 `compileall`，然后执行入口脚本。

## 合同类型

### `equal-output`

适用于行为保持型重构。坏版与修复版都必须成功，而且标准输出必须相同。

```json
{
  "type": "equal-output",
  "expected": "70"
}
```

`expected` 可省略；提供后，两个版本的共同输出还必须与它一致。

### `expected-difference`

适用于缺陷修复。坏版与修复版都必须成功，但各自必须产生明确且不同的输出。

```json
{
  "type": "expected-difference",
  "expected_bad": "contaminated=yes",
  "expected_fixed": "isolated=yes"
}
```

该合同防止“修复版仍然有问题”，也防止坏版无法继续复现教学场景。

### `expected-failure`

适用于故意展示编译失败或运行失败的展品。目标版本必须在指定阶段失败，诊断中必须包含稳定文本；另一个版本必须成功。

```json
{
  "type": "expected-failure",
  "variant": "bad",
  "phase": "compile",
  "contains": "SyntaxError",
  "expected_other": "fixed"
}
```

`phase` 只能描述执行器实际报告的阶段，例如 `compile` 或 `run`。

## 执行边界

执行器会：

- 为每个展品、每个版本创建独立临时目录；
- 分别编译坏版和修复版，避免 classpath 污染；
- 在临时工作目录中运行，不把当前目录设为仓库；
- 清理大部分环境变量，不向展品传递 GitHub Token；
- 设置运行超时；
- 将标准输出与错误输出总量限制为 65536 字节；
- 执行后删除临时目录。

当前执行器**不是操作系统级沙箱**。它没有承诺阻断网络或系统调用，因此仍然禁止提交恶意载荷、资源消耗攻击、网络探测和破坏性代码。CI 使用只读仓库权限，且不得向展品提供项目密钥。

## 本地命令

运行所有正式展品：

```bash
python3 scripts/exhibit_runner.py
```

只运行某种语言：

```bash
python3 scripts/exhibit_runner.py --language java
python3 scripts/exhibit_runner.py --language python
```

查看发现结果而不执行：

```bash
python3 scripts/exhibit_runner.py --list
```
