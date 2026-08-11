import flet as ft

from models.manifest import Parameter
from models.state import AppState
from services.state_service import StateService
from utils.log import get_logger
from utils.paths import get_log_dir

# 创建该模块专用的日志记录器
logger = get_logger(
    name="parameter_panel",
    log_dir=get_log_dir() / "logs",
    fmt_type="detailed",
    console_level=10,  # INFO
    file_level=10,  # DEBUG
)


class ParameterPanel:
    """CLI 参数输入面板。

    根据 Parameter.type 动态创建对应的输入控件。
    """

    # 默认空值显示
    _EMPTY_DISPLAY = ""
    # 支持的类型映射
    _TYPE_MAPPING = {
        "string": "_build_string",
        "file": "_build_file",
        "directory": "_build_directory",
        "dir": "_build_directory",
        "single": "_build_single_choice",
        "enum": "_build_single_choice",
        "multi": "_build_multi_choice",
        "boolean": "_build_boolean",
        "bool": "_build_boolean",
    }

    def __init__(
        self, state: AppState, state_service: StateService, on_command_changed=None
    ):
        # app状态
        self.state = state

        # tool 状态
        self.parameter_controls: dict[str, ft.Control] = {}  # key: parameter.id

        # 服务
        self.state_service = state_service

        # 命令更新回调
        self.on_command_changed = on_command_changed

        # 文件选择器
        self.file_picker = ft.FilePicker()

        # 分组容器（用于布尔和多项选择的分组显示）
        self._group_containers = {
            "boolean": [],  # 存储所有布尔控件，用于统一包装
        }

        self.list_view = ft.ListView(
            expand=True,
            spacing=1,
            padding=1,
        )

        self.view = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "参数",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(height=1),
                    self.list_view,
                ],
                expand=True,
                spacing=1,
            ),
            padding=1,
            margin=1,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            expand=True,
        )

        # 初始化参数面板
        manifest = self.state.get_selected_manifest()
        if manifest and manifest.parameters:
            self.set_parameters(manifest.parameters)

    def build(self):
        return self.view

    def refresh(self):
        """刷新参数面板"""
        self.clear()
        manifest = self.state.get_selected_manifest()
        if manifest and manifest.parameters:
            self.set_parameters(manifest.parameters)

    def set_parameters(self, parameters: list[Parameter]):
        """根据参数定义重新构建参数面板。"""
        # 重置分组容器
        self._group_containers = {
            "boolean": [],
        }

        for parameter in parameters:
            control = self._build_parameter(parameter)
            if control is not None:
                self.parameter_controls[parameter.id] = control
                # 对于布尔，暂存到分组列表
                if parameter.type in ["boolean", "bool"]:
                    self._group_containers["boolean"].append(control)
                else:
                    # 多选和其他类型直接添加到列表
                    self.list_view.controls.append(control)

        # 添加布尔分组控件
        self._add_grouped_controls()

        # 构建完成后从状态加载值
        self.load_from_state()

    def _add_grouped_controls(self):
        """添加分组后的控件（只有布尔）。"""
        # 处理布尔控件分组
        if self._group_containers["boolean"]:
            # 提取所有开关的标签和控件
            switches = []
            for container in self._group_containers["boolean"]:
                # 从容器中提取 Switch 控件
                if isinstance(container.content, ft.Column):
                    for child in container.content.controls:
                        if isinstance(child, ft.Switch):
                            switches.append(child)

            if switches:
                # 创建开关组容器
                switch_group = self._create_switch_group(switches)
                self.list_view.controls.append(switch_group)

    def _create_switch_group(self, switches: list[ft.Switch]) -> ft.Container:
        """创建开关组容器。"""
        # 为每个开关添加标签
        switch_row = ft.Row(
            controls=switches,
            wrap=True,  # 自动换行
            spacing=20,
            run_spacing=10,
            expand=True,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "开关选项",
                        weight=ft.FontWeight.BOLD,
                        size=14,
                    ),
                    ft.Divider(height=1),
                    switch_row,
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            margin=ft.Margin(0, 5, 0, 5),
        )

    def clear(self):
        """清空参数面板。"""
        self.list_view.controls.clear()
        self.parameter_controls.clear()
        self._group_containers = {
            "boolean": [],
        }

    def load_from_state(self):
        """从 ToolState 加载参数值到控件"""
        tool_state = self.state.get_current_state()
        if not tool_state:
            return

        for param_id, control in self.parameter_controls.items():
            value = tool_state.get(param_id)
            if value is None:
                continue

            # 根据控件类型设置值
            if isinstance(control, ft.TextField):
                control.value = str(value) if value is not None else self._EMPTY_DISPLAY
            elif isinstance(control, ft.Dropdown):
                control.value = (
                    value if value in [opt.key for opt in control.options] else None
                )
            elif isinstance(control, ft.Switch):
                control.value = bool(value)
            elif isinstance(control, ft.Container):
                # 多选 - 在 Container 中查找 Checkbox
                self._load_multi_choice_value(control, value)
            elif isinstance(control, ft.Row):
                # 文件/目录 - 在 Row 中查找 TextField
                for child in control.controls:
                    if isinstance(child, ft.TextField):
                        child.value = str(value) if value is not None else self._EMPTY_DISPLAY
                        break
        tool_state.mark_clean()

    def _load_multi_choice_value(self, container: ft.Container, value):
        """加载多选参数值。"""
        selected_values = set(value) if isinstance(value, list) else set()
        
        # 遍历 Container 的内容
        if isinstance(container.content, ft.Column):
            for child in container.content.controls:
                if isinstance(child, ft.Row):
                    # 在 Row 中查找 Checkbox
                    for checkbox in child.controls:
                        if isinstance(checkbox, ft.Checkbox):
                            checkbox.value = checkbox.label in selected_values
                elif isinstance(child, ft.Checkbox):
                    # 直接是 Checkbox
                    child.value = child.label in selected_values

    def _update_state(self, param_id: str, value: object):
        """更新 ToolState，并触发状态保存和命令更新。"""
        tool_state = self.state.get_current_state()
        if tool_state is None:
            return

        # 1. 更新 ToolState
        tool_state.set(param_id, value)

        logger.debug(
            "参数值更新: id=%s value=%r",
            param_id,
            value,
        )

        # 2. 自动保存状态
        self.state_service.auto_save(self.state)

        # 3. 通知外部重新生成命令
        if self.on_command_changed is not None:
            self.on_command_changed()

    def _build_parameter(self, parameter: Parameter) -> ft.Control | None:
        """根据 Parameter.type 创建输入控件。"""
        builder_name = self._TYPE_MAPPING.get(parameter.type)
        if builder_name is None:
            return self._build_unsupported(parameter)

        builder = getattr(self, builder_name)
        return builder(parameter)

    # ---------------------------------------------------------
    # String
    # ---------------------------------------------------------

    def _build_string(self, parameter: Parameter) -> ft.Control:
        """构建字符串参数控件。"""
        value = self._get_parameter_value(parameter)

        field = ft.TextField(
            label=parameter.label,
            value="" if value is None else str(value),
            hint_text=parameter.description or None,
            expand=True,
            on_blur=lambda e: self._update_state(
                parameter.id,
                e.control.value if e.control.value else None,
            ),
        )

        return self._wrap_parameter(parameter, field)

    # ---------------------------------------------------------
    # File
    # ---------------------------------------------------------

    def _build_file(self, parameter: Parameter) -> ft.Control:
        """构建文件参数控件。"""
        value = self._get_parameter_value(parameter)

        field = ft.TextField(
            label=parameter.label,
            value="" if value is None else str(value),
            hint_text=parameter.description or None,
            expand=True,
            on_change=lambda e: self._update_state(
                parameter.id,
                e.control.value if e.control.value else None,
            ),
        )

        async def handle_pick_files(e: ft.Event[ft.IconButton]):
            files = await self.file_picker.pick_files(
                allow_multiple=False,
            )

            if files:
                value = files[0].path
                field.value = value
                self._update_state(parameter.id, value)

        button = ft.IconButton(
            icon=ft.Icons.FILE_OPEN,
            tooltip="选择文件",
            on_click=handle_pick_files,
        )

        return self._wrap_parameter(
            parameter,
            ft.Row(
                controls=[
                    field,
                    button,
                ],
                spacing=5,
            ),
        )

    # ---------------------------------------------------------
    # Directory
    # ---------------------------------------------------------

    def _build_directory(self, parameter: Parameter) -> ft.Control:
        """构建目录参数控件。"""
        value = self._get_parameter_value(parameter)

        field = ft.TextField(
            label=parameter.label,
            value="" if value is None else str(value),
            hint_text=parameter.description or None,
            expand=True,
            on_change=lambda e: self._update_state(
                parameter.id,
                e.control.value if e.control.value else None,
            ),
        )

        async def handle_get_directory_path(e: ft.Event[ft.IconButton]):
            directory = await self.file_picker.get_directory_path()

            if directory:
                field.value = directory
                self._update_state(parameter.id, directory)

        button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="选择目录",
            on_click=handle_get_directory_path,
        )

        return self._wrap_parameter(
            parameter,
            ft.Row(
                controls=[
                    field,
                    button,
                ],
                spacing=5,
            ),
        )

    # ---------------------------------------------------------
    # Single choice
    # ---------------------------------------------------------

    def _build_single_choice(self, parameter: Parameter) -> ft.Control:
        """构建单选参数控件。"""
        value = self._get_parameter_value(parameter)

        dropdown = ft.Dropdown(
            label=parameter.label,
            value=value if value in parameter.choices else None,
            options=[
                ft.DropdownOption(
                    key=choice,
                    text=choice,
                )
                for choice in parameter.choices
            ],
            expand=True,
            on_text_change=lambda e: self._update_state(
                parameter.id,
                e.control.value if e.control.value else None,
            ),
        )

        return self._wrap_parameter(parameter, dropdown)

    # ---------------------------------------------------------
    # Multi choice
    # ---------------------------------------------------------

    def _build_multi_choice(self, parameter: Parameter) -> ft.Control:
        """构建多选参数控件 - 每个多选独立成组，选项水平排列。"""
        value = self._get_parameter_value(parameter)

        selected = set()
        if isinstance(value, list):
            selected.update(str(item) for item in value)

        checkboxes = []

        def on_checkbox_change(e: ft.Event[ft.Checkbox]):
            # 获取同一组所有复选框的值
            parent = e.control.parent
            if parent and isinstance(parent, ft.Row):
                selected_values = [
                    checkbox.label for checkbox in parent.controls 
                    if isinstance(checkbox, ft.Checkbox) and checkbox.value
                ]
                self._update_state(parameter.id, selected_values)

        for choice in parameter.choices:
            checkbox = ft.Checkbox(
                label=choice,
                value=choice in selected,
                on_change=on_checkbox_change,
            )
            checkboxes.append(checkbox)

        # 选项水平排列，自动换行
        checkbox_row = ft.Row(
            controls=checkboxes,
            wrap=True,
            spacing=15,
            run_spacing=8,
            expand=True,
        )

        # 显示参数信息
        title = ft.Text(
            f"{parameter.label} *" if parameter.required else parameter.label,
            weight=ft.FontWeight.BOLD,
            size=14,
        )

        controls = [title]
        if parameter.description:
            controls.append(ft.Text(
                parameter.description,
                size=12,
                color=ft.Colors.GREY_600,
            ))
        controls.append(ft.Divider(height=1))
        controls.append(checkbox_row)

        return ft.Container(
            content=ft.Column(
                controls=controls,
                spacing=5,
            ),
            padding=10,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            margin=ft.Margin(0, 5, 0, 5),
        )

    # ---------------------------------------------------------
    # Boolean
    # ---------------------------------------------------------

    def _build_boolean(self, parameter: Parameter) -> ft.Control:
        """构建布尔参数控件。"""
        value = self._get_parameter_value(parameter)

        switch = ft.Switch(
            label=parameter.label,
            value=bool(value) if value is not None else False,
            on_change=lambda e: self._update_state(
                parameter.id,
                e.control.value,
            ),
        )

        # 返回包含开关的容器，稍后会被统一分组
        return ft.Container(
            content=ft.Column(
                controls=[switch],
                spacing=2,
            ),
            data={"type": "boolean", "label": parameter.label},
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _wrap_parameter(self, parameter: Parameter, control: ft.Control) -> ft.Control:
        """包装单个参数控件（非分组类型）。"""
        if parameter.required:
            title = ft.Text(
                f"{parameter.label} *",
                weight=ft.FontWeight.BOLD,
            )
        else:
            title = ft.Text(
                parameter.label,
                weight=ft.FontWeight.BOLD,
            )

        controls = [title]

        if parameter.description:
            controls.append(
                ft.Text(
                    parameter.description,
                    size=12,
                    color=ft.Colors.GREY_600,
                )
            )

        controls.append(control)

        return ft.Container(
            content=ft.Column(
                controls=controls,
                spacing=4,
            ),
            padding=5,
            margin=ft.Margin(0, 2, 0, 2),
        )

    @staticmethod
    def _default_value(parameter: Parameter) -> str:
        if parameter.default is None:
            return ""
        return str(parameter.default)

    @staticmethod
    def _build_unsupported(parameter: Parameter) -> ft.Control:
        return ft.Text(
            f"暂不支持参数类型: {parameter.type}",
            color=ft.Colors.RED,
        )

    def _get_parameter_value(self, parameter: Parameter) -> object:
        """
        获取参数初始值。

        优先使用当前 ToolState 中已经存在的值；
        如果不存在，则使用 Parameter.default。
        """
        tool_state = self.state.get_current_state()

        if tool_state is not None and tool_state.has(parameter.id):
            value = tool_state.get(parameter.id)

            logger.debug(
                "使用 ToolState 参数值: id=%s value=%r",
                parameter.id,
                value,
            )

            return value

        logger.debug(
            "ToolState 中不存在参数，使用默认值: id=%s default=%r",
            parameter.id,
            parameter.default,
        )

        return parameter.default