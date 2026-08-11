"""
应用状态持久化服务

负责将 AppState 保存到文件并从文件恢复。

职责范围：
- 保存 AppState 到 YAML 文件
- 从 YAML 文件加载 AppState
- 管理状态文件路径

不负责：
- 状态数据的业务逻辑
- GUI 界面更新

依赖：
- models.state: AppState, ToolState
- utils.paths: 路径管理
- ruamel.yaml: YAML 序列化
"""

from pathlib import Path

from ruamel.yaml import YAML

from models.state import AppState, ToolState
from utils.log import get_logger
from utils.paths import ensure_dir, get_data_dir, get_log_dir

# ========================================================================
# 日志
# ========================================================================

logger = get_logger(
    name="state_service",
	log_dir=get_log_dir() / "logs",
    fmt_type="detailed",
    console_level=20,  # INFO
    file_level=10,  # DEBUG
)


class StateService:
    """应用状态持久化服务"""

    # 状态文件名
    STATE_FILE = "app_state.yaml"

    def __init__(self, state_file: str | None = None):
        """
        初始化状态服务

        Args:
            state_file: 状态文件名，默认使用 app_state.yaml
        """
        self.state_file = state_file or self.STATE_FILE

        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)

        logger.debug(
            "StateService 初始化完成: state_file=%s",
            self.state_file,
        )

    # ====================================================================
    # 路径管理
    # ====================================================================

    def get_state_file_path(self) -> Path:
        """获取状态文件完整路径"""
        data_dir = get_data_dir()
        ensure_dir(data_dir)

        state_file = data_dir / self.state_file

        logger.debug(
            "状态文件路径: %s",
            state_file,
        )

        return state_file

    def exists(self) -> bool:
        """检查状态文件是否存在"""
        state_file = self.get_state_file_path()
        exists = state_file.exists()

        logger.debug(
            "检查状态文件: path=%s, exists=%s",
            state_file,
            exists,
        )

        return exists

    # ====================================================================
    # 核心持久化方法
    # ====================================================================

    def save(self, app_state: AppState) -> bool:
        """
        保存应用状态到文件

        Args:
            app_state: 应用状态对象

        Returns:
            bool: 保存成功返回 True
        """
        state_file = self.get_state_file_path()

        logger.info(
            "开始保存应用状态: path=%s",
            state_file,
        )

        try:
            # ------------------------------------------------------------
            # 收集需要保存的工具状态
            # ------------------------------------------------------------

            non_empty_states = {
                tool_id: state
                for tool_id, state in app_state.tool_states.items()
                if not state.is_empty()
            }

            logger.debug(
                "准备保存状态: selected_tool_id=%s, tool_search=%r, "
                "tool_states=%d/%d",
                app_state.selected_tool_id,
                app_state.tool_search,
                len(non_empty_states),
                len(app_state.tool_states),
            )

            logger.debug(
                "待保存工具: %s",
                list(non_empty_states.keys()),
            )

            # ------------------------------------------------------------
            # 构建 YAML 数据
            # ------------------------------------------------------------

            data = {
                "selected_tool_id": app_state.selected_tool_id,
                "tool_search": app_state.tool_search,
                "tool_states": {
                    tool_id: state.to_dict()
                    for tool_id, state in non_empty_states.items()
                },
            }

            # ------------------------------------------------------------
            # 写入文件
            # ------------------------------------------------------------

            logger.debug(
                "正在写入状态文件: %s",
                state_file,
            )

            with open(state_file, "w", encoding="utf-8") as f:
                self.yaml.dump(data, f)

            logger.debug(
                "状态文件写入完成: %s",
                state_file,
            )

            # ------------------------------------------------------------
            # 标记状态为 clean
            # ------------------------------------------------------------

            clean_count = 0

            for state in app_state.tool_states.values():
                state.mark_clean()
                clean_count += 1

            logger.debug(
                "已标记工具状态为 clean: count=%d",
                clean_count,
            )

            logger.info(
                "应用状态保存成功: path=%s, tools=%d",
                state_file,
                len(non_empty_states),
            )

            return True

        except Exception:
            logger.exception(
                "保存应用状态失败: path=%s",
                state_file,
            )
            return False

    def load(self, app_state: AppState) -> bool:
        """
        从文件加载状态到应用状态对象。

        如果状态文件不存在，则自动创建默认状态文件。

        Args:
            app_state: 应用状态对象（会被修改）

        Returns:
            bool: 加载成功或初始化成功返回 True

        Raises:
            Exception: 状态文件读取或解析失败时抛出异常
        """
        state_file = self.get_state_file_path()

        logger.info(
            "开始加载应用状态: path=%s",
            state_file,
        )

        # ------------------------------------------------------------
        # 检查文件
        # ------------------------------------------------------------

        if not state_file.exists():
            logger.info(
                "状态文件不存在，创建默认状态文件: %s",
                state_file,
            )

            # 第一次启动时没有状态文件，
            # 使用当前 AppState 创建一个初始状态文件。
            if self.save(app_state):
                logger.info(
                    "默认状态文件创建成功: %s",
                    state_file,
                )
                return True

            logger.error(
                "默认状态文件创建失败: %s",
                state_file,
            )
            return False

        try:
            # ------------------------------------------------------------
            # 读取 YAML
            # ------------------------------------------------------------

            logger.debug(
                "正在读取状态文件: %s",
                state_file,
            )

            with open(state_file, "r", encoding="utf-8") as f:
                data = self.yaml.load(f)

            if data is None:
                raise ValueError(f"状态文件为空: {state_file}")

            logger.debug(
                "状态文件读取完成: keys=%s",
                list(data.keys()),
            )

            # ------------------------------------------------------------
            # 恢复选中的工具
            # ------------------------------------------------------------

            if "selected_tool_id" in data:
                tool_id = data["selected_tool_id"]

                logger.debug(
                    "尝试恢复选中工具: tool_id=%s",
                    tool_id,
                )

                # --------------------------------------------------------
                # 持久化的工具仍然存在
                # --------------------------------------------------------

                if tool_id is not None and app_state.get_manifest(tool_id) is not None:
                    app_state.selected_tool_id = tool_id

                    logger.info(
                        "恢复选中工具成功: tool_id=%s",
                        tool_id,
                    )

                # --------------------------------------------------------
                # 持久化的工具已经不存在
                # --------------------------------------------------------

                else:
                    app_state.selected_tool_id = None

            # ------------------------------------------------------------
            # 恢复搜索关键词
            # ------------------------------------------------------------

            if "tool_search" in data:
                app_state.tool_search = data["tool_search"]

                logger.debug(
                    "恢复工具搜索关键词: %r",
                    app_state.tool_search,
                )

            # ------------------------------------------------------------
            # 恢复工具状态
            # ------------------------------------------------------------

            if "tool_states" in data:
                tool_states = data["tool_states"]

                logger.debug(
                    "发现持久化工具状态: count=%d",
                    len(tool_states),
                )

                for tool_id, state_data in tool_states.items():

                    # ----------------------------------------------------
                    # 当前工具不存在
                    # ----------------------------------------------------

                    if tool_id not in app_state.tool_states:
                        logger.warning(
                            "持久化工具状态对应的工具已不存在，跳过恢复: "
                            "tool_id=%s",
                            tool_id,
                        )
                        continue

                    logger.debug(
                        "开始恢复工具状态: tool_id=%s",
                        tool_id,
                    )

                    # ----------------------------------------------------
                    # 反序列化 ToolState
                    # ----------------------------------------------------

                    loaded_state = ToolState.from_dict(state_data)

                    logger.debug(
                        "工具状态解析完成: tool_id=%s, values=%d",
                        tool_id,
                        len(loaded_state.values),
                    )

                    # ----------------------------------------------------
                    # 验证 tool_id
                    # ----------------------------------------------------

                    if loaded_state.tool_id != tool_id:
                        raise ValueError(
                            "状态文件中的 tool_id 不一致: "
                            f"key={tool_id}, "
                            f"state.tool_id={loaded_state.tool_id}"
                        )

                    # ----------------------------------------------------
                    # 恢复工具状态
                    # ----------------------------------------------------

                    app_state.tool_states[tool_id] = loaded_state

                    logger.debug(
                        "工具状态恢复完成: tool_id=%s",
                        tool_id,
                    )

            logger.info(
                "应用状态加载成功: path=%s",
                state_file,
            )

            return True

        except Exception:
            logger.exception(
                "加载应用状态失败: path=%s",
                state_file,
            )
            raise

    # ====================================================================
    # 便捷方法
    # ====================================================================

    def auto_save(self, app_state: AppState) -> bool:
        """
        自动保存（仅当状态有变化时）

        Args:
            app_state: AppState

        Returns:
            bool: 保存成功返回 True；没有需要保存的状态返回 False
        """
        dirty = app_state.is_dirty()

        logger.debug(
            "执行自动保存检查: dirty=%s",
            dirty,
        )

        if dirty:
            logger.info("检测到应用状态变化，执行自动保存")
            return self.save(app_state)

        logger.debug("应用状态未发生变化，跳过自动保存")
        return False

    def delete(self) -> bool:
        """
        删除状态文件

        Returns:
            bool: 删除成功返回 True
        """
        state_file = self.get_state_file_path()

        logger.info(
            "开始删除状态文件: path=%s",
            state_file,
        )

        if not state_file.exists():
            logger.debug(
                "状态文件不存在，无需删除: %s",
                state_file,
            )
            return True

        try:
            state_file.unlink()

            logger.info(
                "状态文件删除成功: %s",
                state_file,
            )

            return True

        except Exception:
            logger.exception(
                "删除状态文件失败: path=%s",
                state_file,
            )
            return False

    def reset(self, app_state: AppState) -> None:
        """
        重置状态为默认值。

        操作：
        1. 清空所有工具状态
        2. 清空搜索关键词
        3. 默认选中第一个工具
        4. 删除持久化状态文件

        Args:
            app_state: AppState
        """
        logger.info("开始重置应用状态")

        try:
            # ------------------------------------------------------------
            # 清空工具状态
            # ------------------------------------------------------------

            app_state.clear_all_states()

            logger.debug("已清空所有工具状态")

            # ------------------------------------------------------------
            # 清空搜索关键词
            # ------------------------------------------------------------

            app_state.tool_search = ""

            logger.debug("已清空工具搜索关键词")

            # ------------------------------------------------------------
            # 恢复默认选中工具
            # ------------------------------------------------------------

            if app_state.manifests:
                default_tool_id = app_state.manifests[0].metadata.id
                app_state.selected_tool_id = default_tool_id

                logger.debug(
                    "已恢复默认选中工具: tool_id=%s",
                    default_tool_id,
                )
            else:
                app_state.selected_tool_id = None

                logger.debug(
                    "当前没有可用工具，selected_tool_id=None",
                )

            # ------------------------------------------------------------
            # 删除持久化状态
            # ------------------------------------------------------------

            if self.delete():
                logger.info("持久化状态文件已删除")
            else:
                logger.warning(
                    "应用状态已重置，但状态文件删除失败",
                )

            logger.info("应用状态重置完成")

        except Exception:
            logger.exception("重置应用状态失败")
            raise
