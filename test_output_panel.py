# tests/test_output_panel.py

import flet as ft

from models.state import AppState
from ui.components.project.output_panel import OutputPanel
from ui.components.stacked_notifications.stacked_notifications import (
    NotificationManager,
)


def main(page: ft.Page):
    page.title = "OutputPanel Test"
    page.padding = 20

    # 创建测试状态
    state = AppState()

    # 创建通知管理器
    ntf = NotificationManager(page)

    # 创建 OutputPanel
    output_panel = OutputPanel(
        state=state,
        ntf=ntf,
    )


    page.add(
        output_panel.build(),
    )

    # 测试设置输出内容
    output_panel.set_text(
        "python main.py --input test.txt --output result.txt"
    )


if __name__ == "__main__":
    ft.run(main)

