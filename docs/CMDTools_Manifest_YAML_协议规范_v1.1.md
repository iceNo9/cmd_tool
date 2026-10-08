# CMDTools Manifest YAML 协议规范

> 版本：1.0  
> 适用范围：CMDTools 当前 Manifest / ParameterPanel / CommandBuilderService 实现  
> 目标：作为“工具描述 → `manifest.yml`”的标准输入协议，确保生成的 YAML 能被当前 CMDTools 正确解析、显示并构建命令。

---

## 1. 协议总览

一个工具通过 `manifest.yml` 描述：

- 工具身份与元数据
- 运行时命令的基础部分
- CLI 参数
- 参数类型、默认值、是否必填
- 参数与 CLI flag 的映射
- Shell 环境

当前命令构建流程可以概括为：

```text
Manifest
   +
ToolState
   ↓
CommandBuilderService
   ↓
runtime.language + runtime.entry
   +
parameters
   ↓
Shell 格式化
   ↓
最终命令字符串
```

CMDTools **只生成命令，不执行命令**。

---

# 2. Manifest 基本结构

推荐结构：

```yaml
schema_version: 1

metadata:
  id: example-tool
  name: Example Tool
  version: 1.0.0
  description: 示例工具

runtime:
  language: python
  entry:
    - -m
    - example_tool

command:
  shell: powershell

parameters:
  - id: input
    label: 输入文件
    type: file
    required: true
    default: null
    description: 要处理的输入文件
    cli:
      flag: --input

  - id: verbose
    label: 详细输出
    type: boolean
    required: false
    default: false
    description: 是否启用详细输出
    cli:
      flag: --verbose
```

具体字段是否允许省略，还需要以 `models/manifest.py` 的 dataclass 定义为最终准则；本文重点规定当前 UI 和 CommandBuilder 已明确实现的行为。

---

# 3. `schema_version`

```yaml
schema_version: 1
```

表示 Manifest 协议版本。

当前协议版本：

```yaml
schema_version: 1
```

---

# 4. `metadata`

## 4.1 基本字段

```yaml
metadata:
  id: example-tool
  name: Example Tool
  version: 1.0.0
  description: 示例工具
```

### `id`

工具唯一标识。

建议：

- 使用稳定、唯一的字符串
- 使用小写英文、数字和 `-`
- 不要包含空格
- 不要因为显示名称变化而改变 `id`

示例：

```yaml
id: beancount-trans
```

### `name`

UI 中显示的工具名称。

```yaml
name: Beancount Trans
```

### `version`

工具版本。

```yaml
version: 1.2.0
```

### `description`

工具描述。

```yaml
description: 将银行账单转换为 Beancount 格式
```

---

# 5. `runtime`

`runtime` 描述命令的基础运行入口。

当前 CommandBuilder 会按以下顺序直接追加：

```text
runtime.language
runtime.entry[0]
runtime.entry[1]
...
```

例如：

```yaml
runtime:
  language: python
  entry:
    - -m
    - my_tool
```

生成命令的基础部分：

```text
python -m my_tool
```

另一个例子：

```yaml
runtime:
  language: python
  entry:
    - tools/main.py
```

生成：

```text
python tools/main.py
```

## 5.1 `language`

必需的运行时命令。

例如：

```yaml
language: python
```

或：

```yaml
language: node
```

CommandBuilder 不负责验证该程序是否存在。

它只是将字符串加入最终命令。

## 5.2 `entry`

必需的列表。

```yaml
entry:
  - -m
  - my_tool
```

或：

```yaml
entry:
  - tools/main.py
```

**注意：**

`entry` 中的每个元素都会作为独立命令部分加入。

因此不要把整条命令写成一个字符串：

错误：

```yaml
entry:
  - "-m my_tool"
```

正确：

```yaml
entry:
  - -m
  - my_tool
```

---

# 6. `command`

## 6.1 `shell`

用于决定最终命令字符串的 Shell 格式。

当前明确支持：

```yaml
command:
  shell: powershell
```

```yaml
command:
  shell: pwsh
```

```yaml
command:
  shell: cmd
```

除此之外，CommandBuilder 会按照 Unix-like Shell 的 POSIX 规则处理，例如：

```yaml
command:
  shell: bash
```

```yaml
command:
  shell: sh
```

```yaml
command:
  shell: zsh
```

```yaml
command:
  shell: fish
```

注意：当前实现对非 `powershell` / `pwsh` / `cmd` 的 Shell 统一使用 Python `shlex.join()`，因此它本质上是 POSIX 风格引用，而不是针对每一种 Shell 单独实现。

---

# 7. 参数类型

当前实现实际支持以下参数类型：

