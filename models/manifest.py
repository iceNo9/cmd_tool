# models\manifest.py

"""
Manifest 数据模型模块

定义插件清单（Manifest）所需的所有数据类，用于描述插件的基本信息、
运行环境、命令配置和参数规范。

模块结构：
    - Metadata: 插件元数据信息
    - Runtime: 运行时环境配置
    - Command: 命令执行配置
    - CLI: 命令行接口标志配置
    - Parameter: 参数定义规范
    - Manifest: 插件清单总配置
"""

from dataclasses import dataclass, field


@dataclass
class Metadata:
    """
    插件元数据信息

    用于唯一标识和描述一个插件的基本属性。

    Attributes:
        id: 插件唯一标识符，用于在系统中唯一标识该插件
        name: 插件显示名称，用于用户界面展示
        version: 插件版本号，遵循语义化版本规范（如 "1.0.0"）
        description: 插件功能描述，简要说明插件的用途和功能，默认为空字符串
    """

    id: str
    """插件唯一标识符"""

    name: str
    """插件显示名称"""

    version: str
    """插件版本号，遵循语义化版本规范"""

    description: str = ""
    """插件功能描述，默认为空字符串"""


@dataclass
class Runtime:
    """
    运行时环境配置

    定义插件运行所需的编程语言和入口文件。

    Attributes:
        language: 编程语言类型（如 "python"、"node"、"ruby" 等）
        entry: 入口文件路径，相对于插件根目录的可执行脚本路径
    """

    language: str
    """编程语言类型"""

    entry: list[str]
    """入口文件路径或命令参数列表"""


@dataclass
class Command:
    """
    命令执行配置

    定义插件的可执行命令和工作目录。

    Attributes:
        executable: 可执行命令或脚本路径，相对于 workdir 或绝对路径
        workdir: 工作目录路径，命令执行时的当前工作目录
    """

    executable: str
    """可执行命令或脚本路径"""

    workdir: str
    """工作目录路径，命令执行时的当前工作目录"""


@dataclass
class CLI:
    """
    命令行接口标志配置

    定义参数在命令行中的表示形式。

    Attributes:
        flag: 命令行标志字符串（如 "--input"、"-o"、"--verbose" 等）

    Example:
        CLI(flag="--config")  # 对应命令行参数 --config
        CLI(flag="-c")        # 对应命令行参数 -c
    """

    flag: str
    """命令行标志字符串"""


@dataclass
class Parameter:
    """
    参数定义规范

    详细描述插件可接受的参数配置，包括参数类型、验证规则和 CLI 映射。

    Attributes:
        id: 参数唯一标识符，用于程序内部引用
        label: 参数标签，用于用户界面显示的友好名称
        type: 参数数据类型（如 "string"、"integer"、"float"、"boolean"、"file"、"directory" 等）
        required: 是否为必需参数，默认为 False
        default: 参数默认值，当用户未提供时使用，默认为 None
        description: 参数说明文档，帮助用户理解参数用途，默认为空字符串
        cli: CLI 配置对象，定义参数在命令行中的表示方式，默认为 None
        choices: 可选值列表，用于限制参数的合法取值范围（如枚举类型），默认为空列表
        history: 是否记录参数历史值，用于自动补全等功能，默认为 False

    Example:
        # 必需参数示例
        Parameter(
            id="input_file",
            label="输入文件",
            type="file",
            required=True,
            description="需要处理的输入文件路径",
            cli=CLI(flag="--input")
        )

        # 带选项的参数示例
        Parameter(
            id="mode",
            label="处理模式",
            type="string",
            default="normal",
            choices=["normal", "fast", "thorough"],
            description="选择处理模式",
            cli=CLI(flag="--mode")
        )
    """

    id: str
    """参数唯一标识符"""

    label: str
    """参数显示标签"""

    type: str
    """参数数据类型（如 string、integer、float、boolean、file、directory）"""

    required: bool = False
    """是否为必需参数"""

    default: object = None
    """参数默认值"""

    description: str = ""
    """参数说明文档"""

    cli: CLI | None = None
    """CLI 标志配置，None 表示该参数不映射到命令行"""

    choices: list[str] = field(default_factory=list)
    """可选值列表，限制参数的合法取值范围"""

    history: bool = False
    """是否记录历史值"""


@dataclass
class Manifest:
    """
    插件清单总配置

    完整的插件描述文件，包含插件的所有配置信息。
    该数据类映射到插件根目录下的 manifest.json 或 manifest.yaml 文件。

    Attributes:
        schema_version: 清单模式的版本号，用于兼容性控制
        metadata: 插件元数据信息
        runtime: 运行时环境配置
        command: 命令执行配置
        parameters: 参数定义列表，默认为空列表

    Example:
        >>> manifest = Manifest(
        ...     schema_version=1,
        ...     metadata=Metadata(
        ...         id="com.example.myplugin",
        ...         name="My Plugin",
        ...         version="1.0.0",
        ...         description="一个示例插件"
        ...     ),
        ...     runtime=Runtime(
        ...         language="python",
        ...         entry="main.py"
        ...     ),
        ...     command=Command(
        ...         executable="python",
        ...         workdir="./plugin"
        ...     ),
        ...     parameters=[
        ...         Parameter(
        ...             id="input",
        ...             label="输入文件",
        ...             type="file",
        ...             required=True,
        ...             cli=CLI(flag="--input")
        ...         )
        ...     ]
        ... )
    """

    schema_version: int
    """清单模式版本号，用于兼容性控制"""

    metadata: Metadata
    """插件元数据信息"""

    runtime: Runtime
    """运行时环境配置"""

    command: Command
    """命令执行配置"""

    parameters: list[Parameter] = field(default_factory=list)
    """参数定义列表"""


# 类型别名，便于外部引用
__all__ = [
    "CLI",
    "Command",
    "Manifest",
    "Metadata",
    "Parameter",
    "Runtime",
]
