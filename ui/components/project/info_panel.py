# ui/components/info_panel.py

import flet as ft

from models.state import AppState


class InfoPanel:
    """工具信息面板组件，显示当前选中工具的元数据信息。"""

    # 默认空值显示
    _EMPTY_DISPLAY = "-"
    # 标签模板
    _LABEL_TEMPLATE = "{}: {}"

    def __init__(self, state: AppState):
        self.state = state

        # 初始化所有文本控件
        self._init_text_controls()

        # 构建视图
        self.view = self._build_view()

    def _init_text_controls(self):
        """初始化所有文本显示控件。"""
        # 使用字典存储，便于统一管理
        self._fields = {
            "name": ft.Text(
                size=20,
                weight=ft.FontWeight.BOLD,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            "id": ft.Text(
                size=20,
                weight=ft.FontWeight.BOLD,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            "version": ft.Text(
                size=20,
                weight=ft.FontWeight.BOLD,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            "description": ft.Text(
                size=20,
                weight=ft.FontWeight.BOLD,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        }
        
        # 为方便访问，保留属性引用
        self.title = self._fields["name"]
        self.tool_id = self._fields["id"]
        self.tool_version = self._fields["version"]
        self.tool_description = self._fields["description"]

        # 初始显示空状态
        self._update_display(None)

    def _build_view(self) -> ft.Container:
        """构建视图容器。"""
        return ft.Container(
            content=ft.Column(
                controls=list(self._fields.values()),
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=1,
            ),
            padding=5,
            margin=5,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            width=2000,
            height=110,
            expand=True,
        )

    def _update_display(self, manifest):
        """更新显示内容。"""
        if manifest is None or manifest.metadata is None:
            # 处理 None 情况
            for key in self._fields:
                self._fields[key].value = self._LABEL_TEMPLATE.format(
                    self._get_label(key), self._EMPTY_DISPLAY
                )
            return

        metadata = manifest.metadata
        # 定义字段映射
        field_mapping = {
            "name": metadata.name,
            "id": metadata.id,
            "version": metadata.version,
            "description": metadata.description,
        }

        for key, value in field_mapping.items():
            display_value = value if value is not None else self._EMPTY_DISPLAY
            self._fields[key].value = self._LABEL_TEMPLATE.format(
                self._get_label(key), display_value
            )

    @staticmethod
    def _get_label(key: str) -> str:
        """获取字段对应的中文标签。"""
        labels = {
            "name": "工具名称",
            "id": "工具ID",
            "version": "工具版本",
            "description": "工具描述",
        }
        return labels.get(key, key)

    def build(self):
        """返回视图组件。"""
        return self.view

    def refresh(self):
        """根据当前选中的工具刷新信息。"""
        manifest = self.state.get_selected_manifest()
        self._update_display(manifest)