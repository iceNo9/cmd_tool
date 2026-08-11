# ui/pages/main_page.py

import flet as ft

from models.manifest import Metadata
from ui.components.project.tool_panel import ToolList


def main(page: ft.Page):
    page.title = "CMD Tools"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    # 模拟数据
    tools = [
        Metadata(
            id="com.example.encoder",
            name="视频编码器",
            version="1.2.0",
            description="支持 H.264/H.265 视频编码转换工具",
        ),
        Metadata(
            id="com.example.scanner",
            name="端口扫描器",
            version="2.0.1",
            description="快速扫描目标主机的开放端口和服务",
        ),
        Metadata(
            id="com.example.renamer",
            name="批量重命名",
            version="0.9.5",
            description="支持正则表达式的文件批量重命名工具",
        ),
        Metadata(
            id="com.example.backup",
            name="数据库备份",
            version="3.1.0",
            description="PostgreSQL/MySQL 数据库自动备份工具",
        ),
        Metadata(
            id="com.example.cleaner",
            name="系统清理",
            version="1.0.0",
            description="清理临时文件、缓存和日志文件",
        ),
    ]
    
    def on_tool_click(metadata: Metadata):
        """点击插件卡片"""
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"点击了: {metadata.name} ({metadata.id})"),
            duration=2000,
        )
        page.snack_bar.open = True
        page.update()
    
    # 插件列表
    tool_list = ToolList(tools, on_tool_click=on_tool_click)
    tool_list.expand = True
    
    # ✅ 直接添加，不用 Container 包裹
    page.add(
        ft.Text("插件列表", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(height=20),
        tool_list,
    )
    
    page.update()


if __name__ == "__main__":
    ft.app(target=main)  # 注意：这里还是 ft.app，需要改成 ft.run