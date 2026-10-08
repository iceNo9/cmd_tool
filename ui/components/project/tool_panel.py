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
        on_plugin_deleted=None,
        on_plugin_rescan=None,
    ):

        self.state = state
        self.on_tool_selected = on_tool_selected
        self.on_plugin_imported = on_plugin_imported
        self.on_plugin_exported = on_plugin_exported
        self.on_plugin_deleted = on_plugin_deleted
        self.on_plugin_rescan = on_plugin_rescan

        # 标题
        self.title = ft.Text(
            "工具列表",
            size=20,
            weight=ft.FontWeight.BOLD,
        )

        # 工具栏按钮
        self.rescan_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="重新扫描插件目录",
            on_click=self.on_rescan_click,
        )

        self.import_button = ft.IconButton(
            icon=ft.Icons.UPLOAD_FILE,
            tooltip="导入插件（manifest.yml）",
            on_click=self.on_import_click,
        )

        self.export_button = ft.IconButton(
            icon=ft.Icons.DOWNLOAD,
            tooltip="导出当前插件",
            on_click=self.on_export_click,
        )

        self.delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            tooltip="删除当前插件",
            on_click=self.on_delete_click,
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
                                    self.rescan_button,
                                    self.import_button,
                                    self.export_button,
                                    self.delete_button,
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
            border=ft.Border.all(1, ft.Colors.GREY_400),
            width=200,
            expand=True,
        )

        # 初始化插件列表
        self._rebuild_list()

    # ====================================================================
    # 构建 / 刷新
    # ====================================================================

    def build(self):
        return self.view

    def refresh(self):
        """刷新插件列表。"""
        self._rebuild_list()

        if self.list_view.page:
            self.list_view.update()

    def _rebuild_list(self):
        """重建插件列表内容。"""
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

            card = ToolCard(
                manifest.metadata,
                on_click=self.select_tool,
            )

            self.list_view.controls.append(card.build())

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

    # ====================================================================
    # 工具栏回调
    # ====================================================================

    def on_rescan_click(self, e):
        """手动重新扫描插件目录。"""
        logger.info("点击重新扫描按钮")

        if self.on_plugin_rescan:
            self.on_plugin_rescan()

    async def on_import_click(self, e):
        """打开插件导入文件选择器。

        插件形态为单个 manifest.yml，
        支持多选以一次导入多个插件。
        """
        logger.info("点击导入插件按钮")

        files = await ft.FilePicker().pick_files(
            dialog_title="选择插件 manifest.yml",
            allow_multiple=True,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["yml", "yaml"],
        )

        if not files:
            logger.debug("取消导入插件")
            return

        paths = [file.path for file in files if file.path]

        if not paths:
            logger.warning("选择的文件没有有效路径")
            return

        logger.info("选择插件文件: count=%d", len(paths))

        for path in paths:
            logger.debug("选择插件文件: %s", path)

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

    def on_delete_click(self, e):
        """删除当前选中的插件（带确认对话框）。"""
        logger.info("点击删除插件按钮")

        plugin_id = self.state.selected_tool_id

        if not plugin_id:
            logger.info("没有选择插件，无法删除")
            return

        manifest = self.state.get_selected_manifest()
        if manifest is None:
            logger.warning("选中的插件 Manifest 不存在: %s", plugin_id)
            return

        plugin_name = manifest.metadata.name
        plugin_version = manifest.metadata.version

        page = self.view.page

        # 容器引用，供闭包使用
        overlay_ref = {"container": None}

        def close_dialog(_=None):
            """关闭并移除对话框。"""
            container = overlay_ref["container"]
            if container is None:
                return

            if container in page.overlay:
                page.overlay.remove(container)

            overlay_ref["container"] = None
            page.update()

        def do_delete(_=None):
            """先关对话框，再执行删除。"""
            close_dialog()
            if self.on_plugin_deleted:
                self.on_plugin_deleted(plugin_id)

        # ---------------- 自绘对话框内容 ----------------

        dialog_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "确认删除插件",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(height=1),
                    ft.Text(
                        "此操作不可撤销，删除后需要重新导入才能恢复。",
                        color=ft.Colors.RED_400,
                    ),
                    ft.Text(f"名称：{plugin_name}"),
                    ft.Text(f"ID：{plugin_id}"),
                    ft.Text(f"版本：{plugin_version}"),
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                "取消",
                                on_click=close_dialog,
                            ),
                            ft.TextButton(
                                "删除",
                                on_click=do_delete,
                                style=ft.ButtonStyle(color=ft.Colors.RED),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                tight=True,
                spacing=10,
            ),
            bgcolor=ft.Colors.WHITE,
            padding=20,
            border_radius=8,
            width=420,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLACK_26,
            ),
        )

        # 全屏遮罩 + 居中容器
        overlay_container = ft.Container(
            content=dialog_card,
            alignment=ft.Alignment.CENTER,
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            # 吞掉点击，防止穿透到下层
            on_click=lambda e: None,
        )

        overlay_ref["container"] = overlay_container

        page.overlay.append(overlay_container)
        page.update()
        
    # ====================================================================
    # 列表回调
    # ====================================================================

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
