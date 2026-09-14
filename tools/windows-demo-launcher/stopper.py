from __future__ import annotations

import argparse
import sys

from common import (
    base_dir,
    compose_command,
    configure_console,
    docker_executable,
    ensure_runtime_env,
    pause_if_needed,
    print_status,
    run,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-pause", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    configure_console()
    root = base_dir()
    docker = docker_executable()
    if not docker:
        print_status("未找到 Docker，无法停止服务。")
        pause_if_needed(args.no_pause)
        return 1
    try:
        ensure_runtime_env(root)
        result = run(compose_command(docker, root, "stop"), root, timeout=180, capture=False)
        if result.returncode != 0:
            raise RuntimeError("Docker Compose stop 执行失败。")
    except Exception as exc:
        print_status(f"停止失败：{exc}")
        pause_if_needed(args.no_pause)
        return 1
    print_status("演示服务已安全停止，数据库和上传文件均已保留。")
    pause_if_needed(args.no_pause)
    return 0


if __name__ == "__main__":
    sys.exit(main())
