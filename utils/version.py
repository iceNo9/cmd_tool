# utils/version.py
"""应用版本号。

此文件在开发环境下手动维护，CI 构建时会被自动覆盖为 tag 版本。
"""

__version__ = "0.0.0-dev"


def get_app_version() -> str:
    """获取应用版本号。"""
    return __version__


def get_app_version_display() -> str:
    """获取带 v 前缀的版本号，用于 UI 显示。"""
    return f"v{__version__}"
