#!/usr/bin/env python3
# coding: utf-8
# File: test_parser.py

import unittest
import sys
import os

# 添加上级目录到路径中，使测试可以导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from question_parser import QuestionParser

class TestQuestionParser(unittest.TestCase):
    """测试问题解析器"""
    
    def setUp(self):
        """每个测试用例开始前执行，初始化解析器"""
        self.parser = QuestionParser()
    
    def test_build_entitydict(self):
        """测试实体词典构建功能"""
        test_args = {'武侯祠': ['attraction'], '都江堰': ['attraction']}
        entity_dict = self.parser.build_entitydict(test_args)
        
        # 验证构建结果
        self.assertEqual(['武侯祠', '都江堰'], entity_dict['attraction'])
    
    def test_address_query(self):
        """测试地址查询的SQL生成"""
        test_classification = {
            'args': {'武侯祠': ['attraction']},
            'question_types': ['地址']
        }
        
        result = self.parser.parser_main(test_classification)
        
        # 验证结果结构
        self.assertEqual(1, len(result))
        self.assertEqual('地址', result[0]['question_type'])
        
        # 验证生成的SQL查询
        sql = result[0]['sql'][0]
        self.assertIn("MATCH (a:景点)", sql)
        self.assertIn("a.name = '武侯祠'", sql)
        self.assertIn("RETURN a.name AS name, a.address AS 地址", sql)
    
    def test_multiple_entities(self):
        """测试多个实体的情况"""
        test_classification = {
            'args': {'武侯祠': ['attraction'], '锦里': ['attraction']},
            'question_types': ['简介']
        }
        
        result = self.parser.parser_main(test_classification)
        
        # 验证生成的SQL数量
        self.assertEqual(1, len(result))
        self.assertEqual(2, len(result[0]['sql']))
        
        # 验证每个实体都有对应的SQL
        sql_texts = result[0]['sql']
        entity_names = ['武侯祠', '锦里']
        
        for entity in entity_names:
            found = False
            for sql in sql_texts:
                if f"a.name = '{entity}'" in sql:
                    found = True
                    break
            self.assertTrue(found, f"没有为实体 '{entity}' 生成SQL")

if __name__ == '__main__':
    unittest.main()
