import traceback

import flet as ft

from ui.pages.error_page import build_error_page
from utils.log import get_logger
from utils.paths import get_path_info

logger = get_logger(
    name="app",
    log_dir=None,
    fmt_type="detailed",
    console_level=10,
    file_level=10,
)


def main(page: ft.Page):
    try:
        logger.info("CMD Tools 开始启动")

        # ================================================================
        # 延迟导入
        # ================================================================
        #
        # 不放在文件顶部，这样即使 main_page 导入失败，
        # 也能够被下面的 try/except 捕获。
        #
        from ui.pages.main_page import build_main_page

        logger.info("开始构建主页面")

        build_main_page(page)

        logger.info("CMD Tools 启动完成")

    except Exception as e:
        traceback_text = traceback.format_exc()

        logger.exception("CMD Tools 启动失败")

        # 获取完整路径信息
        try:
            path_info = get_path_info()
        except Exception:
            path_info = {
                "path_info_error": traceback.format_exc(),
            }

        # 显示错误页面
        try:
            page.clean()
            build_error_page(
                page,
                error=e,
                traceback_text=traceback_text,
                path_info=path_info,
            )
        except Exception:
            # 错误页面自己也失败时，至少记录日志
            logger.exception("错误页面构建失败")
            raise


if __name__ == "__main__":
    ft.run(main)