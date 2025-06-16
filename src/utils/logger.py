#!/usr/bin/env python3
# coding: utf-8

"""
日志工具模块，提供统一的日志配置。
使用方法：
1. 在模块中导入: from src.utils.logger import get_logger
2. 获取logger: logger = get_logger(__name__)
3. 使用logger记录日志: logger.info("信息"), logger.error("错误"), 等
"""

import os
import logging
import logging.handlers
from typing import Optional

# 默认日志格式
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging(
    log_level: str = "INFO", 
    log_file: Optional[str] = None,
    log_format: str = DEFAULT_FORMAT
) -> None:
    """
    设置全局日志配置。
    
    Args:
        log_level: 日志级别，默认为INFO
        log_file: 日志文件路径，如果为None则只输出到控制台
        log_format: 日志格式
    """
    # 将字符串日志级别转换为logging模块的常量
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    level = level_map.get(log_level.upper(), logging.INFO)
    
    # 创建日志处理器列表
    handlers = [logging.StreamHandler()]  # 总是添加控制台处理器
    
    # 如果提供了日志文件路径，添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 创建按大小轮转的文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        handlers.append(file_handler)
    
    # 配置根日志器
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器。
    
    Args:
        name: 日志器名称，通常使用__name__传入模块名
    
    Returns:
        配置好的日志器
    """
    return logging.getLogger(name)

# 确保模块被导入时进行初始化
from src.utils.config import get_config

# 从配置获取日志级别
log_level = get_config("LOG_LEVEL", "INFO")

# 设置日志文件路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
log_dir = os.path.join(project_root, "logs")
log_file = os.path.join(log_dir, "sichuan_qa.log")

# 进行日志配置
setup_logging(log_level=log_level, log_file=log_file)
