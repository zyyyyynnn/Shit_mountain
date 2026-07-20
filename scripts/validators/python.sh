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

printf '[python] 正在确认缩进地层没有位移...\n'

mapfile -d '' PYTHON_FILES < <(
  find scripts exhibits -type f -name '*.py' -not -path '*/__pycache__/*' -print0
)

if [[ ${#PYTHON_FILES[@]} -eq 0 ]]; then
  printf '[python:error] 未发现 Python 文件；检查器无法确认这层地质是否存在。\n' >&2
  exit 1
fi

if ! python3 -m compileall -q scripts exhibits; then
  printf '[python:error] Python 语法检查失败。上方诊断包含具体文件和行号。\n' >&2
  exit 1
fi

if ! python3 -m unittest discover -s scripts/tests -p 'test_*.py'; then
  printf '[python:error] Python 回归测试失败。\n' >&2
  exit 1
fi

if ! python3 scripts/smi.py --check; then
  printf '[python:error] SMI 排行榜与事故现场不一致。请运行 python3 scripts/smi.py --write。\n' >&2
  exit 1
fi

swamp_bad_output="$(python3 exhibits/python/003-mutable-default-swamp/bad/mutable_default_swamp.py)"
swamp_fixed_output="$(python3 exhibits/python/003-mutable-default-swamp/fixed/mutable_default_swamp.py)"

expected_swamp_bad='first=inspect-volcano|second=inspect-volcano,repair-bridge|contaminated=yes'
expected_swamp_fixed='first=inspect-volcano|second=repair-bridge|isolated=yes'

[[ "$swamp_bad_output" == "$expected_swamp_bad" ]] || {
  printf '[python:error] 可变默认参数沼泽没有复现预期污染：%s\n' "$swamp_bad_output" >&2
  exit 1
}

[[ "$swamp_fixed_output" == "$expected_swamp_fixed" ]] || {
  printf '[python:error] 沼泽排水后仍存在跨调用污染：%s\n' "$swamp_fixed_output" >&2
  exit 1
}

printf '[python:ok] %s 个 Python 文件通过语法、测试、行为合同与 SMI 漂移检查。\n' "${#PYTHON_FILES[@]}"
