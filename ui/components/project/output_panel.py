# ui/components/output_panel.py

import asyncio
import time

import flet as ft

from models.state import AppState
from ui.components.stacked_notifications.stacked_notifications import (
    NotificationManager,
)


class OutputPanel:
    """命令输出面板。

    交互约定：
    - 输出内容只读展示，用户点击输出框即复制当前内容。
    - set_text 仅更新显示，不触碰剪贴板。
    - 空内容点击时静默返回，不弹 warning。
    - 复制成功通知做节流，避免频繁点击刷屏。
    """

    # 复制成功通知的最小间隔（秒）
    _COPY_TOAST_COOLDOWN = 1.0

    # 剪贴板操作可能抛出的异常类型
    # （Flet 未明确文档化，这里覆盖常见平台相关异常）
    _CLIPBOARD_ERRORS = (OSError, RuntimeError, AssertionError)

    def __init__(
        self,
        state: AppState,
        ntf: NotificationManager,
    ):
        self.state = state
        self.ntf = ntf
        self.clipboard = ft.Clipboard()

        # 上次复制成功通知的时间戳
        self._last_copy_toast_at: float = 0.0

        self.output_text = ft.Text(
            value="",
            expand=True,
            align=ft.Alignment.TOP_LEFT,
        )

        self.output_button = ft.TextButton(
            content=self.output_text,
            expand=True,
            on_click=self._on_click,
            width=2000,
        )

        self.view = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("命令输出", weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    self.output_button,
                ],
                expand=True,
                spacing=5,
            ),
            padding=5,
            margin=5,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            expand=True,
        )

    # ====================================================================
    # 构建 / 刷新
    # ====================================================================

    def build(self):
        return self.view

    def refresh(self) -> None:
        """工具切换时清空旧工具的命令输出。"""
        self.output_text.value = ""

    def clear(self) -> None:
        """清空输出内容。"""
        self.output_text.value = ""

    # ====================================================================
    # 文本读写
    # ====================================================================

    def set_text(self, text: str) -> None:
        """设置输出内容。

        仅更新显示，不自动复制到剪贴板。
        复制由用户点击输出框显式触发。
        """
        self.output_text.value = text or ""

    def get_text(self) -> str:
        """获取当前输出内容。"""
        return self.output_text.value or ""

    # ====================================================================
    # 复制
    # ====================================================================

    def _on_click(self, e: ft.ControlEvent):
        """点击输出内容时复制到剪贴板。"""
        self._copy_to_clipboard()

    def _copy_to_clipboard(self, *, silent_if_empty: bool = True):
        """复制当前输出内容到剪贴板。

        Args:
            silent_if_empty: 空内容时是否静默返回。
                默认 True，避免用户误点空白区域时被 warning 打扰。
        """
        text = self.get_text()

        if not text:
            if not silent_if_empty:
                self.ntf.show("没有可复制的内容", type="warning")
            return

        async def copy_and_verify():
            # ---- 写入剪贴板 ----
            try:
                await self.clipboard.set(text)
            except self._CLIPBOARD_ERRORS as exc:
                self.ntf.show(f"复制失败: {exc!s}", type="error")
                return

            # ---- 短暂延迟，确保剪贴板更新完成 ----
            await asyncio.sleep(0.1)

            # ---- 验证剪贴板内容 ----
            try:
                clipboard_text = await self.clipboard.get()
                ok = clipboard_text == text
            except self._CLIPBOARD_ERRORS:
                # 某些平台不支持读取剪贴板，视为成功
                ok = True

            if ok:
                self._notify_copy_success()
            else:
                self.ntf.show("复制失败，请重试", type="error")

        self.view.page.run_task(copy_and_verify)

    def _notify_copy_success(self):
        """复制成功通知（带节流）。"""
        now = time.monotonic()

        if now - self._last_copy_toast_at < self._COPY_TOAST_COOLDOWN:
            return

        self._last_copy_toast_at = now
        self.ntf.show("已复制到剪切板", type="success")
