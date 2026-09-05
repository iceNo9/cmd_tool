# ui/pages/main_page.py

import flet as ft

from models.state import AppState
from services.command_builder_service import CommandBuilderService
from services.manifest_parser_service import parse_manifests
from services.plugin_import_export_service import (
    PluginImportExportService,
)
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

    command_builder = CommandBuilderService()

    # ====================================================================
    # 创建插件导入导出服务
    # ====================================================================

    plugin_import_export_service = PluginImportExportService()

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

    def reload_plugins():
        """重新加载插件列表。"""

        paths = discover_plugins()
        manifests = parse_manifests(paths)

        state.manifests = manifests

        tool_panel.refresh()

    def on_plugin_imported(paths: list[str]):
        """处理插件导入。"""

        if not paths:
            return

        # ------------------------------------------------------------
        # 调用后端插件导入服务
        # ------------------------------------------------------------

        result = plugin_import_export_service.import_plugins(
            paths
        )

        # ------------------------------------------------------------
        # 导入完成后重新加载插件
        # ------------------------------------------------------------

        if result.success_count > 0:
            reload_plugins()

        # ------------------------------------------------------------
        # 显示导入结果
        # ------------------------------------------------------------

        if result.total_count == 1:
            item = result.results[0]

            if item.success:
                ntf.show(
                    f"导入成功：{item.message}",
                    type="success",
                )
            else:
                ntf.show(
                    f"导入失败：{item.message}",
                    type="error",
                )

        else:
            if result.has_failures:
                ntf.show(
                    f"插件导入完成："
                    f"成功 {result.success_count} 个，"
                    f"失败 {result.failed_count} 个",
                    type="warning",
                )
            else:
                ntf.show(
                    f"插件导入成功："
                    f"{result.success_count} 个",
                    type="success",
                )

    def on_plugin_exported(export_dir: str):
        """处理插件导出。"""

        if not state.selected_tool_id:
            return

        plugin_import_export_service.export_plugin(
            state.selected_tool_id,
            export_dir,
        )

    # 工具选择面板
    tool_panel = ToolPanel(
        state,
        on_tool_selected=on_tool_selected,
        on_plugin_imported=on_plugin_imported,
        on_plugin_exported=on_plugin_exported,
    )

    # 工具信息面板
    info_panel = InfoPanel(state)

    def on_parameter_changed():
        """参数发生变化后重新生成命令。"""

        manifest = state.get_selected_manifest()
        tool_state = state.get_current_state()

        if manifest is None or tool_state is None:
            output_panel.set_text("")
            return

        try:
            command = command_builder.build(
                manifest,
                tool_state,
            )

            output_panel.set_text(command)

        except ValueError as e:
            # 当前参数还没满足 required 条件时，
            # 暂时不生成命令。
            output_panel.set_text(
                f"参数错误: {e}"
            )

    # 工具参数详细面板
    para_panel = ParameterPanel(
        state,
        state_service,
        on_command_changed=on_parameter_changed,
    )

    # 命令输出面板
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
                padding=5,
                height=200,
            ),
        ],
        expand=True,
        spacing=1,
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