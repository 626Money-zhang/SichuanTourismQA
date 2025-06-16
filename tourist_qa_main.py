# coding: utf-8 # 指定文件的编码格式为utf-8
from question_classifier import QuestionClassifier # 从question_classifier模块导入QuestionClassifier类
from question_parser import QuestionParser # 从question_parser模块导入QuestionParser类
from answer_search import AnswerSearcher # 从answer_search模块导入AnswerSearcher类

class TouristQABot: # 定义一个名为TouristQABot的类
    def __init__(self): # 定义类的构造函数
        """
        初始化问答机器人，加载分类器、解析器和搜索器。
        """ # 方法的文档字符串，说明其功能
        self.classifier = QuestionClassifier() # 创建QuestionClassifier类的实例，并赋值给self.classifier属性
        self.parser = QuestionParser() # 创建QuestionParser类的实例，并赋值给self.parser属性
        self.searcher = AnswerSearcher() # 创建AnswerSearcher类的实例，并赋值给self.searcher属性
        print("问答机器人初始化完成。") # 打印问答机器人初始化完成的提示信息

    def chat(self): # 定义chat方法，用于启动与用户的聊天交互
        """
        启动与用户的聊天循环。
        """ # 方法的文档字符串，说明其功能
        print("\n您好！我是四川旅游问答机器人。") # 打印欢迎信息
        print("您可以问我关于四川景点的问题，例如：") # 打印提问示例的引导信息
        print(" - \"武侯祠的地址是什么？\"") # 打印提问示例1
        print(" - \"九寨沟的开放时间？\"") # 打印提问示例2
        print(" - \"都江堰的评分怎么样？\"") # 打印提问示例3
        print(" - \"峨眉山有哪些信息？\"") # 打印提问示例4
        print("输入 '退出', '再见', 'exit' 或 'quit' 可以结束对话。\n") # 打印退出对话的提示信息
        
        while True: # 开始一个无限循环，用于持续接收用户输入并进行问答
            try: # 尝试执行以下代码块
                question = input("用户: ") # 获取用户输入的问题，并提示输入者为"用户"
                if question.lower() in ['退出', '再见', 'exit', 'quit']: # 将用户输入转换为小写，并检查是否为退出指令
                    print("机器人: 感谢您的使用，再见！") # 如果是退出指令，打印感谢信息并准备退出
                    break # 跳出while循环，结束对话
                
                if not question.strip(): # 如果用户输入去除两端空白后为空字符串
                    print("机器人: 请输入您的问题。") # 提示用户输入问题
                    continue # 跳过当前循环的剩余部分，继续等待下一次用户输入

                # 1. 问题分类 # 第一步：对用户的问题进行分类
                # classify 方法期望一个问题字符串，返回一个包含 'question_types' 和 'args' 的字典 # classify方法的输入和输出说明
                # 例如: {'args': {'武侯祠': ['attraction']}, 'question_types': ['attraction_address']} # classify方法输出的示例
                res_classify = self.classifier.classify(question) # 调用分类器的classify方法对问题进行分类
                
                if not res_classify or not res_classify.get('question_types'): # 如果分类结果为空，或者分类结果中没有'question_types'键
                    print("机器人: 抱歉，我暂时无法理解您的问题类型。可以换个问法试试吗？") # 打印无法理解问题类型的提示
                    continue # 继续下一次循环

                # 2. 问题解析 -> Cypher查询语句 # 第二步：将分类后的问题解析成Cypher查询语句
                # parser_main 方法期望分类结果，返回一个包含Cypher查询语句的列表 # parser_main方法的输入和输出说明
                # 例如: [{'question_type': 'attraction_address', 'sql': ["MATCH (a:景点) WHERE a.name = '武侯祠' RETURN a.name, a.address"]}] # parser_main方法输出的示例
                sqls = self.parser.parser_main(res_classify) # 调用解析器的parser_main方法，将分类结果转换为Cypher查询语句
                
                if not sqls:  # 如果解析后没有生成有效的SQL查询语句
                    # parser_main 在无法生成sql时可能返回空列表或None，这里统一处理 # parser_main在无法生成sql时可能返回空列表或None，这里统一处理
                    # 尝试从分类结果中获取实体名称，用于更友好的提示 # 尝试从分类结果中获取实体名称，用于更友好的提示
                    entity_names = list(res_classify.get('args', {}).keys()) # 获取分类结果中提取到的实体名称列表
                    if entity_names: # 如果成功获取到实体名称
                        print(f"机器人: 抱歉，我无法为“{entity_names[0]}”相关的问题构建有效的查询。") # 打印针对特定实体的无法构建查询的提示
                    else: # 如果没有获取到实体名称
                        print("机器人: 抱歉，我无法为这个问题构建有效的查询。") # 打印通用的无法构建查询的提示
                    continue # 继续下一次循环
                    
                # 3. 执行查询并获取答案 # 第三步：执行Cypher查询并获取答案
                # search_main 方法期望Cypher查询语句列表，返回格式化后的答案列表 # search_main方法的输入和输出说明
                final_answers = self.searcher.search_main(sqls) # 调用搜索器的search_main方法，执行查询并获取格式化后的答案
                
                if not final_answers: # 如果没有找到最终答案
                    # search_main 内部已经处理了查询无结果的情况，并可能返回如 "抱歉，没有找到..." 的信息 # search_main内部已经处理了查询无结果的情况，并可能返回如 "抱歉，没有找到..." 的信息
                    # 如果 final_answers 仍然是空列表，表示可能所有查询都没有有效结果或未能美化 # 如果final_answers仍然是空列表，表示可能所有查询都没有有效结果或未能美化
                    # 尝试从分类结果中获取实体名称 # 尝试从分类结果中获取实体名称
                    entity_names = list(res_classify.get('args', {}).keys()) # 获取实体名称列表
                    # question_types已经是中文列表，例如 ['地址', '开放时间'] # question_types已经是中文列表，例如 ['地址', '开放时间']
                    question_types_str = ", ".join(res_classify.get('question_types', [])) # 获取问题类型字符串，用逗号分隔
                    
                    if entity_names: # 如果存在实体名称
                        # entity_names[0] 获取第一个识别到的实体名用于提示 # entity_names[0] 获取第一个识别到的实体名用于提示
                        print(f"机器人: 抱歉，对于“{entity_names[0]}”的“{question_types_str}”问题，我没有找到相关信息。") # 打印针对特定实体和问题类型的未找到信息提示
                    elif question_types_str: # 如果有识别出的问题类型但没有实体 # 如果有识别出的问题类型但没有实体
                        print(f"机器人: 抱歉，对于“{question_types_str}”类问题，我没有找到相关信息。") # 打印针对特定问题类型的未找到信息提示
                    else: # 如果连问题类型都未能明确（理论上前面已处理，但作为兜底） # 如果连问题类型都未能明确（理论上前面已处理，但作为兜底）
                        print("机器人: 抱歉，我没有找到相关信息。请尝试其他问题。") # 打印通用的未找到信息提示

                else: # 如果找到了最终答案
                    for ans in final_answers: # 遍历最终答案列表中的每一个答案
                        print(f"机器人: {ans}") # 打印机器人回复的答案
                print("-" * 30) # 分隔符 # 打印分隔符，用于区分不同的问答轮次

            except EOFError: # 处理Ctrl+D等输入结束的情况 # 如果捕获到EOFError（例如用户按下Ctrl+D）
                print("\n机器人: 检测到输入结束，感谢您的使用，再见！") # 打印检测到输入结束的提示
                break # 跳出while循环，结束对话
            except KeyboardInterrupt: # 处理Ctrl+C中断 # 如果捕获到KeyboardInterrupt（例如用户按下Ctrl+C）
                print("\n机器人: 对话已中断，感谢您的使用，再见！") # 打印对话已中断的提示
                break # 跳出while循环，结束对话
            except Exception as e: # 如果在处理过程中发生其他任何未被捕获的异常
                print(f"机器人: 处理您的问题时发生了一个错误：{e}。请尝试其他问题。") # 打印发生错误的提示，并显示异常信息

if __name__ == '__main__': # 如果当前脚本是作为主程序直接运行（而不是被其他模块导入）
    bot = TouristQABot() # 创建TouristQABot类的实例
    bot.chat() # 调用bot实例的chat方法，开始问答交互
