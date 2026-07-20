#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

for command_name in javac java python3; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf '[java:error] 缺少 %s。Java 展品需要 JDK 17+ 与 Python 3.10+ 的合同执行器。\n' "$command_name" >&2
    exit 1
  fi
done

printf '[java] 正在逐展品检测企业级熔岩...\n'

LEGACY_BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$LEGACY_BUILD_DIR"' EXIT

if ! javac -encoding UTF-8 -d "$LEGACY_BUILD_DIR" shit_demo.java; then
  printf '[java:error] 镇山之屎无法独立编译。\n' >&2
  exit 1
fi

legacy_output="$({
  LEGACY_BUILD_DIR="$LEGACY_BUILD_DIR" python3 - <<'PY'
import os
import subprocess
import sys

build_dir = os.environ["LEGACY_BUILD_DIR"]
environment = {
    "PATH": os.environ.get("PATH", ""),
    "HOME": build_dir,
    "TMPDIR": build_dir,
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
}
if os.environ.get("JAVA_HOME"):
    environment["JAVA_HOME"] = os.environ["JAVA_HOME"]

try:
    result = subprocess.run(
        ["java", "-cp", build_dir, "shit_demo"],
        cwd=build_dir,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=5,
        check=False,
    )
except subprocess.TimeoutExpired:
    print("[java:error] 镇山之屎运行超过 5 秒。", file=sys.stderr)
    raise SystemExit(1)

if result.returncode != 0:
    print(result.stderr, file=sys.stderr)
    raise SystemExit(result.returncode)
if len(result.stdout.encode("utf-8")) + len(result.stderr.encode("utf-8")) > 65536:
    print("[java:error] 镇山之屎输出超过 65536 字节。", file=sys.stderr)
    raise SystemExit(1)
print(result.stdout.strip())
PY
} )"

[[ "$legacy_output" == *"Hello Shitmountain"* ]] || {
  printf '[java:error] 镇山之屎失去响应：%s\n' "$legacy_output" >&2
  exit 1
}

if ! python3 scripts/exhibit_runner.py --language java; then
  printf '[java:error] Java 展品的隔离编译、运行或行为合同失败。\n' >&2
  exit 1
fi

printf '[java:ok] 镇山之屎与全部 Java 展品通过独立编译、受限运行和行为合同检查。\n'
