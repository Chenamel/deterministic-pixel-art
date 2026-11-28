"""Install the Deterministic Pixel Art Skill from its pinned v1.4.1 release or a verified local ZIP.

从固定版本 v1.4.1 的官方 GitHub Release 或已验证的本地 ZIP 压缩包安装完整 Skill。
"""

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen
import zipfile


ARCHIVE_URL = (
    "https://github.com/Chenamel/deterministic-pixel-art/releases/download/"
    "v1.4.1/deterministic-pixel-art-v1.4.1.zip"
)
ARCHIVE_SHA256 = "d6a77c0696134b1419470ff36bef5adb24cdb8cf9233323f0b1e24a2c5ba2671"
ARCHIVE_ROOT = "deterministic-pixel-art/"
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_UNPACKED_BYTES = 16 * 1024 * 1024
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.5
RETRYABLE_HTTP_STATUS = {408, 425, 429, 500, 502, 503, 504}


def _verify_archive_bytes(data):
    """Enforce bounded size and exact pinned SHA-256 digest on release bytes."""
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ValueError(
            "Release archive exceeds the download size limit. / 发行包大小超出 16 MiB 安全上限。"
        )
    digest = hashlib.sha256(data).hexdigest()
    if digest != ARCHIVE_SHA256:
        raise ValueError(
            f"Release archive SHA-256 mismatch: {digest} (expected {ARCHIVE_SHA256}) / "
            "发行包 SHA-256 校验失败，请重新下载官方 v1.4.1 压缩包。"
        )
    return data


def _validate_https_url(url):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.netloc:
        raise ValueError(
            f"Download URL must be a valid https:// URL: {url} / "
            "自定义下载地址仅支持合法的 https:// 链接。"
        )


def _is_retryable_network_error(error):
    if isinstance(error, HTTPError):
        return error.code in RETRYABLE_HTTP_STATUS
    return isinstance(error, (URLError, TimeoutError, OSError))


def download_archive(url=ARCHIVE_URL, retries=DEFAULT_RETRIES, timeout=DEFAULT_TIMEOUT, retry_delay=DEFAULT_RETRY_DELAY):
    """Download the pinned release archive with bounded retries and exact SHA-256 verification."""
    if retries < 0:
        raise ValueError("retries must be non-negative. / 重试次数不能为负数。")
    if timeout <= 0:
        raise ValueError("timeout must be positive. / 超时时间必须大于 0。")
    _validate_https_url(url)

    last_error = None
    for attempt in range(retries + 1):
        try:
            with urlopen(url, timeout=timeout) as response:
                data = response.read(MAX_ARCHIVE_BYTES + 1)
            return _verify_archive_bytes(data)
        except ValueError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = error
            if attempt >= retries or not _is_retryable_network_error(error):
                break
            if retry_delay > 0:
                time.sleep(retry_delay * (attempt + 1))

    raise OSError(
        f"Failed to download {url} after {retries + 1} attempt(s): {last_error} | "
        "下载失败：若国内访问 GitHub 受限，可先通过浏览器手动下载 deterministic-pixel-art-v1.4.1.zip，"
        "再执行 python install.py --archive ./deterministic-pixel-art-v1.4.1.zip --destination <目录> 离线校验安装。"
    ) from last_error


def load_local_archive(archive_path):
    """Read a locally downloaded release ZIP and verify size + pinned SHA-256 before extraction."""
    path = Path(archive_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"Local archive not found: {path} / 未找到本地压缩包，请确认 --archive 路径是否正确。"
        )
    with path.open("rb") as handle:
        data = handle.read(MAX_ARCHIVE_BYTES + 1)
    return _verify_archive_bytes(data)


