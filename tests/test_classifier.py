#!/usr/bin/env python3
# coding: utf-8
# File: test_classifier.py

import unittest
import sys
import os

# 添加上级目录到路径中，使测试可以导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from question_classifier import QuestionClassifier

class TestQuestionClassifier(unittest.TestCase):
    """测试问题分类器"""
    
    def setUp(self):
        """每个测试用例开始前执行，初始化分类器"""
        self.classifier = QuestionClassifier()
    
    def test_attraction_address(self):
        """测试地址类问题的分类"""
        test_question = "武侯祠的地址是什么？"
        result = self.classifier.classify(test_question)
        
        # 验证结果包含预期的字段
        self.assertIn('args', result)
        self.assertIn('question_types', result)
        
        # 验证实体识别
        self.assertIn('武侯祠', result['args'])
        self.assertEqual(['attraction'], result['args']['武侯祠'])
        
        # 验证问题类型
        self.assertIn('地址', result['question_types'])
    
    def test_opening_hours(self):
        """测试开放时间类问题的分类"""
        test_question = "都江堰景区什么时候开门？"
        result = self.classifier.classify(test_question)
        
        self.assertIn('args', result)
        self.assertIn('question_types', result)
        
        # 验证实体识别
        self.assertIn('都江堰景区', result['args'])
        
        # 验证问题类型
        self.assertIn('开放时间', result['question_types'])
    
    def test_no_entity(self):
        """测试没有有效实体的情况"""
        test_question = "四川有哪些好吃的？"
        result = self.classifier.classify(test_question)
        
        # 期望结果中没有识别出景点实体，且问题类型为空列表
        self.assertEqual({}, result.get('args', {}))
        self.assertEqual([], result.get('question_types', []))

if __name__ == '__main__':
    unittest.main()
