# ui/components/info_panel.py


import flet as ft

from models.app_state import AppState


class InfoPanel:

    def __init__(
        self,
        state: AppState,
    ):

        self.state = state
        

        self.title = ft.Text(
            value=f"工具名称: {self.state.selected_tool.name}",
            size=20,
            weight=ft.FontWeight.BOLD,
            max_lines=1,
        )

        self.tool_id = ft.Text(
            value=f"工具ID: {self.state.selected_tool.id}",
            size=20,
            weight=ft.FontWeight.BOLD,
            max_lines=1,
        )

        self.tool_version = ft.Text(
            value=f"工具版本: {self.state.selected_tool.version}",
            size=20,
            weight=ft.FontWeight.BOLD,
            max_lines=1,
        )

        self.tool_description = ft.Text(
            value=f"工具描述: {self.state.selected_tool.description}",
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
            ),
            padding=5,
            margin=5,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            # width=200,
            height=200,
            # expand=True,
        )

    def build(self):
        return self.view
