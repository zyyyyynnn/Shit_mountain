#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

for command_name in javac java; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf '[java:error] 缺少 %s。请安装 JDK 17 或更高版本后重试。\n' "$command_name" >&2
    exit 1
  fi
done

BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$BUILD_DIR"' EXIT

printf '[java] 正在检测企业级熔岩与祖传类文件...\n'

mapfile -d '' JAVA_FILES < <(
  find . -type f -name '*.java' -not -path './.git/*' -print0
)

if [[ ${#JAVA_FILES[@]} -eq 0 ]]; then
  printf '[java:error] 未发现 Java 文件；检查器无法确认这层地质是否存在。\n' >&2
  exit 1
fi

if ! javac -encoding UTF-8 -d "$BUILD_DIR" "${JAVA_FILES[@]}"; then
  printf '[java:error] javac 编译失败。上方诊断包含具体文件和行号。\n' >&2
  exit 1
fi

legacy_output="$(java -cp "$BUILD_DIR" shit_demo)"
volcano_bad_output="$(java -cp "$BUILD_DIR" ShitDiscountCalculator)"
volcano_fixed_output="$(java -cp "$BUILD_DIR" CleanDiscountCalculator)"
god_object_bad_output="$(java -cp "$BUILD_DIR" EverythingManagerFinalV2)"
god_object_fixed_output="$(java -cp "$BUILD_DIR" CompanyOperations)"

[[ "$legacy_output" == *"Hello Shitmountain"* ]] || {
  printf '[java:error] 镇山之屎失去响应：%s\n' "$legacy_output" >&2
  exit 1
}

[[ "$volcano_bad_output" == "70" ]] || {
  printf '[java:error] 火山原始喷发结果异常：%s\n' "$volcano_bad_output" >&2
  exit 1
}

[[ "$volcano_fixed_output" == "$volcano_bad_output" ]] || {
  printf '[java:error] 火山铲屎后业务结果漂移：bad=%s fixed=%s\n' \
    "$volcano_bad_output" "$volcano_fixed_output" >&2
  exit 1
}

expected_empire_output='ORDER-1001|PAID|stock=7|mail=sent|audit=1'
[[ "$god_object_bad_output" == "$expected_empire_output" ]] || {
  printf '[java:error] 王座厅原始政令异常：%s\n' "$god_object_bad_output" >&2
  exit 1
}

[[ "$god_object_fixed_output" == "$god_object_bad_output" ]] || {
  printf '[java:error] 帝国解体后业务结果漂移：bad=%s fixed=%s\n' \
    "$god_object_bad_output" "$god_object_fixed_output" >&2
  exit 1
}

printf '[java:ok] %s 个 Java 文件通过编译与行为合同检查。\n' "${#JAVA_FILES[@]}"