| type | UI 控件 | CLI 行为 | `choices` | 状态值 |
|---|---|---|---|---|
| `string` | 文本框 | `flag value` | 不需要 | `str` / `null` |
| `file` | 文本框 + 文件选择器 | `flag value` | 不需要 | `str` / `null` |
| `directory` | 文本框 + 目录选择器 | `flag value` | 不需要 | `str` / `null` |
| `dir` | 文本框 + 目录选择器 | `flag value` | 不需要 | `str` / `null` |
| `single` | 下拉框 | `flag value` | 需要 | `str` / `null` |
| `enum` | 下拉框 | `flag value` | 需要 | `str` / `null` |
| `multi` | 多选框 | 重复 `flag value` | 需要 | `list[str]` |
| `boolean` | Switch | 仅 True 时输出 flag | 不需要 | `bool` |
| `bool` | Switch | 仅 True 时输出 flag | 不需要 | `bool` |

**不要在 Manifest 中使用 `integer`、`float` 等当前实现没有支持的类型。**

---

# 8. 普通值类型

以下类型采用完全相同的 CLI 构建规则：

```text
string
file
directory
dir
single
enum
```

统一生成：

```text
flag value
```

例如：

```yaml
- id: input
  label: 输入文件
  type: file
  required: true
  default: null
  cli:
    flag: --input
```

用户选择：

```text
D:\Data\input.xlsx
```

内部参数部分为：

```text
--input
D:\Data\input.xlsx
```

最终输出时再根据 Shell 进行引用处理。

---

# 9. `string`

普通字符串输入。

```yaml
- id: output
  label: 输出文件
  type: string
  required: false
  default: output.txt
  description: 输出文件名
  cli:
    flag: --output
```

如果值为：

```text
result.txt
```

参数部分：

```text
--output result.txt
```

如果值包含空格或 Shell 特殊字符，最终命令会由 Shell 格式化阶段处理引用。

---

# 10. `file`

文件路径。

```yaml
- id: input
  label: 输入文件
  type: file
  required: true
  default: null
  description: 选择输入文件
  cli:
    flag: --input
```

UI 会提供文件选择器。

最终仍然按照：

```text
--input <路径>
```

构建。

---

# 11. `directory` / `dir`

目录路径。

两者是当前实现中的别名：

```yaml
type: directory
```

和：

```yaml
type: dir
```

行为完全相同。

推荐统一使用：

```yaml
type: directory
```

例如：

```yaml
- id: output_dir
  label: 输出目录
  type: directory
  required: true
  default: null
  cli:
    flag: --output-dir
```

---

# 12. `single` / `enum`

单选参数。

两者当前行为完全相同，都会使用下拉框。

必须提供 `choices`：

```yaml
- id: format
  label: 输出格式
  type: enum
  required: true
  default: json
  choices:
    - json
    - yaml
    - csv
  cli:
    flag: --format
```

选择：

```text
yaml
```

生成：

```text
--format yaml
```

## 12.1 `default`

默认值应该是 `choices` 中的一个值：

```yaml
default: json
choices:
  - json
  - yaml
  - csv
```

不要写：

```yaml
default: xml
choices:
  - json
  - yaml
  - csv
```

---

# 13. `multi`

多选参数。

必须提供 `choices`：

```yaml
- id: formats
  label: 输出格式
  type: multi
  required: false
  default: []
  choices:
    - json
    - yaml
    - csv
  cli:
    flag: --format
```

如果用户选择：

```yaml
- json
- csv
```

CommandBuilder 当前采用：

```text
--format json --format csv
```

即：

```text
flag value flag value
```

而不是：

```text
--format json,csv
```

也不是：

```text
--format json csv
```

## 13.1 推荐默认值

没有默认选择：

```yaml
default: []
```

有默认选择：

```yaml
default:
  - json
  - csv
```

---

# 14. `boolean` / `bool`

布尔开关。

两者行为完全相同。

推荐使用：

```yaml
type: boolean
```

例如：

```yaml
- id: verbose
  label: 详细输出
  type: boolean
  required: false
  default: false
  description: 启用详细日志
  cli:
    flag: --verbose
```

当值为：

```text
true
```

生成：

```text
--verbose
```

当值为：

```text
false
```

不生成任何参数。

**不会生成：**

```text
--verbose false
```

因此该类型对应的是典型 CLI switch。

---

# 15. `required`

```yaml
required: true
```

表示参数必须提供有效值。

当前行为：

## 普通值类型

以下值视为空：

```text
null
""
```

如果：

```yaml
required: true
```

则会抛出参数缺失错误。

## `multi`

以下情况会被视为没有有效选择：

```yaml
default: []
```

或最终选择为空。

