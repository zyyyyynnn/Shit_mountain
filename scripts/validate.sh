#!/usr/bin/env bash
set -euo pipefail

BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$BUILD_DIR"' EXIT

printf '[smi] 正在校准屎山指数测绘仪...\n'
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 scripts/smi.py --check

printf '[java] 正在扫描山体中的 Java 化石...\n'

mapfile -d '' JAVA_FILES < <(find . -type f -name '*.java' -not -path './.git/*' -print0)

if [[ ${#JAVA_FILES[@]} -eq 0 ]]; then
  printf '[error] 山上居然一坨 Java 都没有。\n' >&2
  exit 1
fi

javac -encoding UTF-8 -d "$BUILD_DIR" "${JAVA_FILES[@]}"

legacy_output="$(java -cp "$BUILD_DIR" shit_demo)"
volcano_bad_output="$(java -cp "$BUILD_DIR" ShitDiscountCalculator)"
volcano_fixed_output="$(java -cp "$BUILD_DIR" CleanDiscountCalculator)"
god_object_bad_output="$(java -cp "$BUILD_DIR" EverythingManagerFinalV2)"
god_object_fixed_output="$(java -cp "$BUILD_DIR" CompanyOperations)"

[[ "$legacy_output" == *"Hello Shitmountain"* ]] || {
  printf '[error] 镇山之屎失去响应。\n' >&2
  exit 1
}

[[ "$volcano_bad_output" == "70" ]] || {
  printf '[error] 火山原始喷发结果异常：%s\n' "$volcano_bad_output" >&2
  exit 1
}

[[ "$volcano_fixed_output" == "$volcano_bad_output" ]] || {
  printf '[error] 火山铲屎后业务结果发生漂移：bad=%s fixed=%s\n' \
    "$volcano_bad_output" "$volcano_fixed_output" >&2
  exit 1
}

expected_empire_output='ORDER-1001|PAID|stock=7|mail=sent|audit=1'
[[ "$god_object_bad_output" == "$expected_empire_output" ]] || {
  printf '[error] 王座厅原始政令异常：%s\n' "$god_object_bad_output" >&2
  exit 1
}

[[ "$god_object_fixed_output" == "$god_object_bad_output" ]] || {
  printf '[error] 帝国解体后业务结果发生漂移：bad=%s fixed=%s\n' \
    "$god_object_bad_output" "$god_object_fixed_output" >&2
  exit 1
}

printf '[ok] 山体稳定：%s 个 Java 文件通过运行检查，SMI 排行榜与代码一致。\n' "${#JAVA_FILES[@]}"
