#!/usr/bin/env python3 # 指定脚本的解释器为python3
# coding: utf-8 # 指定文件的编码格式为utf-8
# File: question_parser.py # 文件名
# Date: 25-6-6 (Original) # 原始日期

class QuestionParser: # Renamed class to follow Python conventions (PascalCase) # 定义一个名为QuestionParser的类，遵循Python的命名规范（帕斯卡命名法）

    def build_entitydict(self, args): # 定义一个方法，用于构建实体字典
        """
        构建实体字典。
        输入: args - {'实体词': ['类型1', '类型2'], ...} 例如: {'武侯祠': ['attraction']}
        输出: entity_dict - {'类型': ['实体词1', '实体词2'], ...} 例如: {'attraction': ['武侯祠']}
        """ # 方法的文档字符串，说明其功能、输入和输出
        entity_dict = {} # 初始化一个空字典，用于存储实体信息
        for arg, types in args.items(): # 遍历输入的args字典，arg是实体词，types是该实体词对应的类型列表
            for entity_type in types: # Renamed 'type' to 'entity_type' to avoid conflict with built-in # 遍历实体词的类型列表，将类型重命名为entity_type以避免与内置的type冲突
                if entity_type not in entity_dict: # 如果当前实体类型不在entity_dict中
                    entity_dict[entity_type] = [arg] # 将实体类型作为键，实体词列表作为值存入字典
                else: # 如果当前实体类型已存在于entity_dict中
                    entity_dict[entity_type].append(arg) # 将当前实体词追加到对应类型的实体词列表中
        return entity_dict # 返回构建好的实体字典

    def parser_main(self, res_classify): # 定义解析主函数
        """
        解析主函数。
        输入: res_classify - QuestionClassifier的输出结果，
                           包含 'args' (提取的实体) 和 'question_types' (问题类型列表)
        输出: sqls - 一个列表，每个元素是一个包含 'question_type' 和 'sql' (Cypher查询语句列表) 的字典
        """ # 方法的文档字符串，说明其功能、输入和输出
        args = res_classify.get('args', {}) # 从分类结果中获取'args'（提取的实体），如果不存在则默认为空字典
        entity_dict = self.build_entitydict(args) # 调用build_entitydict方法构建实体字典
        question_types = res_classify.get('question_types', []) # 从分类结果中获取'question_types'（问题类型列表），如果不存在则默认为空列表
        
        sqls = [] # 初始化一个空列表，用于存储生成的Cypher查询语句信息
        # 获取景点实体，后续查询都基于此 # 获取类型为'attraction'的实体列表，这些是后续查询的基础
        attraction_entities = entity_dict.get('attraction', []) # 从实体字典中获取'attraction'类型的实体列表，如果不存在则默认为空列表

        if not attraction_entities: # 如果没有识别到景点实体，则无法生成查询 # 如果没有景点实体
            return sqls # 直接返回空的sqls列表

        for question_type in question_types: # 遍历问题类型列表中的每一个问题类型
            sql_entry = {'question_type': question_type} # 为当前问题类型创建一个字典条目，包含问题类型本身
            generated_sql_queries = [] # To store Cypher queries for this question_type # 初始化一个空列表，用于存储针对当前问题类型生成的Cypher查询语句

            # 根据问题类型调用sql_transfer生成Cypher查询 # 调用sql_transfer方法生成Cypher查询
            # 注意：sql_transfer现在将处理单个问题类型和所有相关实体 # 注意sql_transfer方法会处理单个问题类型和所有相关的实体
            generated_sql_queries = self.sql_transfer(question_type, attraction_entities) # 调用sql_transfer方法，传入当前问题类型和景点实体列表
            
            if generated_sql_queries: # 如果成功生成了Cypher查询语句
                sql_entry['sql'] = generated_sql_queries # 将生成的查询语句列表存入当前sql_entry字典的'sql'键下
                sqls.append(sql_entry) # 将当前sql_entry字典追加到sqls列表中
        
        return sqls # 返回包含所有生成查询信息的sqls列表

    def sql_transfer(self, question_type, entities): # 定义一个方法，用于根据问题类型和实体列表生成Cypher查询语句
        """
        根据问题类型和实体列表，生成相应的Cypher查询语句。
        输入:
            question_type - 单个问题类型字符串 (例如 '地址')
            entities - 与该问题类型相关的实体列表 (例如 ['武侯祠', '锦里'])
        输出:
            sql - 生成的Cypher查询语句列表
        """ # 方法的文档字符串，说明其功能、输入和输出
        if not entities: # 如果实体列表为空
            return [] # 返回一个空列表

        sql = [] # Initialize list for Cypher queries # 初始化一个空列表，用于存储生成的Cypher查询语句

        # Neo4j中景点节点的标签是 "景点", 名称属性是 "name" # Neo4j数据库中景点节点的标签是"景点"，名称属性是"name"
        # 其他属性名直接对应三元组中的谓词，例如: 地址, 开放时间, 门票价格, 简介等. # 其他属性名直接对应三元组中的谓词，例如：地址、开放时间、门票价格、简介等

        if question_type == '地址': # 如果问题类型是'地址'
            sql = [f"MATCH (a:景点) WHERE a.name = '{entity}' RETURN a.name AS name, a.address AS 地址" for entity in entities] # 为每个实体生成查询其地址的Cypher语句
        
        elif question_type == '开放时间': # 如果问题类型是'开放时间'
            sql = [f"MATCH (a:景点) WHERE a.name = '{entity}' RETURN a.name AS name, a.openingTime AS 开放时间" for entity in entities] # 为每个实体生成查询其开放时间的Cypher语句

        elif question_type == '电话': # 如果问题类型是'电话'
            sql = [f"MATCH (a:景点) WHERE a.name = '{entity}' RETURN a.name AS name, a.phone AS 电话" for entity in entities] # 为每个实体生成查询其电话的Cypher语句

        elif question_type == '评分': # 如果问题类型是'评分'
            sql = [f"MATCH (a:景点) WHERE a.name = '{entity}' RETURN a.name AS name, a.rating AS 评分" for entity in entities] # 为每个实体生成查询其评分的Cypher语句

        elif question_type == '热度': # 如果问题类型是'热度'
            sql = [f"MATCH (a:景点) WHERE a.name = '{entity}' RETURN a.name AS name, a.popularity AS 热度" for entity in entities] # 为每个实体生成查询其热度的Cypher语句

        elif question_type == '官网': # 如果问题类型是'官网'
            sql = [f"MATCH (a:景点) WHERE a.name = '{entity}' RETURN a.name AS name, a.website AS 官网" for entity in entities] # 为每个实体生成查询其官网的Cypher语句
        
        elif question_type == '门票价格': # Assuming '门票价格' refers to discount policy # 如果问题类型是'门票价格'（假设这里指的是优待政策）
            sql = [f"MATCH (a:景点) WHERE a.name = '{entity}' RETURN a.name AS name, a.discountPolicy AS 门票价格" for entity in entities] # 为每个实体生成查询其优待政策（作为门票价格）的Cypher语句

        elif question_type == '简介': # This is also the default type from classifier # 如果问题类型是'简介'（这也是分类器的默认类型）
            sql = [f"MATCH (a:景点) WHERE a.name = '{entity}' RETURN a.name AS name, a.introduction AS introduction" for entity in entities] # 为每个实体生成查询其简介的Cypher语句
        
        # 可以根据需要添加更多问题类型的处理逻辑 # 可以根据需要添加更多问题类型的处理逻辑
        # 例如，如果以后有查询景点所属城市的需求： # 例如，如果以后有查询景点所属城市的需求：
        # elif question_type == '所属城市': # 如果问题类型是'所属城市'
        #     sql = [f"MATCH (a:景点 {{name: '{entity}'}})-[:属于城市]->(c:城市) RETURN a.name AS name, c.name AS 所属城市" for entity in entities] # 为每个实体生成查询其所属城市的Cypher语句

        return sql # 返回生成的Cypher查询语句列表

