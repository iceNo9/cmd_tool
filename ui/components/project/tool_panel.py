# ui/components/tool_panel.py

import flet as ft

from models.state import AppState
from ui.components.project.tool_card import ToolCard
from utils.log import get_logger
from utils.paths import get_log_dir

# 创建该模块专用的日志记录器
logger = get_logger(
    name="tool_panel",
    log_dir=get_log_dir() / "logs",
    fmt_type="detailed",
    console_level=20,  # INFO
    file_level=10,  # DEBUG
)


class ToolPanel:

    def __init__(
        self,
        state: AppState,
        on_tool_selected=None,
        on_plugin_imported=None,
        on_plugin_exported=None,
    ):

        self.state = state
        self.on_tool_selected = on_tool_selected
        self.on_plugin_imported = on_plugin_imported
        self.on_plugin_exported = on_plugin_exported

        # 标题
        self.title = ft.Text(
            "工具列表",
            size=20,
            weight=ft.FontWeight.BOLD,
        )

        # 导入 / 导出按钮
        self.import_button = ft.IconButton(
            icon=ft.Icons.UPLOAD_FILE,
            tooltip="导入插件",
            on_click=self.on_import_click,
        )

        self.export_button = ft.IconButton(
            icon=ft.Icons.DOWNLOAD,
            tooltip="导出插件",
            on_click=self.on_export_click,
        )

        # 搜索框
        self.search_box = ft.TextField(
            hint_text="搜索插件",
            on_change=self.on_search,
        )

        # 插件列表
        self.list_view = ft.ListView(
            expand=True,
            spacing=1,
        )

        # 页面
        self.view = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.title,
                            ft.Row(
                                controls=[
                                    self.import_button,
                                    self.export_button,
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.search_box,
                    self.list_view,
                ],
                expand=True,
            ),
            padding=5,
            margin=5,
            border=ft.Border.all(
                1,
                ft.Colors.GREY_400,
            ),
            width=200,
            expand=True,
        )

        # 初始化插件列表
        keyword = self.state.tool_search.lower()

        for manifest in self.state.manifests:

            if keyword:
                text = (
                    manifest.metadata.name
                    + manifest.metadata.description
                    if manifest.metadata.description
                    else manifest.metadata.name
                )

                if keyword not in text.lower():
                    continue

            card = ToolCard(
                manifest.metadata,
                on_click=self.select_tool,
            )

            self.list_view.controls.append(
                card.build()
            )

        # 没有任何工具时显示提示
        if not self.list_view.controls:

            if self.state.manifests:
                message = "没有找到匹配的插件"
            else:
                message = "暂无可用插件"

            self.list_view.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.EXTENSION_OFF,
                                size=32,
                            ),
                            ft.Text(
                                message,
                                size=14,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=20,
                )
            )

    def build(self):
        return self.view

    def refresh(self):
        """刷新插件列表。"""

        self.list_view.controls.clear()

        keyword = self.state.tool_search.lower()

        for manifest in self.state.manifests:

            if keyword:
                text = (
                    manifest.metadata.name
                    + manifest.metadata.description
                    if manifest.metadata.description
                    else manifest.metadata.name
                )

                if keyword not in text.lower():
                    continue

            card = ToolCard(
                manifest.metadata,
                on_click=self.select_tool,
            )

            self.list_view.controls.append(
                card.build()
            )

        # 没有任何工具时显示提示
        if not self.list_view.controls:

            if self.state.manifests:
                message = "没有找到匹配的插件"
            else:
                message = "暂无可用插件"

            self.list_view.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.EXTENSION_OFF,
                                size=32,
                            ),
                            ft.Text(
                                message,
                                size=14,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=20,
                )
            )

        # 只有已经加入页面后才能 update
        if self.list_view.page:
            self.list_view.update()

    async def on_import_click(self, e):
        """打开插件导入文件选择器。"""

        logger.info("点击导入插件按钮")

        files = await ft.FilePicker().pick_files(
            dialog_title="选择插件 manifest.yml",
            allow_multiple=True,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[
                "yml",
                "yaml",
            ],
        )

        if not files:
            logger.debug("取消导入插件")
            return

        paths = [
            file.path
            for file in files
            if file.path
        ]

        if not paths:
            logger.warning("选择的文件没有有效路径")
            return

        logger.info(
            "选择插件文件: count=%d",
            len(paths),
        )

        for path in paths:
            logger.debug(
                "选择插件文件: %s",
                path,
            )

        # 通知 main_page
        if self.on_plugin_imported:
            self.on_plugin_imported(paths)

    async def on_export_click(self, e):
        """打开插件导出目录选择器。"""

        logger.info("点击导出插件按钮")

        if not self.state.selected_tool_id:
            logger.info("没有选择插件，无法导出")
            return

        export_dir = await ft.FilePicker().get_directory_path(
            dialog_title="选择插件导出目录",
        )

        if not export_dir:
            logger.debug("取消导出插件")
            return

        logger.info(
            "选择插件导出目录: plugin_id=%s, path=%s",
            self.state.selected_tool_id,
            export_dir,
        )

        if self.on_plugin_exported:
            self.on_plugin_exported(export_dir)

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