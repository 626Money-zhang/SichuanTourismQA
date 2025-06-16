#!/usr/bin/env python3 # 指定脚本的解释器为python3
# coding: utf-8 # 指定文件编码为UTF-8，支持中文字符
# File: question_classifier.py # 文件名
# Adapted for Tourist Attractions by: GitHub Copilot # 适配说明
# Date: 25-6-6 (Original) # 原始创建日期

import os # 导入os模块，用于处理文件和目录路径
import ahocorasick # 导入ahocorasick模块，用于高效的字符串多模式匹配
import csv # 导入csv模块，用于处理CSV文件（当前代码中并未使用，但可能为未来扩展或原始版本残留）

class QuestionClassifier: # 定义问题分类器类
    def __init__(self): # 类的初始化方法，创建类的实例时自动调用
        # 获取当前脚本所在的目录的绝对路径
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 定义词典目录路径，通常是当前脚本目录下的 'dict' 文件夹
        self.dict_dir = os.path.join(cur_dir, 'dict')
        # 检查词典目录是否存在
        if not os.path.exists(self.dict_dir):
            # 如果词典目录不存在，则尝试创建它
            try:
                os.makedirs(self.dict_dir) # 创建目录
                print(f"已创建词典目录: {self.dict_dir}") # 打印创建成功的消息
            except OSError as e: # 如果创建目录过程中发生操作系统错误
                print(f"创建词典目录 {self.dict_dir} 失败: {e}. 如果词典文件已存在于其他位置，请确保路径正确。") # 打印错误信息

        # 定义景点名称词典文件的完整路径
        self.attraction_name_path = os.path.join(self.dict_dir, 'attraction_name.txt')
        
        # 加载景点名称词典，调用 load_attraction_names 方法
        self.attraction_name_wds = self.load_attraction_names()
       
        # 定义一个景点简称到全称的映射字典
        # 用户应根据 attraction_name.txt 中的实际全称来验证和扩展此字典
        self.attraction_aliases = {
            "熊猫基地": "成都大熊猫繁育研究基地",  # 示例：将简称“熊猫基地”映射到全称
            "锦里": "锦里古街",              # 示例：将简称“锦里”映射到全称
            "都江堰": "都江堰景区",            # 示例：将简称“都江堰”映射到全称
            "宽窄巷子": "宽窄巷子" # 示例：如果简称和全称相同，或者词典中以此为准
            # 可以根据需要添加更多简称
        }

        # 构建词汇类型字典，调用 build_wdtype_dict 方法 (当前所有词典词都认为是景点)
        self.wdtype_dict = self.build_wdtype_dict()
        
        # 将景点全称和简称都加入到Aho-Corasick自动机中，用于快速匹配
        # 使用set确保词汇的唯一性，以防简称本身也是一个全称
        all_recognizable_names = list(set(list(self.attraction_name_wds) + list(self.attraction_aliases.keys())))
        
        # 构建Aho-Corasick自动机，用于高效地从问题中识别这些景点名称
        self.region_tree = self.build_actree(all_recognizable_names)

        # 定义各类问题类型的特征词列表
        self.address_qwds = ['地址', '位置', '在哪', '坐落', '方位', '哪里', '在哪儿'] # 地址相关的关键词
        self.opening_hours_qwds = ['开放时间', '几点开门', '几点关门', '营业时间', '开放到几点', '什么时候开', '什么时候关', '几点开', '几点关'] # 开放时间相关的关键词
        self.phone_qwds = ['电话', '联系方式', '号码', '订票电话', '咨询电话'] # 电话相关的关键词
        self.rating_qwds = ['评分', '评价', '怎么样', '好不好', '口碑', '值得去吗', '好玩吗', '推荐吗'] # 评分相关的关键词
        self.popularity_qwds = ['热度', '人气', '人多吗', '火不火', '热门程度', '人多不多'] # 人气相关的关键词
        self.url_qwds = ['官网', '网站', '网址', '官方网站', '链接'] # 官网相关的关键词
        self.description_qwds = ['介绍', '简介', '信息', '详情', '描述一下', '讲讲关于', '是什么', '有哪些特色', '概况', '具体情况', '说一下'] # 描述相关的关键词
        self.ticket_qwds = ['门票', '票价', '多少钱', '价格', '入场费', '费用'] # 新增门票相关的关键词

        # 否定词 (用于区分某些意图，例如“不推荐的食物”等，此处暂时保留，可能用于更复杂场景)
        self.deny_words = ['不是', '没有', '除了', '不要', '而非'] # 否定词列表

        print("旅游问答分类器模型初始化完成 ...... ") # 打印初始化完成的消息

    def load_attraction_names(self): # 定义加载景点名称词典的方法
        """
        加载景点名称词典。
        此词典应由 '数据集预处理.py' 脚本预先生成。
        增强鲁棒性：去除名称前后空格，跳过空名称。
        """
        attraction_names = set() # 使用set存储景点名称，可以自动去重
        if not os.path.exists(self.attraction_name_path): # 检查景点名称词典文件是否存在
            print(f"错误: 景点名称词典文件 {self.attraction_name_path} 未找到。") # 打印错误信息
            print(f"请先运行 '数据集预处理.py' 来生成该文件。") # 提示用户操作
            return [] # 如果文件不存在，返回空列表

        print(f"从 {self.attraction_name_path} 加载景点名称词典...") # 打印加载信息
        try: # 尝试打开并读取文件
            with open(self.attraction_name_path, 'r', encoding='utf-8') as f: # 以只读模式打开文件，指定编码为utf-8
                # 修改开始：直接迭代文件对象来按行读取
                for line in f: # 遍历文件中的每一行
                    name = line.strip() # 去除行首尾的空白字符（如换行符、空格）
                    if name: # 如果处理后的名称非空
                        attraction_names.add(name) # 将名称添加到set中
                # 修改结束
            
            if attraction_names: # 如果成功加载到景点名称
                print(f"已加载 {len(attraction_names)} 个景点名称。") # 打印加载的数量
            else: # 如果加载后set为空
                print(f"警告: 从 {self.attraction_name_path} 加载的景点名称为空。文件可能为空或格式不正确。") # 打印警告信息
                print(f"请检查文件内容或重新运行 '数据集预处理.py'。") # 提示用户检查
                return [] # 返回空列表
        except Exception as e: # 如果在读取文件过程中发生任何异常
            print(f"从文件 {self.attraction_name_path} 加载景点名称失败: {e}") # 打印错误信息和异常详情
            print(f"请检查文件格式或重新运行 '数据集预处理.py'。") # 提示用户检查
            return [] # 加载出错，返回空列表
        
        return list(attraction_names) # 将set转换为列表并返回

    def classify(self, question): # 定义问题分类的核心方法，输入参数为用户的问题字符串
        data = {} # 初始化一个空字典，用于存储分类结果
        # 从问题中提取已知的实体 (这里主要是景点名称)，调用 extract_entities 方法
        entities_dict = self.extract_entities(question)
        
        if not entities_dict: # 如果没有检测到任何已知实体（如景点名称）
            return {} # 返回空字典，表示无法处理或问题与已知景点无关
        
        data['args'] = entities_dict # 将提取出的实体及其类型存入结果字典的 'args' 键中
        
        # 收集问题中涉及到的实体类型 (当前主要是 'attraction')
        types = [] # 初始化一个空列表，用于存储实体类型
        for entity_type_list in entities_dict.values(): # 遍历实体字典中的值（每个值是一个类型列表）
            types.extend(entity_type_list) # 将每个实体的类型列表合并到总的types列表中
        
        question_types = [] # 初始化一个空列表，用于存储此问题可能属于的类型

        # 检查问题是否与已知景点相关
        if 'attraction' not in types: # 如果提取到的实体类型中不包含 'attraction'
            return {} # 返回空字典，因为当前分类器主要处理景点相关问题

        # --- 开始分类逻辑 ---

        # 检查问题是否询问景点地址
        if self.check_words(self.address_qwds, question): # 调用 check_words 方法，判断地址关键词是否存在于问题中
            question_types.append('地址') # 如果存在，将'地址'添加到问题类型列表中

        # 检查问题是否询问景点开放时间
        if self.check_words(self.opening_hours_qwds, question): # 判断开放时间关键词是否存在
            question_types.append('开放时间') # 如果存在，添加'开放时间'

        # 检查问题是否询问景点电话
        if self.check_words(self.phone_qwds, question): # 判断电话关键词是否存在
            question_types.append('电话') # 如果存在，添加'电话'
            
        # 检查问题是否询问景点评分/评价
        if self.check_words(self.rating_qwds, question): # 判断评分关键词是否存在
            question_types.append('评分') # 如果存在，添加'评分'

        # 检查问题是否询问景点热度/人气
        if self.check_words(self.popularity_qwds, question): # 判断人气关键词是否存在
            question_types.append('热度') # 如果存在，添加'热度'
            
        # 检查问题是否询问景点网址
        if self.check_words(self.url_qwds, question): # 判断官网关键词是否存在
            question_types.append('官网') # 如果存在，添加'官网' (对应CSV中的“官网”)
        
        # 新增：检查问题是否询问景点门票
        if self.check_words(self.ticket_qwds, question): # 判断门票关键词是否存在
            question_types.append('门票价格') # 如果存在，添加'门票价格' (对应CSV中的“门票价格”)

        # 如果没有匹配到以上具体问题类型，但提到了景点，且包含描述性疑问词，则归类为查询描述
        if not question_types and self.check_words(self.description_qwds, question): # 如果之前未匹配到类型，且包含描述性词汇
            question_types.append('简介') # 添加'简介' (对应CSV中的“简介”)
        
        # 如果仍然没有匹配，但问题中包含景点名称，则默认为查询景点描述
        if not question_types and 'attraction' in types: # 如果之前未匹配到类型，但识别出景点
            question_types.append('简介') # 默认查询描述，添加'简介' (对应CSV中的“简介”)

        data['question_types'] = list(set(question_types)) # 对问题类型列表去重，并存入结果字典的 'question_types' 键
        return data # 返回包含实体和问题类型的分类结果字典

    def build_wdtype_dict(self): # 定义构建词汇及其对应类型字典的方法
        """
        构建词汇及其对应类型的字典。
        当前场景下，所有 self.attraction_name_wds 都属于 'attraction' 类型。
        """
        wd_dict = {} # 初始化一个空字典
        for wd in self.attraction_name_wds: # 遍历加载的景点名称列表 (self.attraction_name_wds)
            wd_dict[wd] = ['attraction'] # 将每个景点名称映射到一个类型列表 ['attraction']
        return wd_dict # 返回构建好的词汇类型字典

    def build_actree(self, wordlist): # 定义构建Aho-Corasick自动机的方法，输入参数为词汇列表
        """
        构造Aho-Corasick自动机，用于快速从文本中匹配词汇表中的词。
        确保添加到自动机的词是字符串且非空。
        """
        actree = ahocorasick.Automaton() # 创建一个Aho-Corasick自动机实例
        valid_words_count = 0 # 初始化有效词汇计数器
        if not wordlist: # 如果传入的词汇列表为空
            print("警告: 传入 build_actree 的词汇列表为空。自动机将为空。") # 打印警告信息
            return actree # 返回一个空的自动机

        for index, word in enumerate(wordlist): # 遍历词汇列表中的每个词及其索引
            if isinstance(word, str) and word.strip(): # 检查词是否为字符串类型，并且去除首尾空格后非空
                actree.add_word(word.strip(), (index, word.strip())) # 将处理后的词添加到自动机中，同时存储其原始索引和词本身
                valid_words_count +=1 # 有效词汇计数加1
            elif isinstance(word, str) and not word.strip(): # 如果是字符串但去除空格后为空
                print(f"警告: 跳过空字符串或纯空格的词汇: '{word}'") # 打印警告
            elif not isinstance(word, str): # 如果词不是字符串类型
                print(f"警告: 跳过非字符串类型的词汇: {word} (类型: {type(word)})") # 打印警告

        if valid_words_count > 0: # 如果有有效词汇被添加到自动机
            actree.make_automaton() # 完成自动机的构建，使其可以用于匹配
            print(f"Aho-Corasick 自动机构建完成，包含 {valid_words_count} 个有效词汇。") # 打印成功信息
        else: # 如果没有有效词汇
            print("警告: 没有有效的词汇添加到Aho-Corasick自动机。") # 打印警告
        return actree # 返回构建好的自动机

    def extract_entities(self, question): # 定义从问题中提取实体的方法，输入参数为用户的问题字符串
        attraction_entities = {} # 初始化一个空字典，用于存储提取到的景点实体
        
        raw_matches = [] # 初始化一个列表，用于存储Aho-Corasick自动机匹配到的原始词汇
        if not hasattr(self, 'region_tree') or self.region_tree is None: # 检查自动机是否已初始化
            return attraction_entities # 如果未初始化，返回空字典

        # 使用Aho-Corasick自动机在问题中查找所有匹配的词汇
        for end_index, (original_index, word) in self.region_tree.iter(question): # 遍历匹配结果
            raw_matches.append(word) # 将匹配到的词（即景点名称）添加到raw_matches列表
        
        if not raw_matches: # 如果没有匹配到任何词汇
            return attraction_entities # 返回空字典

        # 进行最长匹配处理：如果一个短词是另一个长词的子串，则只保留长词
        stop_wds = [] # 初始化一个列表，用于存储需要被移除的短词（子串）
        for wd1 in raw_matches: # 遍历所有匹配到的词
            for wd2 in raw_matches: # 再次遍历所有匹配到的词，进行两两比较
                if wd1 in wd2 and wd1 != wd2: # 如果wd1是wd2的子串，并且它们不相等
                    stop_wds.append(wd1) # 将wd1（短词）添加到stop_wds列表
        
        # 从原始匹配结果中移除作为子串的短词，得到最终的实体词汇列表
        final_wds = [i for i in raw_matches if i not in stop_wds]

        # 将最终识别出的景点名称及其类型（默认为'attraction'）存入attraction_entities字典
        for attraction_name in final_wds: # 遍历最终的实体词汇列表
            # 从wdtype_dict获取类型，如果找不到，默认为['attraction']
            attraction_entities[attraction_name] = self.wdtype_dict.get(attraction_name, ['attraction']) 
        
        # 处理简称，将其转换回全称
        final_entities = {} # 初始化一个新字典，用于存储处理简称后的最终实体
        for entity_name, entity_types in attraction_entities.items(): # 遍历之前提取的实体（可能包含简称）
            # 如果识别出的实体是简称（在attraction_aliases中存在），则使用其对应的全称
            # 否则，直接使用识别出的实体名称
            full_name = self.attraction_aliases.get(entity_name, entity_name)
            # 更新实体字典，确保键是全称
            # 如果全称已存在（例如，问题中同时提到了简称和全称），则合并类型（当前类型都是'attraction'，但为未来扩展保留）
            if full_name in final_entities: # 如果全称已在最终实体字典中
                final_entities[full_name] = list(set(final_entities[full_name] + entity_types)) # 合并类型并去重
            else: # 如果全称不在最终实体字典中
                final_entities[full_name] = entity_types # 直接添加

        return final_entities # 返回处理简称后的最终实体字典

    def check_words(self, words_to_check, sentence): # 定义检查词汇是否在句子中存在的方法
        """
        检查 `words_to_check` 列表中的任一词汇是否存在于 `sentence` 中。
        """
        for word in words_to_check: # 遍历待检查的词汇列表
            if word in sentence: # 如果当前词汇存在于句子中
                return True # 返回True，表示找到了
        return False # 如果遍历完所有词汇都没有找到，则返回False

