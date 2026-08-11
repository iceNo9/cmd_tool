# test_tool_panel.py


import flet as ft

from models.app_state import AppState
from models.manifest import Metadata
from ui.components.project.tool_panel import ToolPanel


def main(page: ft.Page):

    tools = [
        Metadata(
            id="1",
            name="Image Processor",
            version="1.0",
            description="图片处理图片处理图片处理图片处理图片处理图片处理图片处理",
        ),
        Metadata(id="2", name="PDF Generator", version="2.0", description="PDF生成"),
        Metadata(id="3", name="PDF Generator", version="2.0", description="PDF生成"),
        Metadata(id="3", name="PDF Generator", version="2.0", description="PDF生成"),
        Metadata(id="4", name="PDF Generator", version="2.0", description="PDF生成"),
        Metadata(id="5", name="PDF Generator", version="2.0", description="PDF生成"),
        Metadata(id="6", name="PDF Generator", version="2.0", description="PDF生成"),
        Metadata(id="7", name="PDF Generator", version="2.0", description="PDF生成"),
        Metadata(id="8", name="PDF Generator", version="2.0", description="PDF生成"),
        Metadata(id="9", name="PDF Generator", version="2.0", description="PDF生成"),
    ]

    state = AppState(tools=tools)

    panel = ToolPanel(state)

    page.add(panel.build())
    


ft.app(target=main)
