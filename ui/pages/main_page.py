# ui/pages/main_page.py

import flet as ft

from models.state import AppState, ToolState
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
from utils.log import get_logger
from utils.paths import get_log_dir

# 创建该模块专用的日志记录器
logger = get_logger(
    name="main_page",
    log_dir=get_log_dir() / "logs",
    fmt_type="detailed",
    console_level=20,  # INFO
    file_level=10,  # DEBUG
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

    def add_new_plugins(new_manifests: list):
        """增量添加新插件。"""
        
        for manifest in new_manifests:
            tool_id = manifest.metadata.id
            
            # 添加到状态
            if manifest not in state.manifests:
                state.manifests.append(manifest)
                logger.info(f"添加新插件: {tool_id}")
            
            # 初始化工具状态
            if tool_id not in state.tool_states:
                state.tool_states[tool_id] = ToolState(tool_id)
                logger.debug(f"初始化插件状态: {tool_id}")

    def remove_plugins(removed_ids: set):
        """增量移除插件。"""
        
        for tool_id in removed_ids:
            # 从清单中移除
            state.manifests = [
                m for m in state.manifests
                if m.metadata.id != tool_id
            ]
            
            # 移除工具状态
            if tool_id in state.tool_states:
                del state.tool_states[tool_id]
                logger.debug(f"移除插件状态: {tool_id}")
            
            # 如果当前选中的插件被移除，切换选择
            if state.selected_tool_id == tool_id:
                state.selected_tool_id = (
                    state.manifests[0].metadata.id
                    if state.manifests
                    else None
                )
                logger.info(f"选中插件已移除，切换到: {state.selected_tool_id}")

    def update_plugins(updated_manifests: list):
        """增量更新插件。"""
        
        for new_manifest in updated_manifests:
            tool_id = new_manifest.metadata.id
            
            # 替换旧清单
            for i, old_manifest in enumerate(state.manifests):
                if old_manifest.metadata.id == tool_id:
                    state.manifests[i] = new_manifest
                    logger.info(f"更新插件: {tool_id}")
                    break
            
            # 确保工具状态存在
            if tool_id not in state.tool_states:
                state.tool_states[tool_id] = ToolState(tool_id)

    def sync_plugins():
        """同步插件：只处理变更。"""
        
        # 重新发现插件
        paths = discover_plugins()
        new_manifests = parse_manifests(paths)
        
        # 构建 ID 映射
        old_map = {
            m.metadata.id: m
            for m in state.manifests
        }
        new_map = {
            m.metadata.id: m
            for m in new_manifests
        }
        
        old_ids = set(old_map.keys())
        new_ids = set(new_map.keys())
        
        # 找出变更
        added_ids = new_ids - old_ids
        removed_ids = old_ids - new_ids
        common_ids = old_ids & new_ids
        
        # 找出更新的插件（版本变化）
        updated_manifests = []
        for tool_id in common_ids:
            old_manifest = old_map[tool_id]
            new_manifest = new_map[tool_id]
            
            if old_manifest.metadata.version != new_manifest.metadata.version:
                updated_manifests.append(new_manifest)
                logger.info(
                    f"检测到插件更新: {tool_id} "
                    f"({old_manifest.metadata.version} -> "
                    f"{new_manifest.metadata.version})"
                )
        
        # 应用变更
        if added_ids:
            added_manifests = [
                new_map[tool_id] for tool_id in added_ids
            ]
            add_new_plugins(added_manifests)
            logger.info(f"添加插件: {len(added_ids)} 个")
        
        if removed_ids:
            remove_plugins(removed_ids)
            logger.info(f"移除插件: {len(removed_ids)} 个")
        
        if updated_manifests:
            update_plugins(updated_manifests)
            logger.info(f"更新插件: {len(updated_manifests)} 个")
        
        # 如果有任何变更，刷新 UI
        if added_ids or removed_ids or updated_manifests:
            tool_panel.refresh()
            
            # 只有选中的插件受影响时才刷新详情面板
            if (
                state.selected_tool_id in added_ids
                or state.selected_tool_id in updated_manifests
                or state.selected_tool_id in removed_ids
            ):
                info_panel.refresh()
                para_panel.refresh()
                output_panel.refresh()
            
            logger.info(
                f"插件同步完成: "
                f"添加 {len(added_ids)}, "
                f"移除 {len(removed_ids)}, "
                f"更新 {len(updated_manifests)}"
            )
        else:
            logger.debug("没有检测到插件变更")

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
        # 导入完成后增量同步插件
        # ------------------------------------------------------------

        if result.success_count > 0:
            sync_plugins()

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

        result = plugin_import_export_service.export_plugin(
            state.selected_tool_id,
            export_dir,
        )

        if result.success:
            ntf.show(
                f"插件导出成功：{result.message}",
                type="success",
            )
        else:
            ntf.show(
                f"插件导出失败：{result.message}",
                type="error",
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