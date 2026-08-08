# utils\paths.py


"""
路径处理模块

提供跨环境的路径解析功能，兼容开发环境和打包环境（PyInstaller）。

功能：
    - 获取应用根目录
    - 获取各类资源目录（插件、日志、配置、数据）
    - 支持环境变量覆盖

环境适配：
    - 开发环境：基于当前工作目录或 __file__
    - 打包环境：基于 sys.executable 所在目录
    - 环境变量：CMD_TOOLS_HOME 可强制指定

使用方式：
    >>> from utils.paths import get_app_root, get_plugin_dir, get_config_dir
    >>>
    >>> root = get_app_root()
    >>> plugin_dir = get_plugin_dir()

环境变量：
    CMD_TOOLS_HOME          应用根目录
    CMD_TOOLS_PLUGIN_DIR    插件目录
    CMD_TOOLS_CONFIG_DIR    配置目录
    CMD_TOOLS_LOG_DIR       日志目录
    CMD_TOOLS_DATA_DIR      数据目录
"""

import os
import sys
from pathlib import Path

from log import get_logger

logger = get_logger(
    name="paths",
    log_dir="logs",
    fmt_type="detailed",
    console_level=20,
    file_level=10,
)


# ============================================================================
# 核心方法
# ============================================================================


def get_app_root() -> Path:
    """
    获取应用根目录

    优先级：
        1. 环境变量 CMD_TOOLS_HOME
        2. PyInstaller 打包路径（sys.executable 所在目录）
        3. 当前工作目录

    Returns:
        Path: 应用根目录

    Example:
        >>> root = get_app_root()
        >>> print(root)  # /path/to/cmd_tools
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
    path = Path.cwd().resolve()
    logger.debug(f"应用根目录（开发环境）: {path}")
    return path


def is_frozen() -> bool:
    """
    判断是否为打包环境

    Returns:
        bool: True 表示打包环境（PyInstaller/py2exe/cx_Freeze）
    """
    return getattr(sys, "frozen", False)


# ============================================================================
# 标准目录
# ============================================================================


def get_plugin_dir() -> Path:
    """
    获取插件目录

    优先级：
        1. 环境变量 CMD_TOOLS_PLUGIN_DIR
        2. {app_root}/plugin

    Returns:
        Path: 插件目录

    Example:
        >>> plugin_dir = get_plugin_dir()
        >>> print(plugin_dir)  # /path/to/cmd_tools/plugin
    """
    env_dir = os.getenv("CMD_TOOLS_PLUGIN_DIR")
    if env_dir:
        path = Path(env_dir).resolve()
        logger.debug(f"插件目录（环境变量）: {path}")
        return path

    path = get_app_root() / "plugin"
    logger.debug(f"插件目录（默认）: {path}")
    return path


def get_config_dir() -> Path:
    """
    获取配置目录

    优先级：
        1. 环境变量 CMD_TOOLS_CONFIG_DIR
        2. {app_root}/config

    Returns:
        Path: 配置目录

    Example:
        >>> config_dir = get_config_dir()
        >>> print(config_dir)  # /path/to/cmd_tools/config
    """
    env_dir = os.getenv("CMD_TOOLS_CONFIG_DIR")
    if env_dir:
        path = Path(env_dir).resolve()
        logger.debug(f"配置目录（环境变量）: {path}")
        return path

    path = get_app_root() / "config"
    logger.debug(f"配置目录（默认）: {path}")
    return path


def get_log_dir() -> Path:
    """
    获取日志目录

    优先级：
        1. 环境变量 CMD_TOOLS_LOG_DIR
        2. {app_root}/logs

    Returns:
        Path: 日志目录

    Example:
        >>> log_dir = get_log_dir()
        >>> print(log_dir)  # /path/to/cmd_tools/logs
    """
    env_dir = os.getenv("CMD_TOOLS_LOG_DIR")
    if env_dir:
        path = Path(env_dir).resolve()
        logger.debug(f"日志目录（环境变量）: {path}")
        return path

    path = get_app_root() / "logs"
    logger.debug(f"日志目录（默认）: {path}")
    return path


def get_data_dir() -> Path:
    """
    获取数据目录

    优先级：
        1. 环境变量 CMD_TOOLS_DATA_DIR
        2. {app_root}/data

    Returns:
        Path: 数据目录

    Example:
        >>> data_dir = get_data_dir()
        >>> print(data_dir)  # /path/to/cmd_tools/data
    """
    env_dir = os.getenv("CMD_TOOLS_DATA_DIR")
    if env_dir:
        path = Path(env_dir).resolve()
        logger.debug(f"数据目录（环境变量）: {path}")
        return path

    path = get_app_root() / "data"
    logger.debug(f"数据目录（默认）: {path}")
    return path


# ============================================================================
# 用户级目录
# ============================================================================


def get_user_dir() -> Path:
    """
    获取用户级目录（跨环境持久化）

    Returns:
        Path: ~/.cmd_tools

    Example:
        >>> user_dir = get_user_dir()
        >>> print(user_dir)  # /home/user/.cmd_tools
    """
    path = Path.home() / ".cmd_tools"
    logger.debug(f"用户目录: {path}")
    return path


def get_user_config_dir() -> Path:
    """
    获取用户级配置目录

    Returns:
        Path: ~/.cmd_tools/config

    Example:
        >>> user_config_dir = get_user_config_dir()
        >>> print(user_config_dir)  # /home/user/.cmd_tools/config
    """
    path = get_user_dir() / "config"
    logger.debug(f"用户配置目录: {path}")
    return path


def get_user_data_dir() -> Path:
    """
    获取用户级数据目录

    Returns:
        Path: ~/.cmd_tools/data

    Example:
        >>> user_data_dir = get_user_data_dir()
        >>> print(user_data_dir)  # /home/user/.cmd_tools/data
    """
    path = get_user_dir() / "data"
    logger.debug(f"用户数据目录: {path}")
    return path


# ============================================================================
# 目录管理
# ============================================================================


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path: 目录路径

    Example:
        >>> config_dir = ensure_dir(get_config_dir())
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建目录: {path}")
    return path


def ensure_all_dirs() -> dict[str, Path]:
    """
    确保所有标准目录存在

    Returns:
        dict: 目录字典 {名称: 路径}

    Example:
        >>> dirs = ensure_all_dirs()
        >>> for name, path in dirs.items():
        ...     print(f"{name}: {path}")
    """
    dirs = {
        "app_root": get_app_root(),
        "plugin": get_plugin_dir(),
        "config": get_config_dir(),
        "log": get_log_dir(),
        "data": get_data_dir(),
        "user": get_user_dir(),
        "user_config": get_user_config_dir(),
        "user_data": get_user_data_dir(),
    }

    for path in dirs.values():
        ensure_dir(path)

    logger.info("所有标准目录已就绪")
    return dirs


# ============================================================================
# 信息
# ============================================================================


def get_path_info() -> dict:
    """
    获取路径信息（用于调试）

    Returns:
        dict: 路径信息
    """
    return {
        "is_frozen": is_frozen(),
        "app_root": str(get_app_root()),
        "plugin_dir": str(get_plugin_dir()),
        "config_dir": str(get_config_dir()),
        "log_dir": str(get_log_dir()),
        "data_dir": str(get_data_dir()),
        "user_dir": str(get_user_dir()),
        "current_working_dir": str(Path.cwd()),
        "executable": sys.executable,
    }
