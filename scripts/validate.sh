#!/usr/bin/env bash
set -euo pipefail

BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$BUILD_DIR"' EXIT

printf '🔍 正在扫描山体中的 Java 化石...\n'

mapfile -d '' JAVA_FILES < <(find . -type f -name '*.java' -not -path './.git/*' -print0)

if [[ ${#JAVA_FILES[@]} -eq 0 ]]; then
  printf '❌ 山上居然一坨 Java 都没有。\n' >&2
  exit 1
fi

javac -encoding UTF-8 -d "$BUILD_DIR" "${JAVA_FILES[@]}"

legacy_output="$(java -cp "$BUILD_DIR" shit_demo)"
bad_output="$(java -cp "$BUILD_DIR" ShitDiscountCalculator)"
fixed_output="$(java -cp "$BUILD_DIR" CleanDiscountCalculator)"

[[ "$legacy_output" == *"Hello Shitmountain"* ]] || {
  printf '❌ 镇山之屎失去响应。\n' >&2
  exit 1
}

[[ "$bad_output" == "70" ]] || {
  printf '❌ 火山原始喷发结果异常：%s\n' "$bad_output" >&2
  exit 1
}

[[ "$fixed_output" == "70" ]] || {
  printf '❌ 铲屎后业务结果发生漂移：%s\n' "$fixed_output" >&2
  exit 1
}

printf '✅ 山体稳定：%s 个 Java 展品至少还能跑。\n' "${#JAVA_FILES[@]}"
