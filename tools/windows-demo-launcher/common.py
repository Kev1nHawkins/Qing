from __future__ import annotations

import datetime as dt
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


REQUIRED_IMAGES = (
    "lingchao/backend:demo",
    "lingchao/frontend-user:demo",
    "lingchao/frontend-admin:demo",
    "mysql:8.4",
)
COMPOSE_FILES = ("docker-compose.yml", "docker-compose.demo.yml")


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def state_dir() -> Path:
    """Return a per-user writable directory even when the package is read-only."""
    candidates: list[Path] = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "LingchaoCoCreateDemo")
    candidates.append(Path(tempfile.gettempdir()) / "LingchaoCoCreateDemo")

    errors: list[str] = []
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write-test"
            probe.write_text("ok", encoding="ascii")
            probe.unlink(missing_ok=True)
            return candidate
        except OSError as exc:
            errors.append(f"{candidate}: {exc}")
    raise RuntimeError("无法创建用户运行目录：" + "；".join(errors))


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")
    if os.name == "nt":
        os.system("chcp 65001 >NUL")


def print_status(message: str) -> None:
    print(f"\n[岭潮共创] {message}", flush=True)


def pause_if_needed(no_pause: bool) -> None:
    if not no_pause:
        try:
            input("\n按回车键关闭此窗口……")
        except EOFError:
            pass


def docker_executable() -> str | None:
    found = shutil.which("docker")
    if found:
        return found
    candidate = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe"
    return str(candidate) if candidate.is_file() else None


def run(command: list[str], cwd: Path, timeout: int | None = None, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        timeout=timeout,
        check=False,
    )


def docker_ready(docker: str, root: Path) -> bool:
    try:
        return run([docker, "info"], root, timeout=15).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def docker_desktop_running(root: Path) -> bool:
    result = run(["tasklist", "/FI", "IMAGENAME eq Docker Desktop.exe", "/NH"], root, timeout=10)
    return result.returncode == 0 and "Docker Desktop.exe" in (result.stdout or "")


def start_docker_desktop(root: Path) -> bool:
    if docker_desktop_running(root):
        return True
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Docker" / "Docker" / "Docker Desktop.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Docker" / "Docker Desktop.exe",
    ]
    desktop = next((path for path in candidates if path.is_file()), None)
    if desktop is None:
        return False
    subprocess.Popen([str(desktop)], cwd=str(desktop.parent))
    return True


def wait_for_docker(docker: str, root: Path, timeout_seconds: int = 120) -> bool:
    if docker_ready(docker, root):
        return True
    print_status("Docker Engine 尚未启动，正在启动 Docker Desktop……")
    if not start_docker_desktop(root):
        return False
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if docker_ready(docker, root):
            return True
        time.sleep(5)
    return False


def image_exists(docker: str, image: str, root: Path) -> bool:
    return run([docker, "image", "inspect", image], root, timeout=20).returncode == 0


def ensure_images(docker: str, root: Path) -> None:
    missing = [image for image in REQUIRED_IMAGES if not image_exists(docker, image, root)]
    if not missing:
        print_status("演示镜像已就绪，跳过导入。")
        return
    archive = root / "docker-images" / "lingchao-demo-images.tar"
    if not archive.is_file():
        raise RuntimeError(f"缺少离线镜像文件：{archive}")
    print_status("首次启动正在导入演示环境，请稍候……")
    result = run([docker, "load", "-i", str(archive)], root, timeout=1800, capture=False)
    if result.returncode != 0:
        raise RuntimeError("离线镜像导入失败。")
    still_missing = [image for image in REQUIRED_IMAGES if not image_exists(docker, image, root)]
    if still_missing:
        raise RuntimeError("镜像导入后仍缺少：" + "、".join(still_missing))


def ensure_runtime_env(root: Path) -> Path:
    runtime = state_dir() / ".env.demo.runtime"
    if runtime.is_file():
        return runtime
    template = root / ".env.demo.example"
    if not template.is_file():
        raise RuntimeError(f"缺少演示环境模板：{template}")
    content = template.read_text(encoding="utf-8")
    content = content.replace("__GENERATE_RANDOM_JWT_SECRET__", secrets.token_urlsafe(64))
    runtime.write_text(content, encoding="utf-8", newline="\n")
    return runtime


def compose_command(docker: str, root: Path, *arguments: str) -> list[str]:
    command = [docker, "compose", "--project-name", "lingchao-demo"]
    for filename in COMPOSE_FILES:
        path = root / filename
        if not path.is_file():
            raise RuntimeError(f"缺少演示运行文件：{path}")
        command.extend(["-f", str(path)])
    command.extend(["--env-file", str(ensure_runtime_env(root))])
    command.extend(arguments)
    return command


def http_ready(url: str, timeout: float = 4) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 500
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def mysql_ready(docker: str, root: Path) -> bool:
    result = run(
        [docker, "inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}", "lingchao-demo-mysql"],
        root,
        timeout=15,
    )
    return result.returncode == 0 and (result.stdout or "").strip() == "healthy"


def wait_for_services(docker: str, root: Path, timeout_seconds: int = 180) -> tuple[bool, str]:
    checks = (
        ("MySQL", lambda: mysql_ready(docker, root)),
        ("Backend", lambda: http_ready("http://127.0.0.1:8000/health")),
        ("用户端", lambda: http_ready("http://127.0.0.1:5173")),
        ("管理端", lambda: http_ready("http://127.0.0.1:5174")),
    )
    deadline = time.monotonic() + timeout_seconds
    for name, check in checks:
        print_status(f"正在等待 {name}……")
        while time.monotonic() < deadline:
            if check():
                print(f"  √ {name} 已就绪", flush=True)
                break
            time.sleep(3)
        else:
            return False, name
    return True, ""


def write_failure_logs(docker: str, root: Path) -> Path:
    log_dir = state_dir() / "launcher-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = log_dir / f"startup-failure-{stamp}.log"
    sections: list[str] = []
    for title, args in (
        ("docker compose ps", ("ps",)),
        ("mysql logs", ("logs", "--tail", "100", "mysql")),
        ("backend logs", ("logs", "--tail", "100", "backend")),
        ("frontend-user logs", ("logs", "--tail", "100", "frontend-user")),
        ("frontend-admin logs", ("logs", "--tail", "100", "frontend-admin")),
    ):
        try:
            result = run(compose_command(docker, root, *args), root, timeout=90)
            sections.append(f"===== {title} =====\n{result.stdout or ''}")
        except Exception as exc:  # Diagnostic collection must not hide the original failure.
            sections.append(f"===== {title} =====\n{exc}")
    destination.write_text("\n\n".join(sections), encoding="utf-8")
    return destination
