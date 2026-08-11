# services\manifest_parser_service.py

"""
Manifest 解析服务

负责解析 YAML 格式的插件清单文件，并将其转换为内部数据模型。

职责范围：
    - 读取和解析 manifest.yml 文件
    - 验证必要字段的存在性
    - 将原始数据转换为 Manifest 数据模型
    - 处理 CLI 参数的可选配置

不负责：
    - GUI 界面相关操作
    - 命令生成和执行
    - 配置文件的保存和写入
    - 插件运行时管理

依赖：
    - PyYAML: 用于解析 YAML 文件
    - models.manifest: 数据模型定义
    - log: 日志模块

Example:
    >>> parser = ManifestParser()
    >>> manifest = parser.parse("path/to/manifest.yml")
    >>> print(manifest.metadata.name)
"""

import time
from pathlib import Path
from typing import Any, ClassVar

import yaml

from models.manifest import (
    CLI,
    Command,
    Manifest,
    Metadata,
    Parameter,
    Runtime,
)
from utils.log import get_logger
from utils.paths import get_log_dir

# 创建该模块专用的日志记录器
logger = get_logger(
    name="manifest_parser",
	log_dir=get_log_dir() / "logs",
    fmt_type="detailed",
    console_level=20,  # INFO
    file_level=10,  # DEBUG
)


class ManifestParseError(Exception):
    """Manifest 解析异常"""


