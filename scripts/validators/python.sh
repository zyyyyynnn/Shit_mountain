#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  printf '[python:error] 缺少 python3。请安装 Python 3.10 或更高版本后重试。\n' >&2
  exit 1
fi

CACHE_DIR="$(mktemp -d)"
trap 'rm -rf "$CACHE_DIR"' EXIT
export PYTHONPYCACHEPREFIX="$CACHE_DIR"

printf '[python] 正在确认缩进地层、测绘设施和目录索引没有位移...\n'

mapfile -d '' PYTHON_FILES < <(
  find scripts exhibits -type f -name '*.py' -not -path '*/__pycache__/*' -print0
)

if [[ ${#PYTHON_FILES[@]} -eq 0 ]]; then
  printf '[python:error] 未发现 Python 文件；检查器无法确认这层地质是否存在。\n' >&2
  exit 1
fi

if ! python3 -m compileall -q scripts; then
  printf '[python:error] Python 基础设施语法检查失败。上方诊断包含具体文件和行号。\n' >&2
  exit 1
fi

if ! python3 -m unittest discover -s scripts/tests -p 'test_*.py'; then
  printf '[python:error] Python 回归测试失败。\n' >&2
  exit 1
fi

if ! python3 scripts/docs_generator.py --check; then
  printf '[python:error] 生成文档与展品声明不一致。请运行 python3 scripts/docs_generator.py --write。\n' >&2
  exit 1
fi

if ! python3 scripts/exhibit_runner.py --language python; then
  printf '[python:error] Python 展品的隔离编译、运行或行为合同失败。\n' >&2
  exit 1
fi

printf '[python:ok] %s 个 Python 文件通过基础设施测试、隔离运行、行为合同与文档漂移检查。\n' "${#PYTHON_FILES[@]}"