if __name__ == '__main__': # 如果当前脚本是作为主程序运行
    # 这是一个示例，展示如何使用 QuestionParser # 这是一个示例，展示如何使用QuestionParser
    # 实际应用中，你会先用 QuestionClassifier 分类问题，然后将其结果传给 QuestionParser # 实际应用中，你会先用QuestionClassifier分类问题，然后将其结果传给QuestionParser

    # 假设 QuestionClassifier 的输出如下 (使用新的中文问题类型): # 假设QuestionClassifier的输出如下（使用新的中文问题类型）:
    sample_classification_result_1 = { # 定义第一个示例分类结果
        'args': {'武侯祠': ['attraction']}, # 提取到的实体及其类型
        'question_types': ['地址', '开放时间']  # 问题类型列表
    }
    sample_classification_result_2 = { # 定义第二个示例分类结果
        'args': {'锦里': ['attraction']}, # 提取到的实体及其类型
        'question_types': ['评分'] # 问题类型列表
    }
    sample_classification_result_3 = { # 定义第三个示例分类结果
        'args': {'成都欢乐谷': ['attraction']}, # 提取到的实体及其类型
        'question_types': ['简介'] # Classifier defaults to '简介' for general queries # 问题类型列表（分类器对一般查询默认为'简介'）
    }
    sample_classification_result_4 = { # 无有效景点实体 # 定义第四个示例分类结果（无有效景点实体）
        'args': {'北京': ['city']},  # 提取到的实体及其类型
        'question_types': ['city_description'] # 假设的类型，当前解析器不处理 # 问题类型列表（假设的类型，当前解析器不处理）
    }
    sample_classification_result_5 = { # 景点实体，但问题类型未知 (对于此解析器) # 定义第五个示例分类结果（景点实体，但问题类型未知）
        'args': {'杜甫草堂': ['attraction']}, # 提取到的实体及其类型
        'question_types': ['unknown_query']  # 问题类型列表
    }
    sample_classification_result_6 = { # 定义第六个示例分类结果
        'args': {'熊猫基地': ['attraction']}, # 提取到的实体及其类型
        'question_types': ['门票价格', '电话'] # 问题类型列表
    }

    parser = QuestionParser() # 创建QuestionParser类的实例

    print("--- 测试用例 1 (武侯祠的地址和开放时间) ---") # 打印测试用例1的标题
    sqls_1 = parser.parser_main(sample_classification_result_1) # 调用parser_main方法处理第一个示例分类结果
    for sql_entry in sqls_1: # 遍历生成的SQL条目列表
        print(f"  问题类型: {sql_entry['question_type']}") # 打印问题类型
        for cypher_query in sql_entry['sql']: # 遍历该问题类型下的Cypher查询语句列表
            print(f"    Cypher: {cypher_query}") # 打印Cypher查询语句

    print("\\n--- 测试用例 2 (锦里的评分) ---") # 打印测试用例2的标题
    sqls_2 = parser.parser_main(sample_classification_result_2) # 调用parser_main方法处理第二个示例分类结果
    for sql_entry in sqls_2: # 遍历生成的SQL条目列表
        print(f"  问题类型: {sql_entry['question_type']}") # 打印问题类型
        for cypher_query in sql_entry['sql']: # 遍历该问题类型下的Cypher查询语句列表
            print(f"    Cypher: {cypher_query}") # 打印Cypher查询语句
            
    print("\\n--- 测试用例 3 (成都欢乐谷的简介) ---") # 打印测试用例3的标题
    sqls_3 = parser.parser_main(sample_classification_result_3) # 调用parser_main方法处理第三个示例分类结果
    for sql_entry in sqls_3: # 遍历生成的SQL条目列表
        print(f"  问题类型: {sql_entry['question_type']}") # 打印问题类型
        for cypher_query in sql_entry['sql']: # 遍历该问题类型下的Cypher查询语句列表
            print(f"    Cypher: {cypher_query}") # 打印Cypher查询语句

    print("\\n--- 测试用例 4 (无景点实体) ---") # 打印测试用例4的标题
    sqls_4 = parser.parser_main(sample_classification_result_4) # 调用parser_main方法处理第四个示例分类结果
    if not sqls_4: # 如果没有生成SQL查询
        print("  未生成Cypher查询 (符合预期，因为没有景点实体或相关问题类型未被处理)。") # 打印未生成查询的提示（符合预期）
    else: # 如果生成了SQL查询
        for sql_entry in sqls_4: # 遍历生成的SQL条目列表
            print(f"  问题类型: {sql_entry['question_type']}") # 打印问题类型
            for cypher_query in sql_entry['sql']: # 遍历该问题类型下的Cypher查询语句列表
                print(f"    Cypher: {cypher_query}") # 打印Cypher查询语句

    print("\\n--- 测试用例 5 (未知问题类型) ---") # 打印测试用例5的标题
    sqls_5 = parser.parser_main(sample_classification_result_5) # 调用parser_main方法处理第五个示例分类结果
    if not any(entry.get('sql') for entry in sqls_5): # Check if any entry actually has SQL # 检查是否有任何条目实际包含SQL查询
        print("  未生成Cypher查询 (符合预期，因为问题类型 'unknown_query' 未被处理)。") # 打印未生成查询的提示（符合预期）
    else: # 如果生成了SQL查询
         for sql_entry in sqls_5: # 遍历生成的SQL条目列表
            print(f"  问题类型: {sql_entry['question_type']}") # 打印问题类型
            if 'sql' in sql_entry and sql_entry['sql']: # 如果条目中包含'sql'键且其值不为空
                 for cypher_query in sql_entry['sql']: # 遍历该问题类型下的Cypher查询语句列表
                    print(f"    Cypher: {cypher_query}") # 打印Cypher查询语句
            else: # 如果条目中没有有效的SQL查询
                print(f"    未针对此类型 '{sql_entry['question_type']}' 生成Cypher查询。") # 打印未针对此类型生成查询的提示

    print("\\n--- 测试用例 6 (熊猫基地的门票价格和电话) ---") # 打印测试用例6的标题
    sqls_6 = parser.parser_main(sample_classification_result_6) # 调用parser_main方法处理第六个示例分类结果
    for sql_entry in sqls_6: # 遍历生成的SQL条目列表
        print(f"  问题类型: {sql_entry['question_type']}") # 打印问题类型
        for cypher_query in sql_entry['sql']: # 遍历该问题类型下的Cypher查询语句列表
            print(f"    Cypher: {cypher_query}") # 打印Cypher查询语句