# ui/components/tool_panel.py


import flet as ft

from models.app_state import AppState
from ui.components.project.tool_card import ToolCard


class ToolPanel:

    def __init__(
        self,
        state: AppState,
    ):

        self.state = state

        self.title = ft.Text("工具列表", size=20, weight=ft.FontWeight.BOLD)

        self.search_box = ft.TextField(
            hint_text="搜索插件",
            on_change=self.on_search,
        )

        self.list_view = ft.ListView(
            expand=True,
            spacing=1,
        )

        self.view = ft.Container(
            content=ft.Column(
                controls=[
                    self.title,
                    self.search_box,
                    self.list_view,
                ],
                expand=True,
            ),
            padding=5,
            margin=5,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            width=200,
            expand=True,
        )

        keyword = self.state.tool_search.lower()
        for tool in self.state.tools:

            if keyword:

                text = tool.name + tool.description if tool.description else tool.name

                if keyword not in text.lower():
                    continue

            card = ToolCard(tool, on_click=self.select_tool)

            self.list_view.controls.append(card.build())

    def build(self):
        return self.view

    def refresh(self):

        self.list_view.controls.clear()

        keyword = self.state.tool_search.lower()

        for tool in self.state.tools:

            if keyword:

                text = tool.name + tool.description if tool.description else tool.name

                if keyword not in text.lower():
                    continue

            card = ToolCard(tool, on_click=self.select_tool)

            self.list_view.controls.append(card.build())

        self.list_view.update()

    def on_search(self, e):

        self.state.set_search(e.control.value)

        self.refresh()

    def select_tool(self, metadata):

        self.state.select_tool(metadata)

        print("选择:", metadata.name)
