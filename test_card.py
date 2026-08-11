"""
ToolCard 测试
"""

import sys

from pathlib import Path

project_root = Path(__file__).parent.parent


sys.path.insert(0, str(project_root))


import flet as ft


from models.manifest import Metadata

from ui.components.project.tool_card import ToolCard


def main(page: ft.Page):

    page.title = "ToolCard测试"

    page.padding = 20

    metadata = Metadata(
        id="com.example.test",
        name="测试插件",
        version="1.0.0",
        description=("这是一个测试插件" "用于验证新的组件模式"),
    )

    def click(metadata: Metadata):

        print("点击:", metadata.name)

    card = ToolCard(metadata, on_click=click)

    page.add(
        ft.Column(
            controls=[
                ft.Text("ToolCard测试", size=24, weight=ft.FontWeight.BOLD),
                card.build(),
            ]
        )
    )


if __name__ == "__main__":

    ft.app(target=main)
