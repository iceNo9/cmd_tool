# ui/components/tool_panel.py


import flet as ft

from models.state import AppState
from ui.components.project.tool_card import ToolCard
from utils.log import get_logger

# 创建该模块专用的日志记录器
logger = get_logger(
    name="tool_panel",
    log_dir="logs",
    fmt_type="detailed",
    console_level=20,  # INFO
    file_level=10,  # DEBUG
)


class ToolPanel:

    def __init__(
        self,
        state: AppState,
        on_tool_selected=None,
    ):

        self.state = state
        self.on_tool_selected = on_tool_selected

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
        for manifest in self.state.manifests:

            if keyword:

                text = (
                    manifest.metadata.name + manifest.metadata.description
                    if manifest.metadata.description
                    else manifest.metadata.name
                )

                if keyword not in text.lower():
                    continue

            card = ToolCard(manifest.metadata, on_click=self.select_tool)

            self.list_view.controls.append(card.build())

    def build(self):
        return self.view

    def refresh(self):

        self.list_view.controls.clear()

        keyword = self.state.tool_search.lower()
        for manifest in self.state.manifests:

            if keyword:

                text = (
                    manifest.metadata.name + manifest.metadata.description
                    if manifest.metadata.description
                    else manifest.metadata.name
                )

                if keyword not in text.lower():
                    continue

            card = ToolCard(manifest.metadata, on_click=self.select_tool)

            self.list_view.controls.append(card.build())

        self.list_view.update()

    def on_search(self, e):

        self.state.set_search(e.control.value)

        self.refresh()

    def select_tool(self, metadata):
        """选择工具并通知页面刷新。"""

        tool_id = metadata.id

        if self.state.selected_tool_id == tool_id:
            return

        self.state.select_tool(tool_id)

        logger.debug(
            "选择工具: tool_id=%s, name=%s",
            tool_id,
            metadata.name,
        )

        if self.on_tool_selected:
            self.on_tool_selected(tool_id)