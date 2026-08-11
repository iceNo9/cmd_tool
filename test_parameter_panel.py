# test_tool_panel.py

import flet as ft

from models.app_state import AppState
from models.manifest import CLI, Metadata, Parameter
from services.manifest_parser_service import ManifestParser, parse_manifests
from services.plugin_loader_service import PluginLoader, discover_plugins
from ui.components.project.parameter_panel import ParameterPanel


def main(page: ft.Page):
    page.title = "Panel 测试"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    paths = discover_plugins()
    manifests = parse_manifests(paths)


    # 创建 AppState
    state = AppState(manifests)

    # 创建 Panel
    panel = ParameterPanel(state)

    # 添加到页面
    page.add(panel.build())


if __name__ == "__main__":
    ft.app(target=main)