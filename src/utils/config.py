#!/usr/bin/env python3
# coding: utf-8

"""
配置工具模块，用于管理项目的配置信息。
使用方法：
1. 首先在项目根目录创建 .env 文件
2. 在代码中导入此模块并使用 get_config 函数获取配置
"""

import os
from typing import Any, Dict, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    # Neo4j 数据库配置
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "neo4j",
    
    # 讯飞星火API配置
    "SPARK_APPID": "",
    "SPARK_APIKEY": "",
    "SPARK_APISECRET": "",
    
    # Web服务配置
    "FLASK_HOST": "0.0.0.0",
    "FLASK_PORT": "5000",
    "FLASK_DEBUG": "False",
    
    # 日志配置
    "LOG_LEVEL": "INFO"
}

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logger.info(f"从 {dotenv_path} 加载配置")
else:
    logger.warning(f".env文件不存在: {dotenv_path}, 将使用默认配置")

def get_config(key: str, default: Optional[Any] = None) -> Any:
    """
    获取配置项的值。
    
    Args:
        key: 配置项的键名
        default: 如果配置不存在时返回的默认值
        
    Returns:
        配置项的值或默认值
    """
    # 先从环境变量中获取
    value = os.environ.get(key)
    
    # 如果环境变量中没有，则从默认配置中获取
    if value is None:
        value = DEFAULT_CONFIG.get(key, default)
        
    return value

def get_all_config() -> Dict[str, Any]:
    """
    获取所有配置项。
    
    Returns:
        包含所有配置的字典
    """
    config = {}
    
    # 先加载默认配置
    for key, value in DEFAULT_CONFIG.items():
        config[key] = value
        
    # 用环境变量覆盖默认配置
    for key in DEFAULT_CONFIG:
        env_value = os.environ.get(key)
        if env_value is not None:
            config[key] = env_value
            
    return config

def check_required_configs(required_keys: list) -> bool:
    """
    检查必要的配置是否存在。
    
    Args:
        required_keys: 必要的配置项名称列表
        
    Returns:
        如果所有必要的配置都存在则返回True，否则返回False
    """
    missing_keys = []
    
    for key in required_keys:
        value = get_config(key)
        if value is None or value == "":
            missing_keys.append(key)
            
    if missing_keys:
        logger.warning(f"以下必需的配置项未设置: {', '.join(missing_keys)}")
        return False
        
    return True