如果 `required: true`，会抛出错误。

## boolean

`required` 对 Boolean 的命令生成没有相同意义：

```text
true  -> 输出 flag
false -> 不输出
```

当前 Boolean Builder 不会因为 `false` 而报 required 错误。

---

# 16. `default`

参数默认值。

命令构建时的取值优先级：

```text
ToolState
   ↓
Parameter.default
```

也就是说：

1. 如果 ToolState 中存在该参数，使用 ToolState。
2. 否则使用 Manifest 中的 `default`。

例如：

```yaml
default: json
```

如果用户尚未修改参数，则使用：

```text
json
```

---

# 17. `cli`

`cli` 用于声明参数如何映射到命令行。

## 17.1 `flag`

例如：

```yaml
cli:
  flag: --input
```

普通值参数生成：

```text
--input value
```

Boolean 参数生成：

```text
--verbose
```

Multi 参数生成：

```text
--format json --format yaml
```

## 17.2 `cli: null`

参数可以没有 CLI 映射：

```yaml
cli: null
```

这种参数仍然可以存在于 Manifest 和 UI 中，但 CommandBuilder 会直接跳过，不输出任何 CLI 参数。

因此：

```yaml
- id: internal_option
  label: 内部选项
  type: string
  default: something
  cli: null
```

不会出现在最终命令中。

---

# 18. 参数顺序

参数按照 Manifest 中 `parameters` 列表的顺序输出。

例如：

```yaml
parameters:
  - id: input
    ...
    cli:
      flag: --input

  - id: output
    ...
    cli:
      flag: --output

  - id: verbose
    ...
    cli:
      flag: --verbose
```

参数顺序为：

```text
--input ...
--output ...
--verbose
```

因此如果目标 CLI 对参数顺序有要求，应在 Manifest 中按照目标工具期望的顺序排列。

---

# 19. 一个完整示例

```yaml
schema_version: 1

metadata:
  id: example-converter
  name: Example Converter
  version: 1.0.0
  description: 示例文件转换工具

runtime:
  language: python
  entry:
    - -m
    - example_converter

command:
  shell: powershell

parameters:
  - id: input
    label: 输入文件
    type: file
    required: true
    default: null
    description: 选择需要转换的文件
    cli:
      flag: --input

  - id: output_dir
    label: 输出目录
    type: directory
    required: true
    default: null
    description: 选择输出目录
    cli:
      flag: --output-dir

  - id: format
    label: 输出格式
    type: enum
    required: true
    default: json
    description: 输出文件格式
    choices:
      - json
      - yaml
      - csv
    cli:
      flag: --format

  - id: features
    label: 启用功能
    type: multi
    required: false
    default: []
    description: 可同时启用多个功能
    choices:
      - metadata
      - thumbnail
      - compress
    cli:
      flag: --feature

  - id: verbose
    label: 详细日志
    type: boolean
    required: false
    default: false
    description: 输出详细日志
    cli:
      flag: --verbose
```

假设用户选择：

```text
input = D:\Data Files\input.xlsx
output_dir = D:\Output
format = json
features = [metadata, compress]
verbose = true
```

则参数的逻辑结构为：

```text
python
-m
example_converter
--input
D:\Data Files\input.xlsx
--output-dir
D:\Output
--format
json
--feature
metadata
--feature
compress
--verbose
```

PowerShell 格式化后，会根据参数中的空格、特殊字符等进行引用。

---

# 20. Shell 引用

命令构建不是简单字符串拼接。

CommandBuilder 首先构造：

```text
list[str]
```

然后根据 `command.shell` 进行最终格式化。

## PowerShell

以下 Shell 名称走 PowerShell 格式化：

```yaml
shell: powershell
```

```yaml
shell: pwsh
```

## CMD

```yaml
shell: cmd
```

## Unix-like

其他 Shell 当前统一采用 POSIX `shlex.join()`：

```yaml
shell: bash
```

```yaml
shell: sh
```

```yaml
shell: zsh
```

```yaml
shell: fish
```

因此 Manifest 作者**不应该自行给参数值添加引号**。

错误：

```yaml
default: '"D:\My Files\input.txt"'
```

正确：

```yaml
default: 'D:\My Files\input.txt'
```

引用由 CommandBuilder 负责。

---

# 21. 参数类型选择规则

生成 Manifest 时，优先按照下面规则选择：

| 工具参数语义 | Manifest type |
|---|---|
| 普通文本 | `string` |
| 文件路径 | `file` |
| 目录路径 | `directory` |
| 单选枚举 | `enum` |
| 多个可同时选择的选项 | `multi` |
| 开/关选项 | `boolean` |

兼容别名：

