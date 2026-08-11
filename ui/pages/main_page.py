import flet as ft

from models.state import AppState
from services.manifest_parser_service import parse_manifests
from services.plugin_loader_service import discover_plugins
from services.state_service import StateService
from ui.components.project.info_panel import InfoPanel
from ui.components.project.output_panel import OutputPanel
from ui.components.project.parameter_panel import ParameterPanel
from ui.components.project.tool_panel import ToolPanel
from ui.components.stacked_notifications.stacked_notifications import (
    NotificationManager,
)


def build_main_page(page: ft.Page) -> None:
    """构建 CMD Tools 主页面。"""

    page.title = "CMD Tools"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    page.window.width = 1200
    page.window.height = 1000

    # ====================================================================
    # 加载插件
    # ====================================================================

    paths = discover_plugins()
    manifests = parse_manifests(paths)

    # ====================================================================
    # 创建应用状态
    # ====================================================================

    state = AppState(manifests)

    state_service = StateService()
    state_service.load(state)

    # ====================================================================
    # 创建通知管理器
    # ====================================================================

    ntf = NotificationManager(page)

    # ====================================================================
    # 创建页面组件
    # ====================================================================

    def on_tool_selected(tool_id: str):
        """处理工具切换。"""
        info_panel.refresh()
        para_panel.refresh()
        output_panel.refresh()

    tool_panel = ToolPanel(
        state,
        on_tool_selected=on_tool_selected,
    )
    info_panel = InfoPanel(state)
    para_panel = ParameterPanel(state, state_service)
    output_panel = OutputPanel(state, ntf)

    # ====================================================================
    # 页面布局
    # ====================================================================

    left_panel = ft.Container(
        content=tool_panel.build(),
        width=280,
        padding=5,
    )

    right_panel = ft.Column(
        controls=[
            ft.Container(
                content=info_panel.build(),
                # expand=True,
                padding=5,
                height=210,
            ),
            ft.Container(
                content=para_panel.build(),
                expand=True,
                padding=5,
            ),
            ft.Container(
                content=output_panel.build(),                
                # expand=True,
                padding=5,
                height=200,
            ),
        ],
        expand=True,
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    main_layout = ft.Row(
        controls=[
            left_panel,
            ft.VerticalDivider(width=1),
            right_panel,
        ],
        expand=True,
        spacing=5,
    )

    page.add(main_layout)
