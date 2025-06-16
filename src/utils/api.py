#!/usr/bin/env python3
# coding: utf-8

"""
API管理工具，负责各种API接口的调用认证和交互。
目前支持讯飞星火认知大模型API。
"""

import os
import json
import time
import hashlib
import base64
import hmac
import uuid
import datetime
import asyncio
from urllib.parse import urlencode, quote
from typing import Dict, Any, List, Optional, Callable, Union

import websockets

# 从配置和日志模块导入
from src.utils.config import get_config
from src.utils.logger import get_logger

# 创建日志记录器
logger = get_logger(__name__)

class APIManager:
    """API 管理类，提供各种API接口的认证和调用"""
    
    def __init__(self):
        """初始化API管理器，加载配置"""
        # 讯飞星火API配置
        self.spark_appid = get_config("SPARK_APPID", "")
        self.spark_apikey = get_config("SPARK_APIKEY", "")
        self.spark_apisecret = get_config("SPARK_APISECRET", "")
        
        # 讯飞星火WebSocket服务地址
        self.spark_host = "spark-api.xf-yun.com"
        self.spark_x1_path = "/v1/x1"  # X1模型的路径
        
        # 检查API配置
        if not all([self.spark_appid, self.spark_apikey, self.spark_apisecret]):
            logger.warning("讯飞星火API配置不完整，API功能可能无法使用")
    
    def generate_spark_auth_url(self, path: str) -> str:
        """
        生成讯飞星火API的认证URL
        
        Args:
            path: API路径，例如 "/v1/x1"
            
        Returns:
            包含认证信息的WebSocket URL
        """
        # 计算当前时间戳，RFC1123格式
        now = datetime.datetime.now()
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # 拼接签名原文
        # 签名原文 host + path + date
        signature_origin = f"host: {self.spark_host}\ndate: {date}\nGET {path} HTTP/1.1"
        
        # 使用HMAC-SHA256进行签名
        hmac_obj = hmac.new(
            self.spark_apisecret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        )
        signature = base64.b64encode(hmac_obj.digest()).decode()
        
        # 构建认证参数
        auth_params = {
            "host": self.spark_host,
            "date": date,
            "authorization": f"api_key=\"{self.spark_apikey}\", algorithm=\"hmac-sha256\", headers=\"host date request-line\", signature=\"{signature}\""
        }
        
        # 构建完整的WebSocket URL
        auth_url = f"wss://{self.spark_host}{path}?{urlencode(auth_params)}"
        
        return auth_url
    
    def build_spark_x1_request(self, 
                               query: str, 
                               chat_history: Optional[List[Dict[str, str]]] = None, 
                               temperature: float = 0.5,
                               max_tokens: int = 4096) -> Dict[str, Any]:
        """
        构建讯飞星火X1模型请求数据
        
        Args:
            query: 用户问题
            chat_history: 聊天历史记录，每个元素包含'role'和'content'
            temperature: 温度参数，控制随机性 (0.0-1.0)
            max_tokens: 最大生成token数量
            
        Returns:
            请求数据字典
        """
        # 如果没有提供聊天历史，则初始化一个空列表
        if chat_history is None:
            chat_history = []
            
        # 添加当前用户问题
        chat_history.append({
            "role": "user",
            "content": query
        })
        
        # 构建请求数据
        request_data = {
            "header": {
                "app_id": self.spark_appid,
                "uid": str(uuid.uuid1())  # 生成随机用户ID
            },
            "parameter": {
                "chat": {
                    "domain": "general",  # 通用领域
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            },
            "payload": {
                "message": {
                    "text": chat_history
                }
            }
        }
        
        return request_data
    
    async def call_spark_x1_api(self, 
                               query: str, 
                               chat_history: Optional[List[Dict[str, str]]] = None,
                               callback: Optional[Callable[[str], None]] = None) -> str:
        """
        调用讯飞星火X1大模型API
        
        Args:
            query: 用户问题
            chat_history: 聊天历史记录
            callback: 流式返回的回调函数，用于处理部分响应
            
        Returns:
            API返回的完整响应文本
        """
        # 检查API配置是否完整
        if not all([self.spark_appid, self.spark_apikey, self.spark_apisecret]):
            error_msg = "讯飞星火API配置不完整，无法调用API"
            logger.error(error_msg)
            return error_msg
        
        # 生成认证URL
        auth_url = self.generate_spark_auth_url(self.spark_x1_path)
        
        # 构建请求数据
        request = self.build_spark_x1_request(query, chat_history)
        request_json = json.dumps(request)
        
        # 存储完整响应
        full_response = ""
        error_message = None
        
        try:
            # 建立WebSocket连接
            async with websockets.connect(auth_url) as websocket:
                # 发送请求数据
                await websocket.send(request_json)
                logger.info(f"已发送请求到讯飞星火API: {query[:30]}...")
                
                # 接收响应数据
                while True:
                    response_text = await websocket.recv()
                    response = json.loads(response_text)
                    
                    # 检查响应状态
                    if response.get("header", {}).get("code") != 0:
                        error_code = response.get("header", {}).get("code")
                        error_msg = response.get("header", {}).get("message")
                        error_message = f"API调用错误: 代码={error_code}, 消息={error_msg}"
                        logger.error(error_message)
                        break
                    
                    # 提取回复文本
                    content = response.get("payload", {}).get("message", {}).get("content", "")
                    
                    if content:
                        # 更新完整响应
                        full_response += content
                        
                        # 如果提供了回调函数，调用它处理部分响应
                        if callback:
                            callback(content)
                    
                    # 检查是否是最后一个分片
                    is_last = response.get("header", {}).get("status") == 2
                    if is_last:
                        break
                
                logger.info(f"已收到讯飞星火API完整响应: {full_response[:50]}...")
        
        except Exception as e:
            error_message = f"调用讯飞星火API时发生错误: {str(e)}"
            logger.error(error_message)
        
        # 如果有错误，返回错误信息
        if error_message:
            return error_message
            
        return full_response
    
    def call_spark_x1_api_sync(self,
                              query: str,
                              chat_history: Optional[List[Dict[str, str]]] = None,
                              callback: Optional[Callable[[str], None]] = None) -> str:
        """
        同步调用讯飞星火X1大模型API（包装异步调用）
        
        Args:
            query: 用户问题
            chat_history: 聊天历史记录
            callback: 流式返回的回调函数
            
        Returns:
            API返回的完整响应文本
        """
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 在事件循环中运行异步调用
            result = loop.run_until_complete(
                self.call_spark_x1_api(query, chat_history, callback)
            )
            return result
        finally:
            # 关闭事件循环
            loop.close()

# 创建单例实例
api_manager = APIManager()

def get_api_manager() -> APIManager:
    """
    获取API管理器实例
    
    Returns:
        APIManager实例
    """
    return api_manager
