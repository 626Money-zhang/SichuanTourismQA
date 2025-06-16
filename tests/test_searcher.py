#!/usr/bin/env python3
# coding: utf-8
# File: test_searcher.py

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加上级目录到路径中，使测试可以导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from answer_search import AnswerSearcher

class TestAnswerSearcher(unittest.TestCase):
    """测试答案搜索器"""
    
    @patch('answer_search.Graph')
    def setUp(self, mock_graph):
        """每个测试用例开始前执行，初始化搜索器（使用模拟的Neo4j连接）"""
        # 创建Graph实例的模拟
        self.mock_graph_instance = MagicMock()
        mock_graph.return_value = self.mock_graph_instance
        
        self.searcher = AnswerSearcher()
    
    def test_answer_prettify_address(self):
        """测试地址答案的美化"""
        answers = [{'name': '武侯祠', '地址': '武侯祠大街231号'}]
        result = self.searcher.answer_prettify('地址', answers)
        
        expected = "武侯祠的地址是：武侯祠大街231号。"
        self.assertEqual(expected, result)
    
    def test_answer_prettify_missing_value(self):
        """测试缺失值的情况"""
        answers = [{'name': '武侯祠', '地址': None}]
        result = self.searcher.answer_prettify('地址', answers)
        
        expected = "抱歉，未能查询到武侯祠的地址信息。"
        self.assertEqual(expected, result)
    
    def test_answer_prettify_multiple_answers(self):
        """测试多个答案的情况"""
        answers = [
            {'name': '武侯祠', '地址': '武侯祠大街231号'},
            {'name': '锦里', '地址': '武侯祠旁边'}
        ]
        result = self.searcher.answer_prettify('地址', answers)
        
        # 期望答案以换行符分隔
        expected = "武侯祠的地址是：武侯祠大街231号。\n锦里的地址是：武侯祠旁边。"
        self.assertEqual(expected, result)
    
    def test_search_main_no_results(self):
        """测试没有查询结果的情况"""
        # 设置模拟的Neo4j查询结果为空列表
        run_mock = MagicMock()
        run_mock.data.return_value = []
        self.mock_graph_instance.run.return_value = run_mock
        
        sqls = [{'question_type': '地址', 'sql': ["MATCH (a:景点) WHERE a.name = '不存在的景点' RETURN a.name AS name, a.address AS 地址"]}]
        
        result = self.searcher.search_main(sqls)
        
        # 期望返回适当的错误信息
        self.assertIn("抱歉，没有找到", result[0])

if __name__ == '__main__':
    unittest.main()
