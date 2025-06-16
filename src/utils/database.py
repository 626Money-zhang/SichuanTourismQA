#!/usr/bin/env python3
# coding: utf-8

"""
数据库管理模块，用于处理Neo4j数据库的连接和操作。
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from py2neo import Graph, Node, Relationship, NodeMatcher

# 从配置和日志模块导入
from src.utils.config import get_config
from src.utils.logger import get_logger

# 创建日志记录器
logger = get_logger(__name__)

class Neo4jManager:
    """Neo4j数据库管理类，提供连接和基本操作功能"""
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        初始化Neo4j数据库管理器
        
        Args:
            uri: Neo4j数据库URI，默认从配置获取
            user: 用户名，默认从配置获取
            password: 密码，默认从配置获取
        """
        # 优先使用传入的参数，否则从配置获取
        self.uri = uri or get_config("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or get_config("NEO4J_USER", "neo4j")
        self.password = password or get_config("NEO4J_PASSWORD", "neo4j")
        
        # 初始化连接为None，后续lazy加载
        self._graph = None
        self._node_matcher = None
    
    @property
    def graph(self) -> Graph:
        """
        获取Neo4j数据库连接，如果未连接则创建新连接
        
        Returns:
            Graph对象，用于执行Cypher查询
        """
        if self._graph is None:
            try:
                self._graph = Graph(uri=self.uri, auth=(self.user, self.password))
                logger.info("成功连接到Neo4j数据库")
            except Exception as e:
                logger.error(f"连接Neo4j数据库失败: {e}")
                # 重新抛出异常，让调用者处理
                raise
        
        return self._graph
    
    @property
    def matcher(self) -> NodeMatcher:
        """
        获取节点匹配器，用于查找节点
        
        Returns:
            NodeMatcher对象
        """
        if self._node_matcher is None:
            self._node_matcher = NodeMatcher(self.graph)
        
        return self._node_matcher
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行Cypher查询并返回结果
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数字典
            
        Returns:
            查询结果列表，每个元素是一个包含属性的字典
        """
        try:
            # 使用parameters执行参数化查询，防止注入攻击
            result = self.graph.run(query, parameters=parameters)
            return result.data()  # 转换为字典列表
        except Exception as e:
            logger.error(f"执行查询失败: {query}, 错误: {e}")
            # 重新抛出异常，让调用者处理
            raise
    
    def create_attraction_node(self, name: str, properties: Dict[str, Any]) -> Node:
        """
        创建一个景点节点
        
        Args:
            name: 景点名称
            properties: 景点其他属性的字典
            
        Returns:
            创建的Node对象
        """
        # 创建完整的属性字典
        full_props = {"name": name, **properties}
        
        try:
            # 创建节点
            node = Node("景点", **full_props)
            # 保存到数据库
            self.graph.create(node)
            logger.info(f"创建景点节点: {name}")
            return node
        except Exception as e:
            logger.error(f"创建景点节点失败: {name}, 错误: {e}")
            raise
    
    def create_relationship(self, start_node: Node, rel_type: str, end_node: Node, properties: Optional[Dict[str, Any]] = None) -> Relationship:
        """
        在两个节点之间创建关系
        
        Args:
            start_node: 起始节点
            rel_type: 关系类型
            end_node: 目标节点
            properties: 关系属性
            
        Returns:
            创建的Relationship对象
        """
        properties = properties or {}
        
        try:
            # 创建关系
            rel = Relationship(start_node, rel_type, end_node, **properties)
            # 保存到数据库
            self.graph.create(rel)
            logger.info(f"创建关系: ({start_node['name']}) -[{rel_type}]-> ({end_node['name']})")
            return rel
        except Exception as e:
            logger.error(f"创建关系失败: ({start_node['name']}) -[{rel_type}]-> ({end_node['name']}), 错误: {e}")
            raise
    
    def find_attraction_by_name(self, name: str) -> Optional[Node]:
        """
        通过名称查找景点节点
        
        Args:
            name: 景点名称
            
        Returns:
            找到的Node对象，如果未找到则返回None
        """
        try:
            return self.matcher.match("景点", name=name).first()
        except Exception as e:
            logger.error(f"查找景点失败: {name}, 错误: {e}")
            raise
    
    def clear_database(self) -> None:
        """
        清空数据库中的所有数据（谨慎使用）
        """
        try:
            self.graph.delete_all()  # 删除所有节点和关系
            logger.warning("已清空数据库")
        except Exception as e:
            logger.error(f"清空数据库失败: {e}")
            raise

# 创建单例实例
db_manager = Neo4jManager()

def get_db_manager() -> Neo4jManager:
    """
    获取Neo4j数据库管理器实例
    
    Returns:
        Neo4jManager实例
    """
    return db_manager
