from __future__ import annotations

import argparse
import os
import sys

from common import (
    compose_command,
    configure_console,
    docker_executable,
    ensure_images,
    ensure_runtime_env,
    pause_if_needed,
    print_status,
    run,
    wait_for_docker,
    wait_for_services,
    write_failure_logs,
    base_dir,
)


USER_URL = "http://127.0.0.1:5173"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-pause", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    configure_console()
    root = base_dir()
    print("岭潮共创\n广州大学岭南文化 AI 共创平台")

    docker = docker_executable()
    if not docker:
        print_status("未找到 Docker。请先安装 Docker Desktop，再重新双击本程序。")
        pause_if_needed(args.no_pause)
        return 1
    if not wait_for_docker(docker, root):
        print_status("Docker Desktop 尚未正常启动，请启动 Docker Desktop 后重新双击本程序。")
        pause_if_needed(args.no_pause)
        return 1

    try:
        ensure_images(docker, root)
        ensure_runtime_env(root)
        print_status("正在启动岭潮共创演示环境……")
        command = compose_command(docker, root, "up", "-d", "--no-build", "--pull", "never")
        result = run(command, root, timeout=300, capture=False)
        if result.returncode != 0:
            raise RuntimeError("Docker Compose 启动失败。")
        ready, failed_service = wait_for_services(docker, root)
        if not ready:
            raise RuntimeError(f"等待 {failed_service} 就绪超时。")
    except Exception as exc:
        print_status(f"启动失败：{exc}")
        try:
            log_path = write_failure_logs(docker, root)
            print(f"诊断日志已保存到：{log_path}")
        except Exception as log_exc:
            print(f"诊断日志收集失败：{log_exc}")
        pause_if_needed(args.no_pause)
        return 1

    print_status("岭潮共创启动成功！")
    print("用户端：http://127.0.0.1:5173")
    print("管理端：http://127.0.0.1:5174")
    print("Swagger：http://127.0.0.1:8000/docs")
    if not args.no_browser:
        os.startfile(USER_URL)
    pause_if_needed(args.no_pause)
    return 0


if __name__ == "__main__":
    sys.exit(main())