class ManifestParser:
    """
    Manifest 文件解析器

    负责读取 YAML 格式的清单文件并转换为结构化数据模型。

    Attributes:
        无实例属性，所有功能通过方法提供

    Usage:
        parser = ManifestParser()

        # 基本用法
        manifest = parser.parse("plugin/manifest.yml")

        # 使用 Path 对象
        from pathlib import Path
        manifest = parser.parse(Path("plugin/manifest.yml"))
    """

    # 必需的顶层字段
    REQUIRED_FIELDS: ClassVar[set[str]] = {
        "schema_version",
        "metadata",
        "runtime",
        "command",
    }

    # 必需的 metadata 子字段
    REQUIRED_METADATA_FIELDS: ClassVar[set[str]] = {"id", "name", "version"}

    # 必需的 parameter 子字段
    REQUIRED_PARAMETER_FIELDS: ClassVar[set[str]] = {"id", "label", "type"}

    def parse(self, path: str | Path) -> Manifest:
        """
        解析 manifest 文件

        Args:
            path: manifest.yml 文件的路径，可以是字符串或 Path 对象

        Returns:
            Manifest: 解析后的清单数据模型

        Raises:
            FileNotFoundError: 文件不存在
            ManifestParseError: YAML 格式错误或缺少必要字段
            yaml.YAMLError: YAML 解析错误

        Example:
            >>> parser = ManifestParser()
            >>> manifest = parser.parse("path/to/manifest.yml")
        """
        start_time = time.time()
        path = Path(path)

        logger.info(f"开始解析 manifest 文件: {path}")
        logger.debug(f"文件绝对路径: {path.absolute()}")
        logger.debug(f"文件是否存在: {path.exists()}")

        # 验证文件存在性
        if not path.exists():
            logger.error(f"Manifest 文件不存在: {path}")
            raise FileNotFoundError(f"Manifest 文件不存在: {path}")

        if not path.is_file():
            logger.error(f"路径不是有效的文件: {path}")
            raise ManifestParseError(f"路径不是有效的文件: {path}")

        logger.debug(f"文件大小: {path.stat().st_size} 字节")

        # 读取并解析 YAML 文件
        logger.debug("开始读取 YAML 文件")
        data = self._read_yaml(path)
        logger.debug(f"YAML 解析完成，顶层键: {list(data.keys())}")

        # 验证并转换数据模型
        logger.info("开始验证并转换数据模型")
        manifest = self._parse_manifest(data)

        elapsed_time = time.time() - start_time
        logger.info(
            f"Manifest 解析成功 - 插件: {manifest.metadata.name} "
            f"(ID: {manifest.metadata.id}, "
            f"版本: {manifest.metadata.version}, "
            f"参数数量: {len(manifest.parameters)}, "
            f"耗时: {elapsed_time:.3f}s)"
        )

        return manifest

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        """
        读取并解析 YAML 文件

        Args:
            path: YAML 文件路径

        Returns:
            Dict[str, Any]: 解析后的字典数据

        Raises:
            yaml.YAMLError: YAML 解析错误
            ManifestParseError: 文件为空或格式错误
        """
        logger.debug(f"打开文件: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                logger.debug("文件打开成功，开始解析 YAML")
                data = yaml.safe_load(f)

            if data is None:
                logger.error(f"Manifest 文件为空: {path}")
                raise ManifestParseError(f"Manifest 文件为空: {path}")

            if not isinstance(data, dict):
                logger.error(
                    f"Manifest 文件格式错误，应为字典结构，"
                    f"实际为: {type(data).__name__}"
                )
                raise ManifestParseError(
                    f"Manifest 文件格式错误，应为字典结构，实际为: {type(data).__name__}"
                )

            logger.debug(f"YAML 解析成功，包含 {len(data)} 个顶层字段")
            return data

        except yaml.YAMLError as e:
            logger.error(f"YAML 解析错误 ({path}): {e}")
            raise yaml.YAMLError(f"YAML 解析错误 ({path}): {e}")
        except Exception:
            logger.exception("读取文件时发生意外错误")
            raise

    def _parse_manifest(self, data: dict[str, Any]) -> Manifest:
        """
        解析 manifest 数据结构

        Args:
            data: YAML 解析后的字典数据

        Returns:
            Manifest: 完整的清单数据模型

        Raises:
            ManifestParseError: 缺少必要字段或数据格式错误
        """
        logger.debug("验证 manifest 必要字段")
        # 验证必要字段
        self._validate_required_fields(data, self.REQUIRED_FIELDS, "manifest")
        logger.debug("Manifest 必要字段验证通过")

        # 解析各子模块
        logger.debug("开始解析 metadata")
        metadata = self._parse_metadata(data["metadata"])
        logger.debug(f"Metadata 解析完成: {metadata.name} (ID: {metadata.id})")

        logger.debug("开始解析 runtime")
        runtime = self._parse_runtime(data["runtime"])
        logger.debug(f"Runtime 解析完成: {runtime.language} - {runtime.entry}")

        logger.debug("开始解析 command")
        command = self._parse_command(data["command"])
        logger.debug(f"Command 解析完成: {command.executable}")

        logger.debug("开始解析 parameters")
        parameters = self._parse_parameters(data.get("parameters", []))
        logger.debug(f"Parameters 解析完成，共 {len(parameters)} 个参数")

        # 构建完整的 Manifest 对象
        logger.info(f"构建 Manifest 对象 - schema_version: {data['schema_version']}")
        return Manifest(
            schema_version=data["schema_version"],
            metadata=metadata,
            runtime=runtime,
            command=command,
            parameters=parameters,
        )

    def _parse_metadata(self, data: dict[str, Any]) -> Metadata:
        """
        解析元数据信息

        Args:
            data: metadata 字典数据

        Returns:
            Metadata: 元数据对象

        Raises:
            ManifestParseError: 缺少必要字段
        """
        logger.debug(f"验证 metadata 必要字段: {self.REQUIRED_METADATA_FIELDS}")
        self._validate_required_fields(data, self.REQUIRED_METADATA_FIELDS, "metadata")
        logger.debug("Metadata 必要字段验证通过")

        metadata = Metadata(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
        )

        logger.debug(
            f"Metadata 对象创建成功 - "
            f"ID: {metadata.id}, "
            f"名称: {metadata.name}, "
            f"版本: {metadata.version}, "
            f"描述: {metadata.description if metadata.description else '(无)'}"
        )

        return metadata

    def _parse_runtime(self, data: dict[str, Any]) -> Runtime:
        """
        解析运行时配置

        Args:
            data: runtime 字典数据

        Returns:
            Runtime: 运行时配置对象

        Raises:
            ManifestParseError: 缺少 language 或 entry 字段
        """
        logger.debug("验证 runtime 必要字段: language, entry")

        if "language" not in data:
            logger.error("runtime 缺少必要字段: language")
            raise ManifestParseError("runtime 缺少必要字段: language")
        if "entry" not in data:
            logger.error("runtime 缺少必要字段: entry")
            raise ManifestParseError("runtime 缺少必要字段: entry")

        runtime = Runtime(language=data["language"], entry=data["entry"])
        logger.debug(
            f"Runtime 对象创建成功 - 语言: {runtime.language}, 入口: {runtime.entry}"
        )

        return runtime

    def _parse_command(self, data: dict[str, Any]) -> Command:
        """
        解析命令配置

        Args:
            data: command 字典数据

        Returns:
            Command: 命令配置对象

        Raises:
            ManifestParseError: 缺少 executable 或 workdir 字段
        """
        logger.debug("验证 command 必要字段: executable, workdir")

        if "executable" not in data:
            logger.error("command 缺少必要字段: executable")
            raise ManifestParseError("command 缺少必要字段: executable")
        if "workdir" not in data:
            logger.error("command 缺少必要字段: workdir")
            raise ManifestParseError("command 缺少必要字段: workdir")

        command = Command(executable=data["executable"], workdir=data["workdir"])
        logger.debug(
            f"Command 对象创建成功 - "
            f"可执行文件: {command.executable}, "
            f"工作目录: {command.workdir}"
        )

        return command

    def _parse_parameters(self, data: list[dict[str, Any]]) -> list[Parameter]:
        """
        解析参数列表

        Args:
            data: parameters 列表数据

        Returns:
            List[Parameter]: 参数对象列表

        Raises:
            ManifestParseError: 参数格式错误或缺少必要字段
        """
        logger.info(f"开始解析参数列表，共 {len(data)} 个参数")
        parameters = []

        for i, item in enumerate(data):
            logger.debug(f"解析第 {i + 1} 个参数: {item.get('id', '未知ID')}")
            try:
                parameter = self._parse_single_parameter(item, i)
                parameters.append(parameter)
                logger.debug(
                    f"参数 {i + 1} 解析成功 - "
                    f"ID: {parameter.id}, "
                    f"类型: {parameter.type}, "
                    f"必需: {parameter.required}"
                )
            except Exception as e:
                logger.exception(f"解析第 {i + 1} 个参数时出错")
                raise ManifestParseError(f"解析第 {i + 1} 个参数时出错: {e}")

        logger.info(f"参数列表解析完成，成功解析 {len(parameters)} 个参数")
        return parameters

    def _parse_single_parameter(self, item: dict[str, Any], index: int) -> Parameter:
        """
        解析单个参数配置

        Args:
            item: 单个参数的字典数据
            index: 参数在列表中的索引（用于错误提示）

        Returns:
            Parameter: 参数配置对象

        Raises:
            ManifestParseError: 参数缺少必要字段
        """
        param_id = item.get("id", f"索引{index}")
        logger.debug(f"验证参数 {param_id} 的必要字段")

        # 验证必要字段
        self._validate_required_fields(
            item, self.REQUIRED_PARAMETER_FIELDS, f"parameter[{index}]"
        )
        logger.debug(f"参数 {param_id} 必要字段验证通过")

        # 解析可选的 CLI 配置
        if "cli" in item:
            logger.debug(f"参数 {param_id} 包含 CLI 配置")
            cli = self._parse_cli(item["cli"])
        else:
            logger.debug(f"参数 {param_id} 不包含 CLI 配置")
            cli = None

        # 构建 Parameter 对象
        parameter = Parameter(
            id=item["id"],
            label=item["label"],
            type=item["type"],
            required=item.get("required", False),
            default=item.get("default"),
            description=item.get("description", ""),
            choices=item.get("choices", []),
            history=item.get("history", False),
            cli=cli,
        )

        logger.debug(
            f"Parameter 对象创建成功 - "
            f"ID: {parameter.id}, "
            f"标签: {parameter.label}, "
            f"类型: {parameter.type}, "
            f"必需: {parameter.required}, "
            f"有默认值: {parameter.default is not None}, "
            f"有CLI: {parameter.cli is not None}, "
            f"选项数量: {len(parameter.choices)}, "
            f"记录历史: {parameter.history}"
        )

        return parameter

    def _parse_cli(self, data: dict[str, Any]) -> CLI | None:
        """
        解析 CLI 配置

        Args:
            data: CLI 字典数据，可能为 None

        Returns:
            Optional[CLI]: CLI 配置对象，如果 data 为 None 则返回 None

        Raises:
            ManifestParseError: CLI 配置缺少 flag 字段
        """
        if data is None:
            logger.debug("CLI 配置为空，返回 None")
            return None

        logger.debug("验证 CLI 配置必要字段: flag")
        if "flag" not in data:
            logger.error("CLI 配置缺少必要字段: flag")
            raise ManifestParseError("CLI 配置缺少必要字段: flag")

        cli = CLI(flag=data["flag"])
        logger.debug(f"CLI 对象创建成功 - 标志: {cli.flag}")

        return cli

    def _validate_required_fields(
        self, data: dict[str, Any], required_fields: set, context: str
    ) -> None:
        """
        验证必要字段是否存在

        Args:
            data: 待验证的数据字典
            required_fields: 必需的字段集合
            context: 上下文描述（用于错误提示）

        Raises:
            ManifestParseError: 缺少必要字段
        """
        logger.debug(f"验证 {context} 的必要字段: {required_fields}")

        if not isinstance(data, dict):
            logger.error(f"{context} 应为字典类型，实际为: {type(data).__name__}")
            raise ManifestParseError(
                f"{context} 应为字典类型，实际为: {type(data).__name__}"
            )

        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            missing_str = ", ".join(sorted(missing_fields))
            logger.error(f"{context} 缺少必要字段: {missing_str}")
            logger.debug(f"当前字段: {list(data.keys())}")
            raise ManifestParseError(f"{context} 缺少必要字段: {missing_str}")

        logger.debug(f"{context} 字段验证通过，包含字段: {list(data.keys())}")

    @staticmethod
    def validate_manifest_schema(data: dict[str, Any]) -> list[str]:
        """
        静态方法：验证 manifest 数据结构的完整性

        Args:
            data: manifest 字典数据

        Returns:
            List[str]: 验证错误信息列表，空列表表示验证通过

        Example:
            >>> errors = ManifestParser.validate_manifest_schema(data)
            >>> if errors:
            ...     for error in errors:
            ...         print(f"验证错误: {error}")
        """
        logger.info("开始验证 manifest schema")
        errors = []
        parser = ManifestParser()

        try:
            parser._validate_required_fields(data, parser.REQUIRED_FIELDS, "manifest")
            logger.debug("Schema 验证: manifest 顶层字段通过")
        except ManifestParseError as e:
            logger.error(f"Schema 验证失败: {e}")
            errors.append(str(e))
            return errors

        try:
            parser._parse_metadata(data.get("metadata", {}))
            logger.debug("Schema 验证: metadata 字段通过")
        except ManifestParseError as e:
            logger.error(f"Schema 验证失败 (metadata): {e}")
            errors.append(str(e))

        try:
            parser._parse_parameters(data.get("parameters", []))
            logger.debug("Schema 验证: parameters 字段通过")
        except ManifestParseError as e:
            logger.error(f"Schema 验证失败 (parameters): {e}")
            errors.append(str(e))

        if errors:
            logger.warning(f"Schema 验证完成，发现 {len(errors)} 个错误")
        else:
            logger.info("Schema 验证通过")

        return errors


# 便捷函数
def parse_manifest(path: str | Path) -> Manifest:
    """
    便捷函数：快速解析 manifest 文件

    Args:
        path: manifest 文件路径

    Returns:
        Manifest: 解析后的清单对象

    Example:
        >>> manifest = parse_manifest("plugin/manifest.yml")
    """
    logger.info(f"便捷函数 parse_manifest 被调用，路径: {path}")
    parser = ManifestParser()
    return parser.parse(path)


def parse_manifests(paths: list[str | Path]) -> list[Manifest]:
    """
    便捷函数：批量解析 manifest 文件

    Args:
        paths: manifest 文件路径列表

    Returns:
        list[Manifest]: 解析后的清单对象列表

    Example:
        >>> manifests = parse_manifests([
        ...     "plugin1/manifest.yml",
        ...     "plugin2/manifest.yml"
        ... ])
    """
    logger.info(f"便捷函数 parse_manifests 被调用，路径数量: {len(paths)}")
    parser = ManifestParser()
    manifests = []

    for path in paths:
        try:
            manifest = parser.parse(path)
            manifests.append(manifest)
            logger.debug(f"成功解析: {path}")
        except Exception as e:
            logger.error(f"解析失败: {path}, 错误: {e}")
            # 可以选择继续处理其他文件或重新抛出异常
            # 这里选择继续处理，但记录错误
            # 如果需要严格模式，可以取消下面的注释
            # raise

    logger.info(f"批量解析完成，成功: {len(manifests)}/{len(paths)}")
    return manifests
