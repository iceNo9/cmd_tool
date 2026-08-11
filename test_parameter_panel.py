# ui/pages/main_page.py

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


def main(page: ft.Page):
    """CMD Tools 主页面。"""

    page.title = "CMD Tools"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10

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

    tool_panel = ToolPanel(state)
    info_panel = InfoPanel(state)
    para_panel = ParameterPanel(state, state_service)
    output_panel = OutputPanel(state, ntf)

    # ====================================================================
    # 页面布局
    #
    # ┌──────────────────┬────────────────────────────────────┐
    # │                  │ InfoPanel                           │
    # │                  ├────────────────────────────────────┤
    # │    ToolPanel     │ ParameterPanel                     │
    # │                  │                                    │
    # │                  ├────────────────────────────────────┤
    # │                  │ OutputPanel                        │
    # │                  │                                    │
    # └──────────────────┴────────────────────────────────────┘
    # ====================================================================

    # 左侧：工具列表
    left_panel = ft.Container(
        content=tool_panel.build(),
        width=280,
        padding=5,
    )

    # 右侧：信息、参数、输出
    right_panel = ft.Column(
        controls=[
            # 工具信息
            ft.Container(
                content=info_panel.build(),
                padding=5,
            ),

            # 参数面板
            ft.Container(
                content=para_panel.build(),
                expand=True,
                padding=5,
            ),

            # 输出面板
            ft.Container(
                content=output_panel.build(),
                padding=5,
            ),
        ],
        expand=True,
        spacing=5,
    )

    # ====================================================================
    # 主布局
    # ====================================================================

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


if __name__ == "__main__":
    ft.app(target=main)
