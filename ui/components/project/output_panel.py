# ui/components/output_panel.py

import asyncio

import flet as ft

from models.state import AppState
from ui.components.stacked_notifications.stacked_notifications import (
    NotificationManager,
)


class OutputPanel:
    def __init__(
        self,
        state: AppState,
        ntf: NotificationManager,
    ):
        self.state = state
        self.ntf = ntf
        self.clipboard = ft.Clipboard()

        self.output_text = ft.Text(
            value="",
            expand=True,
            align=ft.Alignment.TOP_LEFT,
        )

        self.output_button = ft.TextButton(
            content=self.output_text,
            expand=True,
            on_click=self._on_click,
            width=2000
        )

        self.view = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("命令输出", weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    self.output_button,
                ],
                expand=True,
                spacing=5,  # 控件间距
            ),
            padding=5,
            margin=5,
            border=ft.Border.all(
                1,
                ft.Colors.GREY_400,
            ),
            border_radius=8,
            expand=True,
        )

    def build(self):
        return self.view

    def refresh(self) -> None:
        """根据当前工具刷新输出内容。"""
        # 当前工具切换时，先清空旧工具的命令输出。
        self.output_text.value = ""

    def set_text(self, text: str):
        """设置输出内容，并自动复制到剪贴板。"""
        self.output_text.value = text
        self._copy_to_clipboard()

    def get_text(self) -> str:
        """获取当前输出内容。"""
        return self.output_text.value or ""

    def _on_click(self, e: ft.ControlEvent):
        """点击输出内容时复制到剪贴板。"""
        self._copy_to_clipboard()

    def _copy_to_clipboard(self):
        """复制当前输出内容到剪贴板。"""
        text = self.get_text()

        if not text:
            self.ntf.show("没有可复制的内容", type="warning")
            return

        async def copy_and_verify():
            try:
                # 复制到剪贴板
                await self.clipboard.set(text)

                # 短暂延迟，确保剪贴板更新完成
                await asyncio.sleep(0.1)

                # 验证剪贴板内容
                try:
                    clipboard_text = await self.clipboard.get()
                    if clipboard_text == text:
                        self.ntf.show("已复制到剪切板", type="success")
                    else:
                        self.ntf.show("复制失败，请重试", type="error")
                except:
                    # 如果读取剪贴板失败，仍然认为复制成功（某些平台可能不支持读取）
                    self.ntf.show("已复制到剪切板")

            except Exception as e:
                self.ntf.show(f"复制失败: {str(e)}", type="error")

        self.view.page.run_task(copy_and_verify)
