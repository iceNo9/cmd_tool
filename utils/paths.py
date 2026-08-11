"""
路径处理模块

提供跨环境的路径解析功能，兼容开发环境和打包环境（PyInstaller）。

功能：
    - 获取应用根目录
    - 获取各类资源目录（插件、日志、配置、数据）
    - 支持环境变量覆盖
    - 自动创建目录
    - 路径缓存机制

环境适配：
    - 开发环境：基于当前工作目录或 __file__
    - 打包环境：基于 sys.executable 所在目录
    - 环境变量：CMD_TOOLS_HOME 可强制指定

使用方式：
    >>> from utils.paths import paths
    >>>
    >>> root = paths.app_root
    >>> plugin_dir = paths.plugin_dir

环境变量：
    CMD_TOOLS_HOME          应用根目录
    CMD_TOOLS_PLUGIN_DIR    插件目录
    CMD_TOOLS_CONFIG_DIR    配置目录
    CMD_TOOLS_LOG_DIR       日志目录
    CMD_TOOLS_DATA_DIR      数据目录
"""

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

from utils.log import get_logger

logger = get_logger(
    name="paths",
    log_dir=None,
    fmt_type="detailed",
    console_level=10,
    file_level=10,
)


# ============================================================================
# 核心方法（带缓存）
# ============================================================================


@lru_cache(maxsize=1)
def _get_app_root() -> Path:
    """
    获取应用根目录（内部方法，带缓存）。

    优先级：
        1. 环境变量 CMD_TOOLS_HOME
        2. PyInstaller 打包路径（sys.executable 所在目录）
        3. 开发环境源码路径（utils/paths.py 的上级目录）

    Returns:
        Path: 应用根目录
    """
    # 1. 环境变量
    env_home = os.getenv("CMD_TOOLS_HOME")
    if env_home:
        path = Path(env_home).resolve()
        logger.debug(f"应用根目录（环境变量）: {path}")
        return path

    # 2. 打包环境
    if getattr(sys, "frozen", False):
        path = Path(sys.executable).parent.resolve()
        logger.debug(f"应用根目录（打包环境）: {path}")
        return path

    # 3. 开发环境
    # 注意：不使用 Path.cwd()，因为 Flet run 可能改变工作目录
    path = Path(__file__).resolve().parent.parent
    logger.debug(f"应用根目录（开发环境）: {path}")
    return path


@lru_cache(maxsize=1)
def _get_env_path(env_var: str, default_name: str) -> Path:
    """
    获取路径（内部方法，带缓存）

    Args:
        env_var: 环境变量名
        default_name: 默认目录名（相对于 app_root）

    Returns:
        Path: 目录路径
    """
    env_value = os.getenv(env_var)
    if env_value:
        path = Path(env_value).resolve()
        logger.debug(f"{default_name}目录（环境变量 {env_var}）: {path}")
        return path

    path = _get_app_root() / default_name
    logger.debug(f"{default_name}目录（默认）: {path}")
    return path


def is_frozen() -> bool:
    """判断是否为打包环境"""
    return getattr(sys, "frozen", False)


# ============================================================================
# 路径管理类
# ============================================================================