def install(destination, archive_path=None, url=ARCHIVE_URL, retries=DEFAULT_RETRIES, timeout=DEFAULT_TIMEOUT):
    """Verify and extract the complete Skill archive into a new destination directory."""
    if archive_path is not None and url != ARCHIVE_URL:
        raise ValueError(
            "Pass either --archive or --url, not both. / --archive 与 --url 不能同时指定。"
        )
    destination = Path(destination).expanduser().resolve()
    if destination.exists():
        raise FileExistsError(
            f"Destination already exists: {destination} / "
            "目标目录已存在；为避免覆盖原有文件，请改用新目录名或先自行备份移除。"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)

    data = (
        load_local_archive(archive_path)
        if archive_path is not None
        else download_archive(url=url, retries=retries, timeout=timeout)
    )
    with tempfile.TemporaryDirectory(prefix="deterministic-pixel-art-") as temporary:
        archive_file = Path(temporary) / "release.zip"
        extract_root = Path(temporary) / "extract"
        extract_root.mkdir()
        archive_file.write_bytes(data)
        with zipfile.ZipFile(archive_file) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if not names or len(names) > 2048 or len(names) != len(set(names)):
                raise ValueError(
                    "Release archive has no files or contains duplicate paths. / 压缩包为空或存在重复路径。"
                )
            total_size = 0
            for entry in entries:
                normalized = entry.filename.replace("\\", "/")
                path = PurePosixPath(normalized)
                mode = entry.external_attr >> 16
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or not normalized.startswith(ARCHIVE_ROOT)
                    or stat.S_ISLNK(mode)
                ):
                    raise ValueError(
                        f"Unexpected archive path: {entry.filename} / 压缩包包含非法路径或符号链接。"
                    )
                total_size += entry.file_size
                if total_size > MAX_UNPACKED_BYTES:
                    raise ValueError(
                        "Release archive exceeds the extraction size limit. / 解压体积超出 16 MiB 安全上限。"
                    )
            archive.extractall(extract_root)

        source = extract_root / ARCHIVE_ROOT.rstrip("/")
        required = (source / "SKILL.md", source / "LICENSE", source / "requirements.txt")
        if not all(path.is_file() for path in required):
            raise ValueError(
                "Release archive is missing required Skill files. / 压缩包缺少 SKILL.md、LICENSE 或 requirements.txt。"
            )
        if destination.exists():
            raise FileExistsError(
                f"Destination already exists: {destination} / 目标目录已存在。"
            )
        shutil.move(str(source), str(destination))
    return destination


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Install Deterministic Pixel Art v1.4.1 with pinned SHA-256 verification. / "
            "校验安装 Deterministic Pixel Art v1.4.1（支持自动重试与本地 ZIP 离线安装）。"
        )
    )
    parser.add_argument(
        "--destination",
        required=True,
        type=Path,
        help="New target folder to extract into (must not already exist). / 目标安装目录（必须尚不存在）。",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=None,
        help="Optional local deterministic-pixel-art-v1.4.1.zip for offline install (still verifies SHA-256). / 可选本地官方 ZIP，离线安装并同样校验 SHA-256。",
    )
    parser.add_argument(
        "--url",
        default=ARCHIVE_URL,
        help="Optional custom https:// release ZIP URL (still enforces pinned SHA-256). / 可选自定义 https:// 下载链接（仍强制核对官方 SHA-256）。",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"Network retry count on transient errors (default: {DEFAULT_RETRIES}). / 网络波动自动重试次数（默认 {DEFAULT_RETRIES}）。",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Per-attempt HTTP timeout in seconds (default: {DEFAULT_TIMEOUT}). / 单次请求超时秒数（默认 {DEFAULT_TIMEOUT}）。",
    )
    args = parser.parse_args()
    try:
        installed = install(
            args.destination,
            archive_path=args.archive,
            url=args.url,
            retries=args.retries,
            timeout=args.timeout,
        )
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(2, f"Installation failed / 安装失败: {error}\n")
    print(f"Installed Deterministic Pixel Art v1.4.1 to / 已成功安装至: {installed}")
    print(f"Next / 下一步: python -m pip install -r \"{installed / 'requirements.txt'}\"")
    print(f"Guide / 使用说明: \"{installed / 'SKILL.md'}\"")


if __name__ == "__main__":
    main()
