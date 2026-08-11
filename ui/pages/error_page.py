import flet as ft


def build_error_page(
    page: ft.Page,
    error: Exception,
    traceback_text: str,
    path_info: dict[str, str],
) -> None:
    """构建应用启动错误页面。"""

    page.title = "CMD Tools - 启动错误"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window.width = 1000
    page.window.height = 800

    # ====================================================================
    # 错误信息
    # ====================================================================

    error_text = ft.Text(
        str(error) or error.__class__.__name__,
        selectable=True,
        size=14,
    )

    traceback_field = ft.TextField(
        value=traceback_text,
        multiline=True,
        read_only=True,
        min_lines=15,
        max_lines=20,
        expand=True,
        text_size=12,
    )

    # ====================================================================
    # 路径信息
    # ====================================================================

    path_rows = []

    for key, value in path_info.items():
        path_rows.append(
            ft.Row(
                controls=[
                    ft.Text(
                        key,
                        width=180,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        value,
                        selectable=True,
                        expand=True,
                        size=12,
                    ),
                ],
                spacing=10,
            )
        )

    path_column = ft.Column(
        controls=path_rows,
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
    )

    # ====================================================================
    # 页面
    # ====================================================================

    page.add(
        ft.Column(
            controls=[
                ft.Text(
                    "CMD Tools 启动失败",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "应用在启动过程中发生异常，请根据下面的信息进行排查。",
                    size=14,
                ),
                ft.Divider(),
                ft.Text(
                    "错误",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),
                error_text,
                ft.Divider(),
                ft.Text(
                    "Traceback",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),
                traceback_field,
                ft.Divider(),
                ft.Text(
                    "路径信息",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(
                    content=path_column,
                    expand=True,
                ),
            ],
            expand=True,
            spacing=10,
        )
    )