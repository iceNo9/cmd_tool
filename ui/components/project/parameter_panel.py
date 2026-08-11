import flet as ft

from models.app_state import AppState
from models.manifest import Parameter


class ParameterPanel:
    """CLI 参数输入面板。

    根据 Parameter.type 动态创建对应的输入控件。
    """

    def __init__(self, state: AppState):
        self.state = state

        self.file_picker = ft.FilePicker()

        self.list_view = ft.ListView(
            expand=True,
            spacing=10,
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

        self.set_parameters(self.state.get_selected_manifest().parameters)

    def build(self):
        return self.view

    def refresh(self):
        self.clear()
        manifest = self.state.get_selected_manifest()
        if manifest:
            self.set_parameters(manifest.parameters)

    def set_parameters(self, parameters: list[Parameter]):
        """根据参数定义重新构建参数面板。"""

        for parameter in parameters:
            control = self._build_parameter(parameter)

            if control is not None:
                self.list_view.controls.append(control)

    def clear(self):
        """清空参数面板。"""
        self.list_view.controls.clear()

    def _build_parameter(
        self,
        parameter: Parameter,
    ) -> ft.Control | None:
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
        field = ft.TextField(
            label=parameter.label,
            value=self._default_value(parameter),
            hint_text=parameter.description or None,
            expand=True,
        )

        return self._wrap_parameter(
            parameter,
            field,
        )

    # ---------------------------------------------------------
    # File
    # ---------------------------------------------------------

    def _build_file(self, parameter: Parameter) -> ft.Control:
        field = ft.TextField(
            label=parameter.label,
            value=self._default_value(parameter),
            hint_text=parameter.description or None,
            expand=True,
        )

        button = ft.IconButton(
            icon=ft.Icons.FILE_OPEN,
            tooltip="选择文件",
            on_click=lambda e: self._pick_file(
                field,
                parameter,
            ),
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
        field = ft.TextField(
            label=parameter.label,
            value=self._default_value(parameter),
            hint_text=parameter.description or None,
            expand=True,
        )

        button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="选择目录",
            on_click=lambda e: self._pick_directory(
                field,
                parameter,
            ),
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

    def _build_single_choice(
        self,
        parameter: Parameter,
    ) -> ft.Control:

        default = self._default_value(parameter)

        dropdown = ft.Dropdown(
            label=parameter.label,
            value=default if default in parameter.choices else None,
            options=[
                ft.DropdownOption(
                    key=choice,
                    text=choice,
                )
                for choice in parameter.choices
            ],
            expand=True,
        )

        return self._wrap_parameter(
            parameter,
            dropdown,
        )

    # ---------------------------------------------------------
    # Multi choice
    # ---------------------------------------------------------

    def _build_multi_choice(
        self,
        parameter: Parameter,
    ) -> ft.Control:

        default = parameter.default

        selected = set()

        if isinstance(default, list):
            selected.update(str(value) for value in default)

        checkboxes = []

        for choice in parameter.choices:
            checkbox = ft.Checkbox(
                label=choice,
                value=choice in selected,
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

    def _build_boolean(
        self,
        parameter: Parameter,
    ) -> ft.Control:

        value = bool(parameter.default)

        switch = ft.Switch(
            label=parameter.label,
            value=value,
        )

        return self._wrap_parameter(
            parameter,
            switch,
        )

    # ---------------------------------------------------------
    # File picker
    # ---------------------------------------------------------

    async def _pick_file(
        self,
        field: ft.TextField,
        parameter: Parameter,
    ):
        """打开文件选择器。"""

        file_type = ft.FilePickerFileType.ANY
        allowed_extensions = None

        if parameter.file_types:
            file_type = ft.FilePickerFileType.CUSTOM

            # Flet 的 allowed_extensions 使用扩展名本体，
            # 推荐传 ["txt", "py"]，而不是 [".txt", ".py"]
            allowed_extensions = [
                extension.lstrip(".")
                for extension in parameter.file_types
            ]

        files = await self.file_picker.pick_files(
            file_type=file_type,
            allow_multiple=False,
            allowed_extensions=allowed_extensions,
        )

        if not files:
            return

        selected_file = files[0]

        if selected_file.path:
            field.value = selected_file.path
            field.update()

    # ---------------------------------------------------------
    # Directory picker
    # ---------------------------------------------------------

    async def _pick_directory(
        self,
        field: ft.TextField,
        parameter: Parameter,
    ):
        """打开目录选择器。"""

        path = await self.file_picker.get_directory_path()

        if path:
            field.value = path
            field.update()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _wrap_parameter(
        self,
        parameter: Parameter,
        control: ft.Control,
    ) -> ft.Control:

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
    def _default_value(
        parameter: Parameter,
    ) -> str:
        if parameter.default is None:
            return ""

        return str(parameter.default)

    @staticmethod
    def _build_unsupported(
        parameter: Parameter,
    ) -> ft.Control:

        return ft.Text(
            f"暂不支持参数类型: {parameter.type}",
            color=ft.Colors.RED,
        )
