# models\app_state.py


"""
应用状态管理模块

负责管理当前工具的运行时状态和参数值。

职责范围：
    - 保存当前工具的运行时状态
    - 提供类型安全的参数读写
    - 支持批量操作
    - 支持状态重置和快照

不负责：
    - GUI 界面更新
    - 配置持久化（保存到文件/数据库）
    - 命令生成和执行
    - 多工具并发管理

依赖：
    - dataclasses: 数据类

Example:
    >>> state = ToolState("com.example.myplugin")
    >>> state.set("input_file", "/path/to/file.txt")
    >>> state.set("verbose", True)
    >>> 
    >>> input_file = state.get("input_file")
    >>> is_verbose = state.get("verbose", False)
    >>> 
    >>> all_params = state.export()
    >>> print(all_params)  # {"input_file": "/path/to/file.txt", "verbose": True}
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field


@dataclass
class ToolState:
    """
    工具运行时状态
    
    管理单个工具的运行时参数和状态。
    
    Attributes:
        tool_id: 工具唯一标识符
        values: 参数键值对
        dirty: 是否有未保存的修改
        
    Usage:
        >>> state = ToolState("com.example.plugin")
        >>> state.set("key", "value")
        >>> state.get("key")  # "value"
    """
    
    tool_id: str
    """工具唯一标识符"""
    
    values: dict[str, object] = field(default_factory=dict, init=False)
    """参数键值对"""
    
    dirty: bool = field(default=False, init=False)
    """是否有未保存的修改"""
    
    # ========================================================================
    # 单值操作
    # ========================================================================
    
    def set(self, key: str, value: object) -> None:
        """
        设置参数值
        
        Args:
            key: 参数名
            value: 参数值
            
        Example:
            >>> state.set("input_file", "/path/to/file.txt")
            >>> state.set("verbose", True)
            >>> state.set("count", 42)
        """
        if key not in self.values or self.values[key] != value:
            self.values[key] = value
            self.dirty = True
    
    def get(self, key: str, default: object = None) -> object:
        """
        获取参数值
        
        Args:
            key: 参数名
            default: 默认值（参数不存在时返回）
            
        Returns:
            参数值
            
        Example:
            >>> value = state.get("input_file")
            >>> count = state.get("count", 0)
        """
        return self.values.get(key, default)
    
    def remove(self, key: str) -> bool:
        """
        移除参数
        
        Args:
            key: 参数名
            
        Returns:
            bool: 成功移除返回 True，键不存在返回 False
            
        Example:
            >>> state.remove("temp_param")
        """
        if key in self.values:
            del self.values[key]
            self.dirty = True
            return True
        return False
    
    def has(self, key: str) -> bool:
        """
        检查参数是否存在
        
        Args:
            key: 参数名
            
        Returns:
            bool: 参数存在返回 True
            
        Example:
            >>> if state.has("input_file"):
            ...     print("已设置输入文件")
        """
        return key in self.values
    
    # ========================================================================
    # 批量操作
    # ========================================================================
    
    def set_many(self, params: dict[str, object]) -> None:
        """
        批量设置参数
        
        Args:
            params: 参数字典
            
        Example:
            >>> state.set_many({
            ...     "input_file": "/path/to/file.txt",
            ...     "verbose": True,
            ...     "count": 42,
            ... })
        """
        for key, value in params.items():
            if key not in self.values or self.values[key] != value:
                self.values[key] = value
                self.dirty = True
    
    def export(self) -> dict[str, object]:
        """
        导出所有参数（深拷贝）
        
        Returns:
            dict: 参数副本，修改不影响原状态
            
        Example:
            >>> params = state.export()
            >>> params["temp"] = "value"  # 不影响 state
        """
        return copy.deepcopy(self.values)
    
    def keys(self) -> list[str]:
        """
        获取所有参数名
        
        Returns:
            list[str]: 参数名列表
            
        Example:
            >>> for key in state.keys():
            ...     print(key)
        """
        return list(self.values.keys())
    
    def items(self) -> list[tuple[str, object]]:
        """
        获取所有键值对
        
        Returns:
            list[tuple]: 键值对列表
            
        Example:
            >>> for key, value in state.items():
            ...     print(f"{key} = {value}")
        """
        return list(self.values.items())
    
    # ========================================================================
    # 状态管理
    # ========================================================================
    
    def clear(self) -> None:
        """
        清空所有参数
        
        Example:
            >>> state.clear()
            >>> state.is_empty()  # True
        """
        if self.values:
            self.values.clear()
            self.dirty = True
    
    def reset(self) -> None:
        """
        重置状态（清空并重置 dirty 标志）
        
        Example:
            >>> state.reset()
        """
        self.values.clear()
        self.dirty = False
    
    def is_empty(self) -> bool:
        """
        检查状态是否为空
        
        Returns:
            bool: 无参数返回 True
            
        Example:
            >>> if state.is_empty():
            ...     print("未设置任何参数")
        """
        return len(self.values) == 0
    
    def count(self) -> int:
        """
        获取参数数量
        
        Returns:
            int: 参数数量
            
        Example:
            >>> print(f"已设置 {state.count()} 个参数")
        """
        return len(self.values)
    
    def mark_clean(self) -> None:
        """
        标记为已保存（清除 dirty 标志）
        
        Example:
            >>> state.set("key", "value")
            >>> state.is_dirty()  # True
            >>> state.mark_clean()
            >>> state.is_dirty()  # False
        """
        self.dirty = False
    
    def is_dirty(self) -> bool:
        """
        检查是否有未保存的修改
        
        Returns:
            bool: 有未保存修改返回 True
            
        Example:
            >>> if state.is_dirty():
            ...     print("有未保存的修改")
        """
        return self.dirty
    
    # ========================================================================
    # 特殊方法
    # ========================================================================
    
    def __getitem__(self, key: str) -> object:
        """
        支持字典式访问
        
        Example:
            >>> value = state["input_file"]
        """
        return self.values[key]
    
    def __setitem__(self, key: str, value: object) -> None:
        """
        支持字典式赋值
        
        Example:
            >>> state["input_file"] = "/path/to/file.txt"
        """
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """
        支持 in 操作符
        
        Example:
            >>> if "input_file" in state:
            ...     print("已设置")
        """
        return key in self.values
    
    def __len__(self) -> int:
        """
        支持 len()
        
        Example:
            >>> print(len(state))
        """
        return len(self.values)
    
    def __repr__(self) -> str:
        return (
            f"ToolState(tool_id='{self.tool_id}', "
            f"params={len(self.values)}, "
            f"dirty={self.dirty})"
        )
    
    def __str__(self) -> str:
        lines = [f"ToolState({self.tool_id}):"]
        if self.is_empty():
            lines.append("  (空)")
        else:
            for key, value in self.values.items():
                lines.append(f"  {key} = {value}")
        lines.append(f"  dirty: {self.dirty}")
        return "\n".join(lines)