if __name__ == '__main__': # Python的入口点，当脚本直接执行时，以下代码块会运行
    # 初始化分类器
    classifier = QuestionClassifier() # 创建QuestionClassifier类的实例
    
    # 测试用例列表，包含多个不同类型的问题
    test_questions = [
        "武侯祠的地址是什么？",
        "成都欢乐谷几点开门？",
        "熊猫基地的电话号码是多少？",
        "锦里怎么样？",
        "春熙路的人气如何？",
        "宽窄巷子的官网链接有吗？",
        "介绍一下都江堰。",
        "青城山在哪里，什么时候开放？", # 可能会匹配多个类型，取决于实现
        "北京故宫的评分是多少？", # 包含非四川景点，但如果"故宫"在词典中也会识别
        "我想知道关于杜甫草堂的信息",
        "春熙路好不好玩",
        "天府广场", # 仅实体，应归类为描述
        "熊猫基地的门票多少钱？" # 新增测试门票问题
    ]

    for question_text in test_questions: # 遍历测试问题列表
        print(f"\\n提问: {question_text}") # 打印当前测试的问题
        classification_result = classifier.classify(question_text) # 调用分类器的classify方法进行分类
        print(f"分类结果: {classification_result}") # 打印分类结果

    print("\\n进入交互式提问模式 (输入 '退出' 来结束):") # 提示进入交互模式
    while True: # 开始一个无限循环，用于接收用户输入
        user_question = input("请输入您关于四川景点的问题: ") # 获取用户输入的问题
        if user_question.lower() == '退出': # 如果用户输入'退出'（不区分大小写）
            break # 跳出循环，结束程序
        classification_result = classifier.classify(user_question) # 对用户输入的问题进行分类
        print(f"分类结果: {classification_result}") # 打印分类结果
