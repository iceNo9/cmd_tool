import flet as ft

from models.manifest import Parameter
from models.state import AppState
from services.state_service import StateService
from utils.log import get_logger

# 创建该模块专用的日志记录器
logger = get_logger(
    name="parameter_panel",
    log_dir="logs",
    fmt_type="detailed",
    console_level=10,  # INFO
    file_level=10,  # DEBUG
)


class ParameterPanel:
    """CLI 参数输入面板。

    根据 Parameter.type 动态创建对应的输入控件。
    """

    def __init__(self, state: AppState, state_service: StateService):

        # app状态
        self.state = state

        # tool 状态
        self.parameter_controls: dict[str, ft.Control] = {}  # key: parameter.id

        # 服务
        self.state_service = state_service

        # 文件选择器
        self.file_picker = ft.FilePicker()

        self.list_view = ft.ListView(
            expand=True,
            spacing=1,
            padding=5,
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
                spacing=5,
            ),
            padding=5,
            margin=5,
            border=ft.Border.all(
                1,
                ft.Colors.GREY_400,
            ),
            border_radius=8,
            expand=True,
        )

        # 初始化参数面板
        manifest = self.state.get_selected_manifest()
        if manifest:
            self.set_parameters(manifest.parameters)

    def build(self):
        return self.view

    def refresh(self):
        """刷新参数面板"""
        self.clear()
        manifest = self.state.get_selected_manifest()
        if manifest:
            self.set_parameters(manifest.parameters)

    def set_parameters(self, parameters: list[Parameter]):
        """根据参数定义重新构建参数面板。"""
        for parameter in parameters:
            control = self._build_parameter(parameter)
            if control is not None:
                self.parameter_controls[parameter.id] = control
                self.list_view.controls.append(control)

        # 构建完成后从状态加载值
        self.load_from_state()

    def clear(self):
        """清空参数面板。"""
        self.list_view.controls.clear()
        self.parameter_controls.clear()

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
                control.value = str(value)
            elif isinstance(control, ft.Dropdown):
                control.value = (
                    value if value in [opt.key for opt in control.options] else None
                )
            elif isinstance(control, ft.Switch):
                control.value = bool(value)
            elif isinstance(control, ft.Column):
                # Multi choice - checkboxes
                selected_values = set(value) if isinstance(value, list) else set()
                for checkbox in control.controls:
                    if isinstance(checkbox, ft.Checkbox):
                        checkbox.value = checkbox.label in selected_values
            elif isinstance(control, ft.Row):
                # File/Directory - find TextField in row
                for child in control.controls:
                    if isinstance(child, ft.TextField):
                        child.value = str(value)
                        break
        tool_state.mark_clean()

    def _update_state(self, param_id: str, value: object):
        """更新 ToolState 中的参数值"""
        tool_state = self.state.get_current_state()
        if tool_state != None:
            tool_state.set(param_id, value)
            self.state_service.auto_save(self.state)
            logger.debug(f"参数值更新 id: {param_id} value: {value}")

    def _build_parameter(self, parameter: Parameter) -> ft.Control | None:
        """根据 Parameter.type 创建输入控件。"""
        builders = {
            "string": self._build_string,
            "file": self._build_file,
            "directory": self._build_directory,
            "dir": self._build_directory,
            "single": self._build_single_choice,
            "enum": self._build_single_choice,
            "multi": self._build_multi_choice,
            "boolean": self._build_boolean,
            "bool": self._build_boolean,
        }

        builder = builders.get(parameter.type)

        if builder is None:
            return self._build_unsupported(parameter)

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
                e.control.value,
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
                e.control.value,
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
                e.control.value,
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
                e.control.value,
            ),
        )

        return self._wrap_parameter(parameter, dropdown)

    # ---------------------------------------------------------
    # Multi choice
    # ---------------------------------------------------------

    def _build_multi_choice(self, parameter: Parameter) -> ft.Control:
        """构建多选参数控件。"""

        value = self._get_parameter_value(parameter)

        selected = set()

        if isinstance(value, list):
            selected.update(str(item) for item in value)

        checkboxes = []

        def on_checkbox_change(e: ft.Event[ft.Checkbox]):
            selected_values = [
                checkbox.label
                for checkbox in checkboxes
                if checkbox.value
            ]

            self._update_state(
                parameter.id,
                selected_values,
            )

        for choice in parameter.choices:
            checkbox = ft.Checkbox(
                label=choice,
                value=choice in selected,
                on_change=on_checkbox_change,
            )
            checkboxes.append(checkbox)

        return self._wrap_parameter(
            parameter,
            ft.Column(
                controls=checkboxes,
                spacing=2,
            ),
        )

    # ---------------------------------------------------------
    # Boolean
    # ---------------------------------------------------------

    def _build_boolean(self, parameter: Parameter) -> ft.Control:
        """构建布尔参数控件。"""

        value = self._get_parameter_value(parameter)

        switch = ft.Switch(
            label=parameter.label,
            value=bool(value),
            on_change=lambda e: self._update_state(
                parameter.id,
                e.control.value,
            ),
        )

        return self._wrap_parameter(parameter, switch)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _wrap_parameter(self, parameter: Parameter, control: ft.Control) -> ft.Control:
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