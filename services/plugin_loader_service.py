# services\plugin_loader_service.py


"""
插件加载器模块

负责扫描和发现插件目录中的 manifest 文件。

职责范围：
    - 扫描插件目录
    - 发现所有 manifest.yml 文件
    - 验证目录结构
    - 提供插件路径列表

不负责：
    - YAML 文件解析
    - 插件加载和实例化
    - 插件依赖检查
    - 插件配置管理

依赖：
    - utils.paths: 路径处理
    - utils.log: 日志模块

Example:
    >>> loader = PluginLoader()
    >>> manifests = loader.discover()
    >>> 
    >>> # 自定义插件目录
    >>> loader = PluginLoader("/custom/plugins")
    >>> loader.has_plugins()
"""

import time
from pathlib import Path

from utils.log import get_logger
from utils.paths import get_plugin_dir

# 创建模块专用日志记录器
logger = get_logger(
    name="plugin_loader",
    log_dir="logs",
    fmt_type="detailed",
    console_level=20,  # INFO
    file_level=10,  # DEBUG
)


class PluginLoaderError(Exception):
    """插件加载器异常"""


class PluginLoader:
    """
    插件清单发现器

    负责扫描指定目录，发现所有有效的插件 manifest 文件。
    默认使用 utils.paths.get_plugin_dir() 获取插件目录，
    兼容开发环境和打包环境。

    Attributes:
        plugin_dir (Path): 插件目录路径
        MANIFEST_FILENAME (str): manifest 文件名

    Usage:
        # 使用默认插件目录
        >>> loader = PluginLoader()
        >>> manifests = loader.discover()

        # 指定插件目录
        >>> loader = PluginLoader("/path/to/plugins")
        >>> if loader.has_plugins():
        ...     print(loader.get_statistics())
    """

    MANIFEST_FILENAME = "manifest.yml"

    def __init__(self, plugin_dir: str | Path | None = None):
        """
        初始化插件加载器

        Args:
            plugin_dir: 插件目录路径，为 None 时自动从 utils.paths 获取

        Raises:
            PluginLoaderError: 目录不存在或无法访问
            TypeError: plugin_dir 类型不正确

        Example:
            >>> loader = PluginLoader()  # 使用默认目录
            >>> loader = PluginLoader("./my_plugins")  # 自定义目录
            >>> loader = PluginLoader(Path("/path/to/plugins"))
        """
        start_time = time.time()

        # 类型验证
        if plugin_dir is not None and not isinstance(plugin_dir, (str, Path)):
            raise TypeError(
                f"plugin_dir 必须是 str 或 Path 类型，实际为: {type(plugin_dir).__name__}"
            )

        # 设置插件目录
        if plugin_dir is None:
            self.plugin_dir = get_plugin_dir()
            logger.debug("使用默认插件目录")
        else:
            self.plugin_dir = Path(plugin_dir).resolve()

        elapsed_time = time.time() - start_time
        logger.info("PluginLoader 初始化完成")
        logger.debug(f"插件目录: {self.plugin_dir}")
        logger.debug(f"目录存在: {self.plugin_dir.exists()}")
        logger.debug(f"初始化耗时: {elapsed_time:.4f}s")

    def discover(self) -> list[Path]:
        """
        发现所有插件 manifest 文件

        扫描 plugin_dir 下的所有一级子目录，查找 manifest.yml 文件。

        Returns:
            list[Path]: manifest 文件路径列表，按路径排序

        Note:
            - 只扫描一级子目录（不递归）
            - 只返回存在的 manifest.yml 文件
            - 如果插件目录不存在，返回空列表

        Example:
            >>> loader = PluginLoader()
            >>> manifests = loader.discover()
            >>> for manifest in manifests:
            ...     print(f"发现插件: {manifest.parent.name}")
        """
        start_time = time.time()
        logger.info(f"开始扫描插件目录: {self.plugin_dir}")

        # 检查插件目录
        if not self.plugin_dir.exists():
            logger.warning(f"插件目录不存在: {self.plugin_dir}")
            return []

        if not self.plugin_dir.is_dir():
            logger.error(f"插件路径不是目录: {self.plugin_dir}")
            return []

        # 扫描 manifest 文件
        pattern = f"*/{self.MANIFEST_FILENAME}"
        logger.debug(f"扫描模式: {self.plugin_dir}/{pattern}")

        try:
            manifests = sorted(self.plugin_dir.glob(pattern))
        except (OSError, PermissionError, RuntimeError):
            logger.exception("扫描插件目录时发生错误")
            return []

        elapsed_time = time.time() - start_time

        # 记录结果
        if manifests:
            logger.info(f"发现 {len(manifests)} 个插件 (耗时: {elapsed_time:.4f}s)")
            for i, manifest in enumerate(manifests, 1):
                logger.debug(f"  [{i}] {manifest.parent.name} -> {manifest}")
        else:
            logger.warning(f"未发现插件 (*/{self.MANIFEST_FILENAME})")
            # 列出目录内容帮助调试
            try:
                contents = list(self.plugin_dir.iterdir())
                logger.debug(f"目录内容: {[p.name for p in contents]}")
            except (OSError, PermissionError) as e:
                logger.debug(f"无法列出目录内容: {e}")

        return manifests

    def has_plugins(self) -> bool:
        """
        检查是否有插件存在

        Returns:
            bool: 至少有一个插件返回 True

        Example:
            >>> loader = PluginLoader()
            >>> if loader.has_plugins():
            ...     print("发现插件")
        """
        return len(self.discover()) > 0

    def get_plugin_names(self) -> list[str]:
        """
        获取所有插件名称

        Returns:
            list[str]: 插件名称列表（目录名）

        Example:
            >>> loader = PluginLoader()
            >>> names = loader.get_plugin_names()
            >>> print(names)  # ['plugin1', 'plugin2']
        """
        return [m.parent.name for m in self.discover()]

    def get_plugin_paths(self) -> list[Path]:
        """
        获取所有插件目录路径

        Returns:
            list[Path]: 插件目录路径列表（不含 manifest 文件名）

        Example:
            >>> loader = PluginLoader()
            >>> for path in loader.get_plugin_paths():
            ...     print(f"插件路径: {path}")
        """
        return [m.parent for m in self.discover()]

    def get_statistics(self) -> dict:
        """
        获取插件目录统计信息

        Returns:
            dict: 统计信息
                - plugin_dir: 插件目录路径
                - dir_exists: 目录是否存在
                - total: 发现的插件总数
                - names: 插件名称列表

        Example:
            >>> loader = PluginLoader()
            >>> stats = loader.get_statistics()
            >>> print(f"发现 {stats['total']} 个插件")
        """
        manifests = self.discover()
        stats = {
            "plugin_dir": str(self.plugin_dir),
            "dir_exists": self.plugin_dir.exists(),
            "total": len(manifests),
            "names": [m.parent.name for m in manifests],
        }
        logger.debug(f"统计信息: {stats}")
        return stats

    def discover_with_details(self) -> list[dict]:
        """
        发现插件并返回详细信息

        Returns:
            list[dict]: 插件信息列表
                - path: manifest 文件路径
                - plugin_name: 插件名称
                - manifest_exists: manifest 是否存在
                - plugin_dir_exists: 插件目录是否存在
                - manifest_size: manifest 文件大小（字节）

        Example:
            >>> loader = PluginLoader()
            >>> details = loader.discover_with_details()
            >>> for d in details:
            ...     print(f"{d['plugin_name']}: {d['manifest_size']} bytes")
        """
        logger.info("开始详细扫描")
        manifests = self.discover()

        details = []
        for manifest in manifests:
            plugin_dir = manifest.parent
            detail = {
                "path": str(manifest),
                "plugin_name": plugin_dir.name,
                "manifest_exists": manifest.exists(),
                "plugin_dir_exists": plugin_dir.is_dir(),
                "manifest_size": manifest.stat().st_size if manifest.exists() else 0,
            }
            details.append(detail)

        logger.info(f"详细扫描完成，共 {len(details)} 个插件")
        return details

    def __repr__(self) -> str:
        return f"PluginLoader(plugin_dir='{self.plugin_dir}')"

    def __str__(self) -> str:
        stats = self.get_statistics()
        return (
            f"PluginLoader\n"
            f"  插件目录: {self.plugin_dir}\n"
            f"  目录存在: {stats['dir_exists']}\n"
            f"  发现插件: {stats['total']} 个"
        )


# ============================================================================
# 便捷函数
# ============================================================================

def discover_plugins(plugin_dir: str | Path | None = None) -> list[Path]:
    """
    便捷函数：快速发现插件

    Args:
        plugin_dir: 插件目录，为 None 使用默认目录

    Returns:
        list[Path]: manifest 文件路径列表

    Example:
        >>> manifests = discover_plugins()
        >>> print(f"发现 {len(manifests)} 个插件")
    """
    loader = PluginLoader(plugin_dir)
    return loader.discover()


def get_plugin_statistics(plugin_dir: str | Path | None = None) -> dict:
    """
    便捷函数：快速获取插件统计信息

    Args:
        plugin_dir: 插件目录，为 None 使用默认目录

    Returns:
        dict: 统计信息

    Example:
        >>> stats = get_plugin_statistics()
        >>> print(f"发现 {stats['total']} 个插件: {stats['names']}")
    """
    loader = PluginLoader(plugin_dir)
    return loader.get_statistics()