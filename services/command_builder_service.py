# services/command_builder_service.py

"""
命令构建服务

负责根据 Manifest 和 ToolState 构建最终 CLI 命令。

职责范围：
    - 获取工具命令配置
    - 获取参数当前值
    - 处理默认值
    - 检查必填参数
    - 将参数转换为 CLI 参数
    - 构建最终命令字符串

不负责：
    - GUI 界面更新
    - 参数输入
    - ToolState 持久化
    - 命令执行

输入：
    Manifest
    ToolState

输出：
    str
    例如：

        python --in "input.txt" --out "output.txt" --bool
"""

from __future__ import annotations

import subprocess

from models.manifest import Manifest, Parameter
from models.state import ToolState
from utils.log import get_logger
from utils.paths import get_log_dir

logger = get_logger(
    name="command_builder_service",
    log_dir=get_log_dir() / "logs",
    fmt_type="detailed",
    console_level=10,
    file_level=10,
)


class CommandBuilderService:
    """CLI 命令构建服务。"""

    # ====================================================================
    # 对外接口
    # ====================================================================

    def build(
        self,
        manifest: Manifest,
        tool_state: ToolState,
    ) -> str:
        """
        根据 Manifest 和 ToolState 构建完整命令。

        Args:
            manifest: 当前工具 Manifest。
            tool_state: 当前工具运行时状态。

        Returns:
            str: 最终命令字符串。

        Raises:
            ValueError:
                参数配置错误或必填参数缺失。
        """

        logger.debug(
            "开始构建命令: tool_id=%s",
            manifest.metadata.id,
        )

        parts: list[str] = []

        # ------------------------------------------------------------
        # 基础可执行命令
        # ------------------------------------------------------------

        language = manifest.runtime.language

        if not language:
            raise ValueError(
                f"工具没有配置 runtime.language: " f"{manifest.metadata.id}"
            )

        entry = manifest.runtime.entry

        if not entry:
            raise ValueError(f"工具没有配置 runtime.entry: " f"{manifest.metadata.id}")

        parts.extend(
            [
                language,
                entry,
            ]
        )

        # ------------------------------------------------------------
        # 构建参数
        # ------------------------------------------------------------

        for parameter in manifest.parameters:
            argument_parts = self._build_parameter(
                parameter,
                tool_state,
            )

            parts.extend(argument_parts)

        # ------------------------------------------------------------
        # Windows 命令行格式化
        # ------------------------------------------------------------

        command = subprocess.list2cmdline(parts)

        logger.info(
            "命令构建完成: tool_id=%s command=%s",
            manifest.metadata.id,
            command,
        )

        return command

    # ====================================================================
    # 参数构建
    # ====================================================================

    def _build_parameter(
        self,
        parameter: Parameter,
        tool_state: ToolState,
    ) -> list[str]:
        """
        构建单个参数对应的 CLI 参数。

        Returns:
            list[str]:
                例如：

                ["--input", "test.txt"]

                或：

                ["--verbose"]
        """

        # ------------------------------------------------------------
        # 没有 CLI 映射
        # ------------------------------------------------------------

        if parameter.cli is None:
            logger.debug(
                "参数没有 CLI 映射，跳过: id=%s",
                parameter.id,
            )
            return []

        flag = parameter.cli.flag

        if not flag:
            raise ValueError(f"参数 CLI flag 不能为空: " f"parameter={parameter.id}")

        # ------------------------------------------------------------
        # 获取参数值
        #
        # ToolState 优先：
        #   ToolState -> Parameter.default
        # ------------------------------------------------------------

        if tool_state.has(parameter.id):
            value = tool_state.get(parameter.id)

            logger.debug(
                "使用 ToolState 参数值: id=%s value=%r",
                parameter.id,
                value,
            )
        else:
            value = parameter.default

            logger.debug(
                "ToolState 中没有参数，使用默认值: " "id=%s default=%r",
                parameter.id,
                value,
            )

        # ------------------------------------------------------------
        # 根据参数类型构建 CLI
        # ------------------------------------------------------------

        parameter_type = parameter.type.lower()

        if parameter_type in {
            "boolean",
            "bool",
        }:
            return self._build_boolean(
                parameter,
                flag,
                value,
            )

        if parameter_type in {
            "multi",
        }:
            return self._build_multi(
                parameter,
                flag,
                value,
            )

        if parameter_type in {
            "string",
            "file",
            "directory",
            "dir",
            "single",
            "enum",
        }:
            return self._build_value(
                parameter,
                flag,
                value,
            )

        raise ValueError(
            f"不支持的参数类型: " f"parameter={parameter.id}, " f"type={parameter.type}"
        )

    # ====================================================================
    # 普通值参数
    # ====================================================================

    @staticmethod
    def _build_value(
        parameter: Parameter,
        flag: str,
        value: object,
    ) -> list[str]:
        """
        构建普通值参数。

        例如：

            --input test.txt
            --mode option1
        """

        # ------------------------------------------------------------
        # 空值处理
        # ------------------------------------------------------------

        if value is None or value == "":
            if parameter.required:
                raise ValueError(
                    f"必填参数没有提供值: " f"{parameter.label} ({parameter.id})"
                )

            return []

        # ------------------------------------------------------------
        # 构建参数
        # ------------------------------------------------------------

        return [
            flag,
            str(value),
        ]

    # ====================================================================
    # Boolean
    # ====================================================================

    @staticmethod
    def _build_boolean(
        parameter: Parameter,
        flag: str,
        value: object,
    ) -> list[str]:
        """
        构建布尔参数。

        True：

            --bool

        False：

            不输出任何参数。
        """

        enabled = bool(value)

        if enabled:
            return [flag]

        # bool=False 不需要输出 flag。
        #
        # 这是典型的 CLI switch 行为：
        #
        #   --verbose
        #
        # 而不是：
        #
        #   --verbose false

        return []

    # ====================================================================
    # Multi
    # ====================================================================

    @staticmethod
    def _build_multi(
        parameter: Parameter,
        flag: str,
        value: object,
    ) -> list[str]:
        """
        构建多选参数。

        当前采用：

            --multi option1 --multi option2

        例如：

            value = ["option1", "option3"]

        输出：

            ["--multi", "option1", "--multi", "option3"]
        """

        if value is None:
            values: list[object] = []

        elif isinstance(value, (list, tuple, set)):
            values = list(value)

        else:
            raise ValueError(
                f"多选参数必须是 list/tuple/set: "
                f"parameter={parameter.id}, "
                f"value={value!r}"
            )

        if not values:
            if parameter.required:
                raise ValueError(
                    f"必填多选参数没有选择任何值: "
                    f"{parameter.label} ({parameter.id})"
                )

            return []

        result: list[str] = []

        for item in values:
            if item is None or str(item) == "":
                continue

            result.extend(
                [
                    flag,
                    str(item),
                ]
            )

        if not result and parameter.required:
            raise ValueError(
                f"必填多选参数没有有效值: " f"{parameter.label} ({parameter.id})"
            )

        return result

    # ====================================================================
    # 工具方法
    # ====================================================================

    @staticmethod
    def get_current_value(
        parameter: Parameter,
        tool_state: ToolState,
    ) -> object:
        """
        获取参数当前值。

        优先级：

            ToolState
                ↓
            Parameter.default
        """

        if tool_state.has(parameter.id):
            return tool_state.get(parameter.id)

        return parameter.default
