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


def _manifest_signature(manifest) -> str:
    """manifest 内容指纹，用于判断是否真的变化。"""
    return repr(manifest)


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
    # 组件前向声明（回调里会引用）
    # ====================================================================

    tool_panel = None
    info_panel = None
    para_panel = None
    output_panel = None

    # ====================================================================
    # 回调：工具切换
    # ====================================================================

    def on_tool_selected(tool_id: str):
        """处理工具切换。"""
        info_panel.refresh()
        para_panel.refresh()
        output_panel.refresh()

    # ====================================================================
    # 回调：命令生成
    # ====================================================================

    _param_error_state = {"last": None}

    def on_parameter_changed():
        """参数发生变化后重新生成命令。"""

        manifest = state.get_selected_manifest()
        tool_state = state.get_current_state()

        if manifest is None or tool_state is None:
            output_panel.clear()
            _param_error_state["last"] = None
            return

        try:
            command = command_builder.build(
                manifest,
                tool_state,
            )
            output_panel.set_text(command)
            _param_error_state["last"] = None

        except ValueError as e:
            msg = str(e)

            # 清空输出，避免用户点到"参数错误: xxx"被复制走
            output_panel.clear()

            # 相同错误只在首次出现时提示，
            # 避免 Tab 跳转时反复弹
            if msg != _param_error_state["last"]:
                _param_error_state["last"] = msg
                ntf.show(f"参数错误: {msg}", type="error")

    # ====================================================================
    # 插件同步（热重载）
    # ====================================================================

    def add_new_plugins(new_manifests: list):
        """增量添加新插件。"""
        for manifest in new_manifests:
            tool_id = manifest.metadata.id

            if manifest not in state.manifests:
                state.manifests.append(manifest)
                logger.info(f"添加新插件: {tool_id}")

            if tool_id not in state.tool_states:
                state.tool_states[tool_id] = ToolState(tool_id)
                logger.debug(f"初始化插件状态: {tool_id}")

    def remove_plugins(removed_ids: set):
        """增量移除插件。"""
        for tool_id in removed_ids:
            state.manifests = [m for m in state.manifests if m.metadata.id != tool_id]

            if tool_id in state.tool_states:
                del state.tool_states[tool_id]
                logger.debug(f"移除插件状态: {tool_id}")

            if state.selected_tool_id == tool_id:
                state.selected_tool_id = (
                    state.manifests[0].metadata.id if state.manifests else None
                )
                logger.info(f"选中插件已移除，切换到: " f"{state.selected_tool_id}")

    def update_plugins(updated_manifests: list):
        """无条件替换 manifest（不只是版本变化时）。"""
        for new_manifest in updated_manifests:
            tool_id = new_manifest.metadata.id

            for i, old_manifest in enumerate(state.manifests):
                if old_manifest.metadata.id == tool_id:
                    state.manifests[i] = new_manifest
                    logger.info(f"更新插件: {tool_id}")
                    break

            if tool_id not in state.tool_states:
                state.tool_states[tool_id] = ToolState(tool_id)

    def sync_plugins() -> bool:
        """同步插件：只处理变更。

        返回是否检测到变更。
        """
        paths = discover_plugins()
        new_manifests = parse_manifests(paths)

        old_map = {m.metadata.id: m for m in state.manifests}
        new_map = {m.metadata.id: m for m in new_manifests}

        old_ids = set(old_map.keys())
        new_ids = set(new_map.keys())

        added_ids = new_ids - old_ids
        removed_ids = old_ids - new_ids
        common_ids = old_ids & new_ids

        # 无条件比对 common 的 manifest，
        # 用内容指纹判断是否真的变化
        changed_manifests = []
        for tool_id in common_ids:
            old_manifest = old_map[tool_id]
            new_manifest = new_map[tool_id]

            if _manifest_signature(old_manifest) != _manifest_signature(new_manifest):
                changed_manifests.append(new_manifest)
                logger.info(f"检测到插件变更: {tool_id}")

        added_manifests = [new_map[tid] for tid in added_ids]

        # 应用变更
        if added_manifests:
            add_new_plugins(added_manifests)
            logger.info(f"添加插件: {len(added_ids)} 个")

        if removed_ids:
            remove_plugins(removed_ids)
            logger.info(f"移除插件: {len(removed_ids)} 个")

        if changed_manifests:
            update_plugins(changed_manifests)
            logger.info(f"更新插件: {len(changed_manifests)} 个")

        # 有变更时刷新 UI
        if added_manifests or removed_ids or changed_manifests:
            tool_panel.refresh()

            # 修 bug：用 id 集合判断，而不是 Manifest 对象
            changed_ids = {m.metadata.id for m in changed_manifests}

            selected_affected = (
                state.selected_tool_id in added_ids
                or state.selected_tool_id in changed_ids
                or state.selected_tool_id in removed_ids
            )

            if selected_affected:
                info_panel.refresh()
                para_panel.refresh()
                output_panel.refresh()

            logger.info(
                f"插件同步完成: "
                f"添加 {len(added_ids)}, "
                f"移除 {len(removed_ids)}, "
                f"更新 {len(changed_manifests)}"
            )
            return True

        logger.debug("没有检测到插件变更")
        return False

    # ====================================================================
    # 回调：导入 / 导出 / 删除 / 重新扫描
    # ====================================================================

    def on_plugin_imported(paths: list[str]):
        """处理插件导入。"""

        if not paths:
            return

        result = plugin_import_export_service.import_plugins(paths)

        if result.success_count > 0:
            sync_plugins()

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
                    f"插件导入成功：" f"{result.success_count} 个",
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

    def on_plugin_deleted(plugin_id: str):
        """处理插件删除。"""
        result = plugin_import_export_service.delete_plugin(plugin_id)

        if result.success:
            sync_plugins()
            ntf.show(
                f"删除成功：{result.message}",
                type="success",
            )
        else:
            ntf.show(
                f"删除失败：{result.message}",
                type="error",
            )

    def on_plugin_rescan():
        """手动重新扫描插件目录。"""
        changed = sync_plugins()

        if changed:
            ntf.show("插件列表已更新", type="success")
        else:
            ntf.show("没有检测到插件变更", type="info")

    # ====================================================================
    # 创建页面组件
    # ====================================================================

    tool_panel = ToolPanel(
        state,
        on_tool_selected=on_tool_selected,
        on_plugin_imported=on_plugin_imported,
        on_plugin_exported=on_plugin_exported,
        on_plugin_deleted=on_plugin_deleted,
        on_plugin_rescan=on_plugin_rescan,
    )

    # 工具信息面板
    info_panel = InfoPanel(state)

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