```text
dir       → directory
single    → enum
bool      → boolean
```

虽然当前实现支持别名，但新 Manifest 推荐使用：

```text
directory
enum
boolean
```

以减少协议中的同义类型。

---

# 22. 不要使用的类型

当前 CommandBuilder 明确没有实现：

```text
integer
float
number
list
object
```

因此不要根据工具本身的参数类型随意扩展 Manifest：

错误：

```yaml
type: integer
```

如果工具需要输入整数，当前协议应该使用：

```yaml
type: string
```

并由目标工具自身完成整数解析。

同理，浮点数也暂时使用：

```yaml
type: string
```

直到 CMDTools 增加专门的数值参数类型。

---

# 23. 给 AI 生成 Manifest 时的规则

当向 AI 提供一个工具说明并要求生成 `manifest.yml` 时，应遵循：

1. 先确定工具的运行命令。
2. 将命令拆分成 `runtime.language` 和 `runtime.entry`。
3. 每个可配置 CLI 参数转换为一个 `parameters` 项。
4. 普通文本使用 `string`。
5. 文件路径使用 `file`。
6. 目录路径使用 `directory`。
7. 单选使用 `enum` + `choices`。
8. 多选使用 `multi` + `choices`。
9. 开关使用 `boolean`。
10. 每个真正需要传给 CLI 的参数提供 `cli.flag`。
11. 不需要传给 CLI 的 UI 参数使用 `cli: null`。
12. `multi` 的 CLI 形式必须按照重复 flag 处理。
13. Boolean 为 true 时只输出 flag，不输出 `true`。
14. 不要自行给路径或字符串增加 Shell 引号。
15. 不要使用当前未支持的 `integer` / `float` 等类型。
16. 参数顺序按照目标工具命令的合理顺序排列。
17. `default` 必须与参数类型匹配。
18. `enum` / `single` 的默认值应属于 `choices`。
19. `multi` 的默认值应为列表。
20. 不确定某个 CLI 参数的具体语义时，不要猜测，应向用户询问。

---

# 24. 当前实现的重要边界

本协议描述的是 **当前 CMDTools 实际实现**，不是抽象的理想 CLI 协议。

尤其需要注意：

- ParameterPanel 决定参数如何在 GUI 中输入。
- CommandBuilder 决定参数如何转换为 CLI。
- 两者共同决定 `type` 的实际语义。
- `command.shell` 决定最终字符串的 Shell 引用方式。
- `required` 主要用于普通值和 multi 的缺失检查。
- `cli: null` 会使参数完全跳过 CLI 输出。
- `runtime.language` 与 `runtime.entry` 会直接构成命令前缀。
- 当前 CommandBuilder 不使用 `command.executable` 或 `command.workdir` 来构建输出命令；如果 Manifest 模型中仍存在这些字段，应将它们视为当前协议模型中的其他配置，而不要误认为它们会自动出现在生成的 CLI 字符串中。

---

# 25. 最小 Manifest

一个最小的可构建思路如下：

```yaml
schema_version: 1

metadata:
  id: hello
  name: Hello
  version: 1.0.0
  description: Hello World

runtime:
  language: python
  entry:
    - hello.py

command:
  shell: powershell

parameters: []
```

生成的基础命令：

```text
python hello.py
```

---

# 26. AI 输入模板

以后可以直接向 AI 提供：

```text
请根据下面的工具说明生成 CMDTools manifest.yml。

要求：
1. 严格遵循 CMDTools Manifest YAML 协议。
2. 只使用 string、file、directory、enum、multi、boolean 等当前支持的参数类型。
3. enum 必须提供 choices。
4. multi 必须提供 choices，CLI 使用重复 flag。
5. boolean 为 true 时只输出 flag。
6. 不要自行给参数值添加 Shell 引号。
7. 正确区分 runtime.language、runtime.entry、command.shell。
8. 如果工具说明无法确定某个 CLI 参数的行为，不要猜测，列出需要确认的问题。
9. 最终只输出完整 manifest.yml。

工具说明：

<在这里粘贴工具说明>
```

---

## 27. 当前协议的核心原则

> **Manifest 描述“工具是什么、有哪些参数、参数如何映射到 CLI”；CommandBuilder 负责把这些结构化信息转换成最终命令字符串。**

最重要的映射关系：

```text
string/file/directory
    ↓
--flag value

enum/single
    ↓
--flag value

multi
    ↓
--flag value --flag value ...

boolean
    ↓
--flag

cli: null
    ↓
不输出

ToolState
    ↓
覆盖 default

command.shell
    ↓
最终 Shell 引用
```

这套规则应作为后续生成 CMDTools `manifest.yml` 的标准协议。
