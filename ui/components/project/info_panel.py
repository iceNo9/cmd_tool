# ui/components/info_panel.py


import flet as ft

from models.state import AppState


class InfoPanel:

    def __init__(
        self,
        state: AppState,
    ):

        self.state = state

        self.title = ft.Text(
            value=f"工具名称: {self.state.get_selected_manifest().metadata.name}",
            size=20,
            weight=ft.FontWeight.BOLD,
            max_lines=1,
        )

        self.tool_id = ft.Text(
            value=f"工具ID: {self.state.get_selected_manifest().metadata.id}",
            size=20,
            weight=ft.FontWeight.BOLD,
            max_lines=1,
        )

        self.tool_version = ft.Text(
            value=f"工具版本: {self.state.get_selected_manifest().metadata.version}",
            size=20,
            weight=ft.FontWeight.BOLD,
            max_lines=1,
        )

        self.tool_description = ft.Text(
            value=f"工具描述: {self.state.get_selected_manifest().metadata.description}",
            size=20,
            weight=ft.FontWeight.BOLD,
        )

        self.view = ft.Container(
            content=ft.Column(
                controls=[
                    self.title,
                    self.tool_id,
                    self.tool_version,
                    self.tool_description,
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=1,
            ),
            padding=5,
            margin=5,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            width=2000,
            height=110,
            expand=True,
        )

    def build(self):
        return self.view

    def refresh(self):
        """根据当前选中的工具刷新信息。"""

        manifest = self.state.get_selected_manifest()

        if manifest is None:
            self.title.value = "工具名称: -"
            self.tool_id.value = "工具ID: -"
            self.tool_version.value = "工具版本: -"
            self.tool_description.value = "工具描述: -"
            return

        metadata = manifest.metadata

        self.title.value = f"工具名称: {metadata.name}"
        self.tool_id.value = f"工具ID: {metadata.id}"
        self.tool_version.value = f"工具版本: {metadata.version}"
        self.tool_description.value = f"工具描述: {metadata.description}"
