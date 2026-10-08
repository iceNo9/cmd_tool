# services\plugin_import_export_service.py
"""
插件导入导出服务

负责插件的导入、导出和删除操作。

当前插件形态约定：
    插件 = 单个 manifest.yml 文件
    插件逻辑（runtime.entry / command.executable 等）
    由执行环境提供，与插件包本身无关。
    因此导入时只复制 manifest.yml，不复制任何附加文件。

导入流程：
    1. 解析 manifest.yml 验证有效性
    2. 读取 metadata.id 作为插件目录名
    3. 检查插件版本
    4. 新插件直接安装，高版本覆盖低版本
    5. 只复制 manifest.yml 到插件目录
    6. 重新加载插件列表

导出流程：
    1. 根据插件 ID 定位插件目录
    2. 复制整个目录到目标位置

删除流程：
    1. 根据插件 ID 定位插件目录
    2. 校验目录与 manifest 一致
    3. 移入备份目录后删除

依赖：
    - services.manifest_parser_service: 解析和验证 manifest
    - services.plugin_loader_service: 插件发现
    - utils.log: 日志模块
    - utils.paths: 路径管理

Example:
    >>> service = PluginImportExportService()
    >>> result = service.import_plugin("path/to/manifest.yml")
    >>> if result.success:
    ...     manifests = service.reload_manifests()
"""

import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from services.manifest_parser_service import (
    ManifestParseError,
    ManifestParser,
)
from services.plugin_loader_service import PluginLoader
from utils.log import get_logger
from utils.paths import get_log_dir, get_plugin_dir

# 创建该模块专用的日志记录器
logger = get_logger(
    name="plugin_import_export",
    log_dir=get_log_dir() / "logs",
    fmt_type="detailed",
    console_level=20,  # INFO
    file_level=10,  # DEBUG
)


@dataclass
class ImportResult:
    """单个插件导入结果"""

    success: bool
    message: str
    plugin_id: str = ""
    plugin_name: str = ""
    target_path: Path | None = None


@dataclass
class ExportResult:
    """插件导出结果"""

    success: bool
    message: str
    plugin_id: str = ""
    export_path: Path | None = None


@dataclass
class DeleteResult:
    """插件删除结果"""

    success: bool
    message: str
    plugin_id: str = ""
    plugin_name: str = ""


