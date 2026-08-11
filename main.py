import flet as ft

from ui.pages.main_page import build_main_page


def main(page: ft.Page):
    build_main_page(page)


if __name__ == "__main__":
    ft.run(main)