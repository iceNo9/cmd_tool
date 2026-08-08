"""
日志模块 - 提供统一的日志记录功能
支持控制台输出和文件输出，可配置日志级别和格式
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional


class Logger:
    """
    日志管理器类
    支持多种日志输出方式和灵活的配置
    """
    
    # 预定义的日志格式
    FORMATS = {
        'default': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'detailed': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        'simple': '%(levelname)s - %(message)s',
        'minimal': '%(message)s'
    }
    
    _instances = {}
    
    def __new__(cls, name: str = 'default', *args, **kwargs):
        """单例模式，相同名称的logger只创建一次"""
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
    
    def __init__(
        self,
        name: str = 'default',
        log_dir: str = 'logs',
        log_level: int = logging.DEBUG,
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        fmt_type: str = 'default',
        use_file: bool = True,
        use_console: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        use_timed_rotation: bool = False
    ):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            log_dir: 日志文件存放目录
            log_level: 全局日志级别
            console_level: 控制台输出级别
            file_level: 文件输出级别
            fmt_type: 日志格式类型 ('default', 'detailed', 'simple', 'minimal')
            use_file: 是否启用文件日志
            use_console: 是否启用控制台日志
            max_bytes: 单个日志文件最大字节数（用于RotatingFileHandler）
            backup_count: 保留的日志文件备份数量
            use_timed_rotation: 是否使用按时间轮转
        """
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.name = name
        self.log_dir = log_dir
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # 清除已有的处理器，避免重复添加
        self.logger.handlers.clear()
        
        # 获取日志格式
        self.formatter = logging.Formatter(
            self.FORMATS.get(fmt_type, self.FORMATS['default']),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 添加控制台处理器
        if use_console:
            self._add_console_handler(console_level)
        
        # 添加文件处理器
        if use_file:
            self._add_file_handler(file_level, max_bytes, backup_count, use_timed_rotation)
        
        self._initialized = True
    
    def _add_console_handler(self, level: int):
        """添加控制台日志处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self, level: int, max_bytes: int, backup_count: int, use_timed_rotation: bool):
        """添加文件日志处理器"""
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 生成日志文件名
        log_file = os.path.join(self.log_dir, f'{self.name}_{datetime.now().strftime("%Y%m%d")}.log')
        
        if use_timed_rotation:
            # 按时间轮转：每天午夜轮转
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.suffix = '%Y%m%d'
        else:
            # 按大小轮转
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        
        file_handler.setLevel(level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录INFO级别日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """记录异常日志，自动包含堆栈信息"""
        self.logger.exception(message, *args, **kwargs)
    
    def set_level(self, level: int):
        """动态设置日志级别"""
        self.logger.setLevel(level)
    
    def add_filter(self, log_filter):
        """添加日志过滤器"""
        self.logger.addFilter(log_filter)
    
    def remove_handler(self, handler_type):
        """移除指定类型的处理器"""
        for handler in self.logger.handlers[:]:
            if isinstance(handler, handler_type):
                self.logger.removeHandler(handler)
    
    def close(self):
        """关闭所有处理器"""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


# 创建默认的日志记录器实例
default_logger = Logger('app')

# 快捷函数，方便直接使用
def debug(msg: str, *args, **kwargs):
    """全局DEBUG日志函数"""
    default_logger.debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs):
    """全局INFO日志函数"""
    default_logger.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    """全局WARNING日志函数"""
    default_logger.warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    """全局ERROR日志函数"""
    default_logger.error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    """全局CRITICAL日志函数"""
    default_logger.critical(msg, *args, **kwargs)

def exception(msg: str, *args, **kwargs):
    """全局异常日志函数"""
    default_logger.exception(msg, *args, **kwargs)

def get_logger(name: str = 'app', **kwargs) -> Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        **kwargs: 传递给Logger的其他参数
    
    Returns:
        Logger实例
    
    Example:
        >>> logger = get_logger('my_module', log_dir='custom_logs')
        >>> logger.info("这是来自my_module的日志")
    """
    return Logger(name, **kwargs)


# 配置示例
def configure_logger(config: dict):
    """
    根据配置字典配置日志
    
    Args:
        config: 配置字典，可包含以下键：
            - name: 日志记录器名称
            - log_dir: 日志目录
            - log_level: 日志级别
            - console_level: 控制台级别
            - file_level: 文件级别
            - fmt_type: 格式类型
            - max_bytes: 最大文件大小
            - backup_count: 备份数量
            - use_timed_rotation: 是否使用时间轮转
    
    Example:
        >>> configure_logger({
        ...     'name': 'web_app',
        ...     'log_dir': './logs/web',
        ...     'log_level': logging.INFO,
        ...     'fmt_type': 'detailed'
        ... })
    """
    global default_logger
    default_logger = Logger(**config)


if __name__ == '__main__':
    # 使用示例
    print("=" * 60)
    print("日志模块测试")
    print("=" * 60)
    
    # 测试默认logger
    print("\n1. 测试默认日志记录器：")
    debug("这是一条DEBUG级别的日志")
    info("这是一条INFO级别的日志")
    warning("这是一条WARNING级别的日志")
    error("这是一条ERROR级别的日志")
    critical("这是一条CRITICAL级别的日志")
    
    # 测试异常日志
    print("\n2. 测试异常日志记录：")
    try:
        result = 10 / 0
    except Exception as e:
        exception(f"捕获到除零异常: {e}")
    
    # 测试自定义logger
    print("\n3. 测试自定义日志记录器：")
    custom_logger = get_logger(
        name='database',
        log_dir='logs/db',
        fmt_type='detailed',
        console_level=logging.WARNING
    )
    custom_logger.info("数据库连接成功")
    custom_logger.error("数据库查询失败")
    
    # 测试配置更新
    print("\n4. 测试配置更新：")
    configure_logger({
        'name': 'new_app',
        'log_dir': 'logs/new',
        'fmt_type': 'simple'
    })
    info("使用新配置的日志")
    
    print("\n日志文件已生成，请查看 logs 目录")