import json
import os
import platform
import subprocess
import threading
import queue
from pathlib import Path
from typing import Callable, Optional


def is_termux() -> bool:
    return bool(
        os.environ.get("TERMUX_VERSION")
        or os.path.exists("/data/data/com.termux")
        or "com.termux" in os.environ.get("PREFIX", "")
    )


def is_proot() -> bool:
    """Detect proot-distro environment (Ubuntu/Debian inside Termux)."""
    try:
        with open("/proc/version", "r") as f:
            if "proot" in f.read().lower():
                return True
    except (FileNotFoundError, PermissionError):
        pass
    if os.environ.get("PROOT_DISTRO_NAME"):
        return True
    if is_termux():
        return False
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read()
                if any(d in content for d in ("Ubuntu", "Debian")) and os.getuid() == 0:
                    return True
        except (FileNotFoundError, PermissionError):
            pass
    return False


class Installer:
    def __init__(self, json_path: str = None):
        if json_path is None:
            json_path = str(Path(__file__).parent / "packages.json")
        self.json_path = json_path
        self.system = platform.system().lower()
        if is_proot():
            self.platform_key = "linux"
        elif is_termux():
            self.platform_key = "termux"
        elif self.system == "linux":
            self.platform_key = "linux"
        elif self.system == "darwin":
            self.platform_key = "darwin"
        else:
            self.platform_key = "win32"
        self.data = self._load()
        self._sudo_password: Optional[str] = None
        self._sudo_checked = False
        self._needs_sudo = False

    def _load(self) -> dict:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[WARN] Failed to load {self.json_path}: {e}")
            return {"categories": []}

    def save(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_categories(self) -> list:
        return self.data.get("categories", [])

    def get_all_packages(self) -> list:
        result = []
        for cat in self.data.get("categories", []):
            for pkg in cat.get("packages", []):
                result.append({
                    "category_id": cat["id"],
                    "category_name": cat["name"],
                    **pkg,
                })
        return result

    def get_package(self, pkg_id: str) -> Optional[dict]:
        for cat in self.data.get("categories", []):
            for pkg in cat.get("packages", []):
                if pkg["id"] == pkg_id:
                    return {
                        "category_id": cat["id"],
                        "category_name": cat["name"],
                        **pkg,
                    }
        return None

    def is_installed(self, pkg_id: str) -> bool:
        pkg = self.get_package(pkg_id)
        if pkg is None:
            return False
        checks = pkg.get("check", {})
        cmd = checks.get(self.platform_key)
        if not cmd:
            return False
        try:
            shell = self.platform_key != "win32"
            result = subprocess.run(
                cmd, shell=shell, capture_output=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def get_installed_version(self, pkg_id: str) -> Optional[str]:
        pkg = self.get_package(pkg_id)
        if pkg is None:
            return None

        version_cmds = {
            "rust": "rustc --version | grep -oE '[0-9]+\\.[0-9]+(\\.[0-9]+)?'",
            "go": "go version | grep -oE 'go[0-9]+\\.[0-9]+(\\.[0-9]+)?' | sed 's/go//'",
            "node": "node --version | grep -oE '[0-9]+\\.[0-9]+(\\.[0-9]+)?'",
            "bun": "bun --version",
            "uv": "uv --version | grep -oE '[0-9]+\\.[0-9]+(\\.[0-9]+)?'",
            "nvim": "nvim --version | head -1 | grep -oE 'v[0-9]+\\.[0-9]+(\\.[0-9]+)?' | sed 's/v//'",
            "docker": "docker --version | grep -oE '[0-9]+\\.[0-9]+(\\.[0-9]+)?'",
            "tailscale": "tailscale --version | grep -oE '[0-9]+\\.[0-9]+(\\.[0-9]+)?'",
        }

        cmd = version_cmds.get(pkg_id)
        if not cmd:
            return None

        try:
            shell = self.platform_key != "win32"
            result = subprocess.run(
                cmd, shell=shell, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                ver = result.stdout.strip()
                return ver if ver else None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None

    # ── Sudo handling ──

    def check_sudo(self) -> bool:
        """Check if sudo is available and passwordless."""
        if self.platform_key in ("win32", "termux"):
            return False
        try:
            result = subprocess.run(
                "sudo -n true", shell=True, capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def needs_sudo_for_packages(self, pkg_ids: list[str]) -> list[str]:
        """Return list of package names that need sudo."""
        if self.platform_key == "termux":
            return []
        needed = []
        for pkg_id in pkg_ids:
            pkg = self.get_package(pkg_id)
            if pkg is None:
                continue
            cmd = pkg.get("install", {}).get(self.platform_key, "")
            if cmd and self._cmd_needs_sudo(cmd):
                needed.append(pkg["name"])
        return needed

    def _cmd_needs_sudo(self, cmd: str) -> bool:
        """Check if a command string contains sudo."""
        parts = cmd.strip().split()
        for i, part in enumerate(parts):
            if part == "sudo":
                return True
            if part in ("||", "&&", "|", ";"):
                continue
        return False

    def set_sudo_password(self, password: str):
        self._sudo_password = password

    # ── Install ──

    def install(
        self,
        pkg_ids: list[str],
        callback: Optional[Callable[[int, str], None]] = None,
    ) -> bool:
        total = len(pkg_ids)
        success_count = 0
        failed_pkgs: list[str] = []

        for i, pkg_id in enumerate(pkg_ids):
            try:
                pkg = self.get_package(pkg_id)
                if pkg is None:
                    if callback:
                        callback(self._progress(i, total), f"[SKIP] Not found: {pkg_id}")
                    continue

                if self.is_installed(pkg_id):
                    success_count += 1
                    ver = self.get_installed_version(pkg_id)
                    ver_str = f" (v{ver})" if ver else ""
                    if callback:
                        callback(self._progress(i, total), f"[SKIP] Already installed: {pkg['name']}{ver_str}")
                    continue

                if callback:
                    callback(self._progress(i, total), f"[...] Installing: {pkg['name']}")

                install_cmds = pkg.get("install", {})
                cmd = install_cmds.get(self.platform_key)
                if not cmd:
                    if callback:
                        callback(self._progress(i, total), f"[SKIP] Not supported on {self.platform_key}: {pkg['name']}")
                    continue

                ok = self._run_cmd(cmd, callback, f"  {pkg['name']}")
                if not ok:
                    failed_pkgs.append(pkg['name'])
                    if callback:
                        callback(self._progress(i, total), f"[FAIL] Failed: {pkg['name']} - skipped, continuing...")
                    continue

                post = pkg.get("post_install", {})
                post_cmd = post.get(self.platform_key)
                if post_cmd:
                    post_ok = self._run_cmd(post_cmd, callback, f"  Post-install {pkg['name']}")
                    if not post_ok:
                        if callback:
                            callback(self._progress(i, total), f"[WARN] Post-install failed: {pkg['name']} (main install OK)")

                success_count += 1
                if callback:
                    callback(self._progress(i, total), f"[OK] Done: {pkg['name']}")

            except Exception as e:
                failed_pkgs.append(pkg_id)
                if callback:
                    callback(self._progress(i, total), f"[ERROR] Unexpected error on {pkg_id}: {e} - skipped, continuing...")

        if callback:
            if failed_pkgs:
                callback(100, f"Finished! Installed {success_count}/{total} packages. Failed: {', '.join(failed_pkgs)}")
            else:
                callback(100, f"Finished! All {success_count}/{total} packages installed successfully.")

        return success_count == total

    def _run_cmd(
        self,
        cmd: str,
        callback: Optional[Callable[[int, str], None]] = None,
        prefix: str = "",
        timeout: int = 900,
        heartbeat: int = 10,
    ) -> bool:
        shell = self.platform_key != "win32"
        process = None

        use_sudo_stdin = False
        if self.platform_key != "termux" and self._cmd_needs_sudo(cmd) and self._sudo_password:
            use_sudo_stdin = True

        try:
            popen_kwargs = dict(
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
            )
            if use_sudo_stdin:
                popen_kwargs["stdin"] = subprocess.PIPE

            process = subprocess.Popen(
                cmd,
                shell=shell,
                **popen_kwargs,
            )

            if use_sudo_stdin:
                try:
                    process.stdin.write((self._sudo_password + "\n").encode())
                    process.stdin.flush()
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass

            output_queue: queue.Queue = queue.Queue()

            def _reader():
                if process.stdout is None:
                    output_queue.put(("done", None))
                    return
                buf = b""
                try:
                    while True:
                        chunk = process.stdout.read(4096)
                        if not chunk:
                            break
                        buf += chunk
                        while b"\n" in buf or b"\r" in buf:
                            nl = buf.find(b"\n")
                            cr = buf.find(b"\r")
                            if nl == -1 and cr == -1:
                                break
                            candidates = [x for x in [nl, cr] if x != -1]
                            idx = min(candidates)
                            line = buf[:idx].decode("utf-8", errors="replace").rstrip()
                            buf = buf[idx + 1:]
                            if line:
                                output_queue.put(("line", line))
                finally:
                    if buf:
                        line = buf.decode("utf-8", errors="replace").rstrip()
                        if line:
                            output_queue.put(("line", line))
                    output_queue.put(("done", None))

            reader_thread = threading.Thread(target=_reader, daemon=True)
            reader_thread.start()

            elapsed = 0

            while True:
                try:
                    msg_type, data = output_queue.get(timeout=heartbeat)
                except queue.Empty:
                    elapsed += heartbeat
                    if elapsed >= timeout:
                        if callback:
                            callback(-1, f"{prefix} | TIMEOUT: no output for {timeout}s, killing...")
                        process.kill()
                        process.wait()
                        return False
                    if callback:
                        callback(-1, f"{prefix} | ... still running ({elapsed}s elapsed)")
                    continue

                if msg_type == "done":
                    break

                if msg_type == "line":
                    elapsed = 0
                    if callback:
                        callback(-1, f"{prefix} | {data}")

            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                if callback:
                    callback(-1, f"{prefix} | TIMEOUT: process did not exit after 30s, killed")
                return False
            return process.returncode == 0

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
                process.wait()
            if callback:
                callback(-1, f"{prefix} | TIMEOUT: process killed after {timeout}s")
            return False
        except Exception as e:
            if process and process.poll() is None:
                process.kill()
                process.wait()
            if callback:
                callback(-1, f"{prefix} | ERROR: {e}")
            return False

    # ── Package management ──

    def add_package(
        self,
        category_id: str,
        pkg_id: str,
        name: str,
        description: str,
        install_cmds: dict,
        check_cmds: dict,
        post_install_cmds: dict = None,
    ) -> bool:
        for cat in self.data.get("categories", []):
            if cat["id"] == category_id:
                for pkg in cat.get("packages", []):
                    if pkg["id"] == pkg_id:
                        return False
                new_pkg = {
                    "id": pkg_id,
                    "name": name,
                    "description": description,
                    "install": install_cmds,
                    "check": check_cmds,
                }
                if post_install_cmds:
                    new_pkg["post_install"] = post_install_cmds
                cat.setdefault("packages", []).append(new_pkg)
                self.save()
                return True
        return False

    def add_category(self, cat_id: str, name: str) -> bool:
        for cat in self.data.get("categories", []):
            if cat["id"] == cat_id:
                return False
        self.data.setdefault("categories", []).append({
            "id": cat_id,
            "name": name,
            "packages": [],
        })
        self.save()
        return True

    def remove_package(self, pkg_id: str) -> bool:
        for cat in self.data.get("categories", []):
            packages = cat.get("packages", [])
            for i, pkg in enumerate(packages):
                if pkg["id"] == pkg_id:
                    packages.pop(i)
                    self.save()
                    return True
        return False

    def remove_category(self, cat_id: str) -> bool:
        categories = self.data.get("categories", [])
        for i, cat in enumerate(categories):
            if cat["id"] == cat_id:
                categories.pop(i)
                self.save()
                return True
        return False

    def update_package(
        self,
        pkg_id: str,
        name: str = None,
        description: str = None,
        install_cmds: dict = None,
        check_cmds: dict = None,
        post_install_cmds: dict = None,
    ) -> bool:
        for cat in self.data.get("categories", []):
            for pkg in cat.get("packages", []):
                if pkg["id"] == pkg_id:
                    if name is not None:
                        pkg["name"] = name
                    if description is not None:
                        pkg["description"] = description
                    if install_cmds is not None:
                        pkg["install"] = install_cmds
                    if check_cmds is not None:
                        pkg["check"] = check_cmds
                    if post_install_cmds is not None:
                        pkg["post_install"] = post_install_cmds
                    self.save()
                    return True
        return False

    def _progress(self, current: int, total: int) -> int:
        if total == 0:
            return 100
        return int((current / total) * 100)
