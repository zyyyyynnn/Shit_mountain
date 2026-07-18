#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATORS_DIR="$ROOT_DIR/scripts/validators"
cd "$ROOT_DIR"

if [[ ! -d "$VALIDATORS_DIR" ]]; then
  printf '[dispatch:error] 检查器目录不存在：%s\n' "$VALIDATORS_DIR" >&2
  exit 1
fi

mapfile -t VALIDATORS < <(
  find "$VALIDATORS_DIR" -maxdepth 1 -type f -name '*.sh' | sort
)

if [[ ${#VALIDATORS[@]} -eq 0 ]]; then
  printf '[dispatch:error] 未注册任何语言检查器：%s\n' "$VALIDATORS_DIR" >&2
  exit 1
fi

printf '[dispatch] 已发现 %s 个语言检查器。\n' "${#VALIDATORS[@]}"

for validator in "${VALIDATORS[@]}"; do
  validator_name="$(basename "$validator" .sh)"
  printf '[dispatch] 进入 %s 地质层：%s\n' "$validator_name" "$validator"
  bash "$validator"
done

printf '[ok] 多语言山体安检完成：%s 个检查器全部通过。\n' "${#VALIDATORS[@]}"
