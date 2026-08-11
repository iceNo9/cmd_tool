"""
插件卡片组件

负责显示单个插件信息。

设计原则:
- 不继承 Flet Control
- 内部组合 Flet 控件
- 通过 build() 暴露 UI
- 通过 refresh() 更新 UI

"""

from collections.abc import Callable

import flet as ft

from models.manifest import Metadata
from utils.log import get_logger
from utils.paths import get_log_dir

# 创建该模块专用的日志记录器
logger = get_logger(
    name="tool_card",
	log_dir=get_log_dir() / "logs",
    fmt_type="detailed",
    console_level=10,  # INFO
    file_level=10,  # DEBUG
)

class ToolCard:
    """
    插件卡片组件


    Example:

        card = ToolCard(
            metadata,
            on_click=lambda m:
                print(m.name)
        )

        page.add(
            card.build()
        )

    """

    def __init__(
        self,
        metadata: Metadata,
        on_click: Callable[[Metadata], None] | None = None,
        on_double_click: Callable[[Metadata], None] | None = None,
    ):

        logger.debug(f"ToolCard 初始化: {metadata.name}")

        # 展示数据
        self.metadata = metadata

        # 外部事件
        self.on_click = on_click
        self.on_double_click = on_double_click

        # Flet 控件
        self.view = self._build()

    # ===============================
    # 构建UI
    # ===============================

    def _build(self) -> ft.Control:

        self.card_container = ft.Container(
            content=self._build_content(),
            width=200,
            height=60,
            padding=10,
            margin=5,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=12,
            ink=True,
            on_click=self._handle_click,
        )

        gesture = ft.GestureDetector(
            content=self.card_container,
            on_tap=self._handle_click,
            on_double_tap=(self._handle_double_click if self.on_double_click else None),
        )

        # 保存引用
        self.gesture = gesture

        return gesture

    def _build_content(self) -> ft.Control:

        return ft.Column(
            controls=[
                ft.Text(
                    value=(f"{self.metadata.name}"),
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    value=(f"version: {self.metadata.version}"),
                    size=10,
                    color=ft.Colors.GREY_600,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                # ft.Text(
                #     value=(f"{self.metadata.description or '无'}"),
                #     size=12,
                #     max_lines=2,
                #     overflow=ft.TextOverflow.ELLIPSIS,
                # ),
            ],
            spacing=5,
        )

    # ===============================
    # 对外暴露
    # ===============================

    def build(self) -> ft.Control:
        """
        返回Flet控件

        Page里面调用
        """

        return self.view

    def refresh(self, metadata: Metadata | None = None):
        """
        刷新显示

        不负责业务逻辑

        """

        if metadata:

            logger.info(
                f"更新卡片: " f"{self.metadata.name}" f" -> " f"{metadata.name}"
            )

            self.metadata = metadata

        self.card_container.content = self._build_content()

        self.card_container.update()

    # ===============================
    # 事件
    # ===============================

    def _handle_click(self, e: ft.ControlEvent):

        logger.info(f"点击插件: {self.metadata.name}")

        if self.on_click:

            self.on_click(self.metadata)

    def _handle_double_click(self, e: ft.TapEvent):

        logger.info(f"双击插件: {self.metadata.name}")

        if self.on_double_click:

            self.on_double_click(self.metadata)

    # ===============================
    # 悬停效果
    # ===============================

    def set_hover(self, enable=True):

        if enable:

            self.card_container.shadow = ft.BoxShadow(
                spread_radius=2,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            )

        else:

            self.card_container.shadow = None

        self.card_container.update()