class PathManager:
    """
    路径管理器

    统一管理所有路径，支持缓存和自动创建目录。

    Example:
        >>> paths = PathManager()
        >>> print(paths.app_root)
        >>> print(paths.log_dir)
        >>> paths.ensure_all()  # 创建所有目录
    """

    def __init__(self):
        self._app_root: Optional[Path] = None
        self._dirs: dict[str, Path] = {}

    @property
    def app_root(self) -> Path:
        """应用根目录"""
        if self._app_root is None:
            self._app_root = _get_app_root()
        return self._app_root

    @property
    def plugin_dir(self) -> Path:
        """插件目录"""
        return self._get_dir("CMD_TOOLS_PLUGIN_DIR", "plugin")

    @property
    def config_dir(self) -> Path:
        """配置目录"""
        return self._get_dir("CMD_TOOLS_CONFIG_DIR", "config")

    @property
    def log_dir(self) -> Path:
        """日志目录"""
        return self._get_dir("CMD_TOOLS_LOG_DIR", "logs")
        # return self.user_dir / "logs"

    @property
    def data_dir(self) -> Path:
        """数据目录"""
        return self._get_dir("CMD_TOOLS_DATA_DIR", "data")

    @property
    def user_dir(self) -> Path:
        """用户级目录"""
        return Path.home() / ".cmd_tools"

    @property
    def user_config_dir(self) -> Path:
        """用户级配置目录"""
        return self.user_dir / "config"

    @property
    def user_data_dir(self) -> Path:
        """用户级数据目录"""
        return self.user_dir / "data"

    @property
    def cache_dir(self) -> Path:
        """缓存目录"""
        return self.data_dir / "cache"

    @property
    def temp_dir(self) -> Path:
        """临时目录"""
        return self.data_dir / "temp"

    def _get_dir(self, env_var: str, default_name: str) -> Path:
        """
        获取目录（内部方法，带缓存）

        Args:
            env_var: 环境变量名
            default_name: 默认目录名

        Returns:
            Path: 目录路径
        """
        cache_key = f"{env_var}:{default_name}"
        if cache_key in self._dirs:
            return self._dirs[cache_key]

        path = _get_env_path(env_var, default_name)
        self._dirs[cache_key] = path
        return path

    def ensure(self, *paths: Path) -> None:
        """
        确保目录存在

        Args:
            *paths: 要创建的目录路径
        """
        for path in paths:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目录: {path}")

    def ensure_all(self) -> dict[str, Path]:
        """
        确保所有标准目录存在

        Returns:
            dict[str, Path]: 所有路径字典
        """
        all_dirs = {
            "app_root": self.app_root,
            "plugin": self.plugin_dir,
            "config": self.config_dir,
            "log": self.log_dir,
            "data": self.data_dir,
            "user": self.user_dir,
            "user_config": self.user_config_dir,
            "user_data": self.user_data_dir,
            "cache": self.cache_dir,
            "temp": self.temp_dir,
        }

        for name, path in all_dirs.items():
            if name not in ("app_root", "plugin"):  # plugin 可能不需要自动创建
                self.ensure(path)

        logger.info("所有标准目录已就绪")
        return all_dirs

    def get_info(self) -> dict[str, str]:
        """
        获取路径信息（用于调试）

        Returns:
            dict[str, str]: 路径信息
        """
        return {
            "is_frozen": str(is_frozen()),
            "app_root": str(self.app_root),
            "plugin_dir": str(self.plugin_dir),
            "config_dir": str(self.config_dir),
            "log_dir": str(self.log_dir),
            "data_dir": str(self.data_dir),
            "user_dir": str(self.user_dir),
            "current_working_dir": str(Path.cwd()),
            "executable": sys.executable,
        }

    def clear_cache(self) -> None:
        """清除路径缓存"""
        self._app_root = None
        self._dirs.clear()
        logger.debug("路径缓存已清除")


# ============================================================================
# 便捷函数（兼容旧接口）
# ============================================================================

# 单例模式
_paths = PathManager()


def get_app_root() -> Path:
    """获取应用根目录"""
    return _paths.app_root


def get_plugin_dir() -> Path:
    """获取插件目录"""
    return _paths.plugin_dir


def get_config_dir() -> Path:
    """获取配置目录"""
    return _paths.config_dir


def get_log_dir() -> Path:
    """获取日志目录"""
    return _paths.log_dir


def get_data_dir() -> Path:
    """获取数据目录"""
    return _paths.data_dir


def get_user_dir() -> Path:
    """获取用户级目录"""
    return _paths.user_dir


def get_user_config_dir() -> Path:
    """获取用户级配置目录"""
    return _paths.user_config_dir


def get_user_data_dir() -> Path:
    """获取用户级数据目录"""
    return _paths.user_data_dir


def get_cache_dir() -> Path:
    """获取缓存目录"""
    return _paths.cache_dir


def get_temp_dir() -> Path:
    """获取临时目录"""
    return _paths.temp_dir


def ensure_dir(path: Path) -> Path:
    """确保目录存在"""
    _paths.ensure(path)
    return path


def ensure_all_dirs() -> dict[str, Path]:
    """确保所有标准目录存在"""
    return _paths.ensure_all()


def get_path_info() -> dict[str, str]:
    """获取路径信息（用于调试）"""
    return _paths.get_info()


def clear_cache() -> None:
    """清除路径缓存"""
    _paths.clear_cache()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 类
    "PathManager",
    # 实例
    "paths",
    # 函数
    "get_app_root",
    "get_plugin_dir",
    "get_config_dir",
    "get_log_dir",
    "get_data_dir",
    "get_user_dir",
    "get_user_config_dir",
    "get_user_data_dir",
    "get_cache_dir",
    "get_temp_dir",
    "ensure_dir",
    "ensure_all_dirs",
    "get_path_info",
    "clear_cache",
    "is_frozen",
]

# 推荐使用方式：直接导入 paths 实例
paths = _paths