@dataclass
class BatchImportResult:
    """批量导入结果"""

    results: list[ImportResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len([r for r in self.results if r.success])

    @property
    def failed_count(self) -> int:
        return len([r for r in self.results if not r.success])

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def has_failures(self) -> bool:
        return self.failed_count > 0


class PluginImportExportService:
    """
    插件导入导出服务

    负责插件的导入、导出和删除操作，遵循以下约定：
    - 插件形态 = 单个 manifest.yml 文件
    - 插件目录名 = manifest.metadata.id
    - 插件目录下包含 manifest.yml
    - 导入时先验证 manifest 有效性
    - 已存在插件时，仅允许更高版本覆盖
    - 删除时校验目录名与 manifest ID 一致

    Usage:
        service = PluginImportExportService()

        # 导入单个插件
        result = service.import_plugin("path/to/manifest.yml")

        # 批量导入
        batch_result = service.import_plugins([
            "path1/manifest.yml",
            "path2/manifest.yml",
        ])

        # 导出插件
        result = service.export_plugin(
            "plugin_id",
            "/export/directory",
        )

        # 删除插件
        result = service.delete_plugin("plugin_id")

        # 重新加载插件列表
        manifests = service.reload_manifests()
    """

    def __init__(
        self,
        plugin_dir: str | Path | None = None,
    ):
        """
        初始化服务

        Args:
            plugin_dir: 插件目录，None 使用默认目录
        """
        self.plugin_dir = Path(plugin_dir) if plugin_dir else get_plugin_dir()

        self.parser = ManifestParser()
        self.loader = PluginLoader(self.plugin_dir)

        logger.info("PluginImportExportService 初始化完成")
        logger.debug(f"插件目录: {self.plugin_dir}")

    # ====================================================================
    # 导入功能
    # ====================================================================

    def import_plugin(
        self,
        manifest_path: str | Path,
    ) -> ImportResult:
        """
        导入单个插件。

        流程：
        1. 验证并解析 manifest.yml
        2. 使用 metadata.id 定位插件目录
        3. 如果不存在则直接安装
        4. 如果存在则比较版本
        5. 只有更高版本可以覆盖
        6. 使用临时目录完成导入
        7. 替换旧插件

        插件形态为单个 manifest.yml，
        因此只复制该文件，不复制同目录其他文件。

        Args:
            manifest_path: manifest.yml 文件路径

        Returns:
            ImportResult: 导入结果
        """
        manifest_path = Path(manifest_path)

        logger.info(f"开始导入插件: {manifest_path}")

        # ------------------------------------------------------------
        # 1. 验证文件存在
        # ------------------------------------------------------------

        if not manifest_path.exists():
            error_msg = f"文件不存在: {manifest_path}"
            logger.error(error_msg)

            return ImportResult(
                success=False,
                message=error_msg,
            )

        if not manifest_path.is_file():
            error_msg = f"路径不是文件: {manifest_path}"
            logger.error(error_msg)

            return ImportResult(
                success=False,
                message=error_msg,
            )

        if manifest_path.name != "manifest.yml":
            error_msg = f"文件名必须是 manifest.yml: " f"{manifest_path.name}"

            logger.error(error_msg)

            return ImportResult(
                success=False,
                message=error_msg,
            )

        # ------------------------------------------------------------
        # 2. 解析并验证 manifest
        # ------------------------------------------------------------

        try:
            manifest = self.parser.parse(manifest_path)

            plugin_id = manifest.metadata.id
            plugin_name = manifest.metadata.name
            import_version = manifest.metadata.version

            logger.debug(
                f"Manifest 验证通过 - "
                f"ID: {plugin_id}, "
                f"名称: {plugin_name}, "
                f"版本: {import_version}"
            )

        except ManifestParseError as e:
            error_msg = f"Manifest 无效: {e}"
            logger.error(error_msg)

            return ImportResult(
                success=False,
                message=error_msg,
            )

        except (
            OSError,
            ValueError,
            yaml.YAMLError,
        ) as e:
            error_msg = f"解析失败: {e}"
            logger.error(error_msg)

            return ImportResult(
                success=False,
                message=error_msg,
            )

        # ------------------------------------------------------------
        # 3. 确定插件目标目录
        # ------------------------------------------------------------

        target_dir = self.plugin_dir / plugin_id

        # ------------------------------------------------------------
        # 4. 检查已安装版本
        # ------------------------------------------------------------

        if target_dir.exists():
            if not target_dir.is_dir():
                error_msg = f"插件目标路径不是目录: " f"{target_dir}"

                logger.error(error_msg)

                return ImportResult(
                    success=False,
                    message=error_msg,
                    plugin_id=plugin_id,
                    plugin_name=plugin_name,
                )

            installed_manifest_path = target_dir / "manifest.yml"

            if not installed_manifest_path.exists():
                error_msg = f"已存在插件目录，但缺少 " f"manifest.yml: {target_dir}"

                logger.error(error_msg)

                return ImportResult(
                    success=False,
                    message=error_msg,
                    plugin_id=plugin_id,
                    plugin_name=plugin_name,
                )

            try:
                installed_manifest = self.parser.parse(installed_manifest_path)

                installed_id = installed_manifest.metadata.id

                installed_version = installed_manifest.metadata.version

                # 防止插件目录与 manifest ID 不一致
                if installed_id != plugin_id:
                    error_msg = (
                        f"插件目录与 Manifest ID 不一致: "
                        f"目录={plugin_id}, "
                        f"Manifest ID={installed_id}"
                    )

                    logger.error(error_msg)

                    return ImportResult(
                        success=False,
                        message=error_msg,
                        plugin_id=plugin_id,
                        plugin_name=plugin_name,
                    )

                logger.info(
                    f"发现已安装插件 - "
                    f"ID: {plugin_id}, "
                    f"当前版本: {installed_version}, "
                    f"导入版本: {import_version}"
                )

            except ManifestParseError as e:
                error_msg = f"现有插件 Manifest 无效: {e}"

                logger.error(error_msg)

                return ImportResult(
                    success=False,
                    message=error_msg,
                    plugin_id=plugin_id,
                    plugin_name=plugin_name,
                )

            # --------------------------------------------------------
            # 5. 比较版本
            # --------------------------------------------------------

            version_compare = self._compare_versions(
                import_version,
                installed_version,
            )

            if version_compare < 0:
                error_msg = (
                    f"插件版本过低，拒绝导入: "
                    f"{plugin_id} "
                    f"(当前 {installed_version}, "
                    f"导入 {import_version})"
                )

                logger.warning(error_msg)

                return ImportResult(
                    success=False,
                    message=error_msg,
                    plugin_id=plugin_id,
                    plugin_name=plugin_name,
                    target_path=target_dir,
                )

            if version_compare == 0:
                error_msg = (
                    f"插件版本已存在，拒绝重复导入: "
                    f"{plugin_id} "
                    f"(版本 {installed_version})"
                )

                logger.warning(error_msg)

                return ImportResult(
                    success=False,
                    message=error_msg,
                    plugin_id=plugin_id,
                    plugin_name=plugin_name,
                    target_path=target_dir,
                )

            logger.info(
                f"插件将进行升级: "
                f"{plugin_id} "
                f"{installed_version} -> "
                f"{import_version}"
            )

        else:
            installed_version = None

            logger.info(
                f"插件不存在，将进行首次安装: "
                f"{plugin_id} "
                f"(版本 {import_version})"
            )

        # ------------------------------------------------------------
        # 6. 执行导入
        # ------------------------------------------------------------

        try:
            self.plugin_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            # 使用插件目录的父目录作为临时目录位置，
            # 避免临时目录被 PluginLoader 发现。
            temp_dir = self.plugin_dir.parent / (
                f".{plugin_id}.import-" f"{time.time_ns()}"
            )

            logger.debug(f"创建临时导入目录: {temp_dir}")

            try:
                temp_dir.mkdir(
                    parents=False,
                    exist_ok=False,
                )

                # ----------------------------------------------------
                # 复制 manifest.yml
                #
                # 插件形态为单个 manifest.yml，
                # 不复制 manifest 同目录下的其他文件，
                # 避免把用户桌面等目录中的无关文件带进插件目录。
                # ----------------------------------------------------

                target_manifest = temp_dir / "manifest.yml"

                shutil.copy2(
                    manifest_path,
                    target_manifest,
                )

                logger.debug(
                    f"复制 manifest.yml: " f"{manifest_path} -> " f"{target_manifest}"
                )

                # ----------------------------------------------------
                # 替换插件目录
                # ----------------------------------------------------

                self._replace_plugin_directory(
                    temp_dir,
                    target_dir,
                )

                # temp_dir 已经移动到 target_dir，
                # 后续不能再删除 temp_dir。

                temp_dir = None

            finally:
                if temp_dir is not None and temp_dir.exists():
                    shutil.rmtree(
                        temp_dir,
                        ignore_errors=True,
                    )

                    logger.debug(f"清理临时导入目录: " f"{temp_dir}")

            if installed_version is None:
                success_msg = (
                    f"插件导入成功: "
                    f"{plugin_name} "
                    f"({plugin_id}) "
                    f"v{import_version}"
                )
            else:
                success_msg = (
                    f"插件升级成功: "
                    f"{plugin_name} "
                    f"({plugin_id}) "
                    f"{installed_version} "
                    f"-> {import_version}"
                )

            logger.info(success_msg)

            return ImportResult(
                success=True,
                message=success_msg,
                plugin_id=plugin_id,
                plugin_name=plugin_name,
                target_path=target_dir,
            )

        except (OSError, shutil.Error) as e:
            error_msg = f"复制插件文件失败: {e}"

            logger.exception(error_msg)

            return ImportResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
                plugin_name=plugin_name,
            )

    def import_plugins(
        self,
        manifest_paths: list[str | Path],
    ) -> BatchImportResult:
        """
        批量导入插件。

        同一个插件 ID 出现多个版本时，
        最终只有最高版本能够成功安装。

        不依赖输入文件顺序。

        Args:
            manifest_paths: manifest.yml 文件路径列表

        Returns:
            BatchImportResult: 批量导入结果
        """
        logger.info(f"开始批量导入插件，" f"共 {len(manifest_paths)} 个")

        results = []

        for path in manifest_paths:
            result = self.import_plugin(path)
            results.append(result)

            if result.success:
                logger.info(f"  ✓ {result.plugin_name}: " f"{result.message}")
            else:
                logger.warning(f"  ✗ {path}: " f"{result.message}")

        batch_result = BatchImportResult(results=results)

        logger.info(
            f"批量导入完成 - "
            f"成功: {batch_result.success_count}, "
            f"失败: {batch_result.failed_count}"
        )

        return batch_result

    def _replace_plugin_directory(
        self,
        source_dir: Path,
        target_dir: Path,
    ) -> None:
        """
        使用新的插件目录替换旧插件目录。

        如果目标不存在：
            source_dir -> target_dir

        如果目标存在：
            旧目录先移动到临时备份目录，
            新目录移动到正式位置，
            成功后删除旧目录。

        如果替换失败：
            尝试恢复旧目录。

        Args:
            source_dir: 已经准备完成的新插件目录
            target_dir: 正式插件目录

        Raises:
            OSError: 替换失败
        """
        if not source_dir.exists():
            raise OSError(f"临时插件目录不存在: {source_dir}")

        if target_dir.exists():
            backup_dir = self.plugin_dir.parent / (
                f".{target_dir.name}.backup-" f"{time.time_ns()}"
            )

            logger.debug(f"备份旧插件目录: " f"{target_dir} -> {backup_dir}")

            target_dir.rename(backup_dir)

            try:
                logger.debug(f"安装新插件目录: " f"{source_dir} -> {target_dir}")

                source_dir.rename(target_dir)

            except OSError:
                # 新目录替换失败，恢复旧版本。
                logger.error("新插件目录替换失败，" "尝试恢复旧插件")

                if target_dir.exists():
                    shutil.rmtree(
                        target_dir,
                        ignore_errors=True,
                    )

                if backup_dir.exists():
                    backup_dir.rename(target_dir)

                raise

            # 新版本已经成功成为正式目录，
            # 删除旧版本备份。
            try:
                shutil.rmtree(
                    backup_dir,
                    ignore_errors=False,
                )

                logger.debug(f"删除旧插件备份: " f"{backup_dir}")

            except OSError as e:
                # 新版本已经安装成功。
                # 备份删除失败不应该让导入被判定为失败。
                logger.warning(f"删除旧插件备份失败: " f"{backup_dir}, {e}")

        else:
            logger.debug(f"安装新插件目录: " f"{source_dir} -> {target_dir}")

            source_dir.rename(target_dir)

    # ====================================================================
    # 版本功能
    # ====================================================================

    @staticmethod
    def _compare_versions(
        version_a: str,
        version_b: str,
    ) -> int:
        """
        比较两个 SemVer 版本。

        Returns:
            -1: version_a < version_b
             0: version_a == version_b
             1: version_a > version_b

        例如：

            1.0.0 < 1.1.0
            1.1.0 < 2.0.0
            1.0.0-alpha < 1.0.0
            1.0.0-rc.1 < 1.0.0
        """
        a = PluginImportExportService._parse_version(version_a)
        b = PluginImportExportService._parse_version(version_b)

        # 比较 MAJOR / MINOR / PATCH
        if a[:3] != b[:3]:
            return 1 if a[:3] > b[:3] else -1

        a_prerelease = a[3]
        b_prerelease = b[3]

        # 都没有 prerelease
        if not a_prerelease and not b_prerelease:
            return 0

        # 正式版本 > prerelease
        if not a_prerelease:
            return 1

        if not b_prerelease:
            return -1

        # 比较 prerelease
        for a_identifier, b_identifier in zip(
            a_prerelease,
            b_prerelease,
        ):
            if a_identifier == b_identifier:
                continue

            a_numeric = a_identifier.isdigit()
            b_numeric = b_identifier.isdigit()

            # 数字标识符优先级低于非数字标识符
            if a_numeric and not b_numeric:
                return -1

            if not a_numeric and b_numeric:
                return 1

            if a_numeric and b_numeric:
                a_number = int(a_identifier)
                b_number = int(b_identifier)

                return 1 if a_number > b_number else -1

            return 1 if a_identifier > b_identifier else -1

        # 前面部分完全相同，
        # prerelease 标识符数量更多的版本更高。
        if len(a_prerelease) != len(b_prerelease):
            return 1 if len(a_prerelease) > len(b_prerelease) else -1

        return 0

    @staticmethod
    def _parse_version(
        version: str,
    ) -> tuple[int, int, int, list[str]]:
        """
        将 SemVer 拆分为：

            major
            minor
            patch
            prerelease

        build metadata 不参与版本比较。
        """
        match = re.fullmatch(
            r"(\d+)\.(\d+)\.(\d+)"
            r"(?:-([0-9A-Za-z-]+"
            r"(?:\.[0-9A-Za-z-]+)*))?"
            r"(?:\+[0-9A-Za-z-]+"
            r"(?:\.[0-9A-Za-z-]+)*)?",
            version,
        )

        if not match:
            raise ValueError(f"非法 SemVer: {version}")

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))

        prerelease = match.group(4).split(".") if match.group(4) else []

        return (
            major,
            minor,
            patch,
            prerelease,
        )

    # ====================================================================
    # 导出功能
    # ====================================================================

    def export_plugin(
        self,
        plugin_id: str,
        export_dir: str | Path,
    ) -> ExportResult:
        """
        导出插件到指定目录

        Args:
            plugin_id: 插件 ID
            export_dir: 导出目标目录

        Returns:
            ExportResult: 导出结果
        """
        export_dir = Path(export_dir)

        logger.info(f"开始导出插件: " f"{plugin_id} -> {export_dir}")

        # ------------------------------------------------------------
        # 检查插件是否存在
        # ------------------------------------------------------------

        source_dir = self.plugin_dir / plugin_id

        if not source_dir.exists():
            error_msg = f"插件不存在: {plugin_id}"

            logger.error(error_msg)

            return ExportResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
            )

        if not source_dir.is_dir():
            error_msg = f"插件路径不是目录: " f"{source_dir}"

            logger.error(error_msg)

            return ExportResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
            )

        # ------------------------------------------------------------
        # 检查导出目录
        # ------------------------------------------------------------

        if not export_dir.exists():
            try:
                export_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                logger.debug(f"创建导出目录: {export_dir}")

            except OSError as e:
                error_msg = f"无法创建导出目录: {e}"

                logger.error(error_msg)

                return ExportResult(
                    success=False,
                    message=error_msg,
                    plugin_id=plugin_id,
                )

        # ------------------------------------------------------------
        # 复制插件目录
        # ------------------------------------------------------------

        target_dir = export_dir / plugin_id

        # 如果目标已存在，添加时间戳
        if target_dir.exists():
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            target_dir = export_dir / f"{plugin_id}_{timestamp}"

            logger.debug(f"目标目录已存在，" f"使用新名称: {target_dir}")

        try:
            shutil.copytree(
                source_dir,
                target_dir,
            )

            success_msg = f"插件导出成功: {plugin_id}"

            logger.info(success_msg)

            return ExportResult(
                success=True,
                message=success_msg,
                plugin_id=plugin_id,
                export_path=target_dir,
            )

        except (OSError, shutil.Error) as e:
            error_msg = f"导出失败: {e}"

            logger.exception(error_msg)

            return ExportResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
            )

    # ====================================================================
    # 删除功能
    # ====================================================================

    def delete_plugin(
        self,
        plugin_id: str,
    ) -> DeleteResult:
        """
        删除已安装插件。

        流程：
        1. 校验插件目录存在
        2. 读取 manifest 确认 ID 一致（防止误删）
        3. 移入临时备份目录（而非直接 rmtree），便于失败恢复
        4. 删除备份

        Args:
            plugin_id: 插件 ID

        Returns:
            DeleteResult: 删除结果
        """
        logger.info(f"开始删除插件: {plugin_id}")

        target_dir = self.plugin_dir / plugin_id

        # ------------------------------------------------------------
        # 1. 校验目录
        # ------------------------------------------------------------

        if not target_dir.exists():
            error_msg = f"插件不存在: {plugin_id}"
            logger.error(error_msg)

            return DeleteResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
            )

        if not target_dir.is_dir():
            error_msg = f"插件路径不是目录: {target_dir}"
            logger.error(error_msg)

            return DeleteResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
            )

        manifest_path = target_dir / "manifest.yml"

        if not manifest_path.exists():
            error_msg = f"插件目录缺少 manifest.yml: " f"{target_dir}"
            logger.error(error_msg)

            return DeleteResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
            )

        # ------------------------------------------------------------
        # 2. 校验 manifest ID 与目录名一致
        # ------------------------------------------------------------

        try:
            manifest = self.parser.parse(manifest_path)
            installed_id = manifest.metadata.id
            plugin_name = manifest.metadata.name

        except (
            ManifestParseError,
            OSError,
            ValueError,
        ) as e:
            error_msg = f"解析 manifest 失败，拒绝删除: {e}"
            logger.error(error_msg)

            return DeleteResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
            )

        if installed_id != plugin_id:
            error_msg = (
                f"插件目录与 Manifest ID 不一致，"
                f"拒绝删除: "
                f"目录={plugin_id}, "
                f"Manifest ID={installed_id}"
            )
            logger.error(error_msg)

            return DeleteResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
                plugin_name=plugin_name,
            )

        # ------------------------------------------------------------
        # 3. 移入备份目录
        # ------------------------------------------------------------

        backup_dir = self.plugin_dir.parent / (
            f".{plugin_id}.delete-" f"{time.time_ns()}"
        )

        try:
            target_dir.rename(backup_dir)

            logger.debug(f"插件目录已移入备份: " f"{target_dir} -> {backup_dir}")

        except OSError as e:
            error_msg = f"移入备份目录失败: {e}"
            logger.exception(error_msg)

            return DeleteResult(
                success=False,
                message=error_msg,
                plugin_id=plugin_id,
                plugin_name=plugin_name,
            )

        # ------------------------------------------------------------
        # 4. 删除备份
        # ------------------------------------------------------------

        try:
            shutil.rmtree(backup_dir)

            logger.debug(f"备份已删除: {backup_dir}")

        except OSError as e:
            # 备份删不掉不影响删除结果，但要记录
            logger.warning(f"删除备份目录失败: " f"{backup_dir}, {e}")

        success_msg = f"插件删除成功: " f"{plugin_name} ({plugin_id})"

        logger.info(success_msg)

        return DeleteResult(
            success=True,
            message=success_msg,
            plugin_id=plugin_id,
            plugin_name=plugin_name,
        )

    # ====================================================================
    # 重新加载功能
    # ====================================================================

    def reload_manifests(self) -> list:
        """
        重新加载所有插件清单

        使用 PluginLoader 发现插件，
        使用 ManifestParser 解析清单。

        Returns:
            list[Manifest]: 解析后的插件清单列表
        """
        logger.info("重新加载插件清单")

        manifests = []
        manifest_paths = self.loader.discover()

        logger.debug(f"发现 {len(manifest_paths)} " f"个 manifest 文件")

        for manifest_path in manifest_paths:
            try:
                manifest = self.parser.parse(manifest_path)

                manifests.append(manifest)

                logger.debug(
                    f"  加载插件: "
                    f"{manifest.metadata.name} "
                    f"(ID: {manifest.metadata.id})"
                )

            except (
                ManifestParseError,
                OSError,
                ValueError,
            ) as e:
                logger.error(f"解析失败: " f"{manifest_path}, " f"错误: {e}")

        logger.info(f"成功加载 {len(manifests)} 个插件")

        return manifests


# ====================================================================
# 便捷函数
# ====================================================================


def import_plugin(
    manifest_path: str | Path,
) -> ImportResult:
    """
    便捷函数：导入单个插件

    Example:
        >>> result = import_plugin(
        ...     "path/to/manifest.yml"
        ... )
    """
    service = PluginImportExportService()

    return service.import_plugin(manifest_path)


def export_plugin(
    plugin_id: str,
    export_dir: str | Path,
) -> ExportResult:
    """
    便捷函数：导出插件

    Example:
        >>> result = export_plugin(
        ...     "file_archiver",
        ...     "/backup",
        ... )
    """
    service = PluginImportExportService()

    return service.export_plugin(
        plugin_id,
        export_dir,
    )


def delete_plugin(
    plugin_id: str,
) -> DeleteResult:
    """
    便捷函数：删除插件

    Example:
        >>> result = delete_plugin("file_archiver")
    """
    service = PluginImportExportService()

    return service.delete_plugin(plugin_id)


__all__ = [
    "BatchImportResult",
    "DeleteResult",
    "ExportResult",
    "ImportResult",
    "PluginImportExportService",
    "delete_plugin",
    "export_plugin",
    "import_plugin",
]
