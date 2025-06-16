import csv # 导入csv模块，用于处理CSV文件
import os # 导入os模块，用于与操作系统交互，例如文件路径操作
from py2neo import Graph, Node, Relationship # 从py2neo库导入Graph、Node和Relationship类，用于操作Neo4j数据库

# Neo4j 连接信息 (请根据你的设置修改) # Neo4j数据库的连接配置信息
NEO4J_URI = "bolt://localhost:7687" # Neo4j数据库的URI地址
NEO4J_USER = "neo4j" # Neo4j数据库的用户名
NEO4J_PASSWORD = "neo4j"  # 修改为你的Neo4j密码 # Neo4j数据库的密码，需要根据实际情况修改

# 确定CSV文件的绝对路径 # 获取CSV文件的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__)) # 获取当前脚本文件所在的目录的绝对路径
# 确保读取的是三元组文件 # 指定要读取的CSV文件名
input_csv_path = os.path.join(script_dir, '景点知识图谱_三元组.csv') # 构建输入CSV文件的完整绝对路径

# Helper to convert predicate to Neo4j property name and determine type # 辅助函数，用于将谓语转换为Neo4j属性名并确定其类型
def get_property_details(predicate): # 定义一个函数，根据谓语获取属性的详细信息（键名和类型）
    """将谓语映射到Neo4j属性键名和期望类型""" # 函数的文档字符串，说明其功能
    mapping = { # 定义一个字典，存储谓语到Neo4j属性键名和类型的映射关系
        "位于": {"key": "address", "type": str}, # "位于" 对应属性键 "address"，类型为字符串
        "的评分是": {"key": "rating", "type": float}, # "的评分是" 对应属性键 "rating"，类型为浮点数
        "的热度为": {"key": "popularity", "type": float}, # "的热度为" 对应属性键 "popularity"，类型为浮点数
        "的开放时间为": {"key": "openingTime", "type": str}, # "的开放时间为" 对应属性键 "openingTime"，类型为字符串
        "的官方电话是": {"key": "phone", "type": str}, # "的官方电话是" 对应属性键 "phone"，类型为字符串
        "的介绍是": {"key": "introduction", "type": str}, # "的介绍是" 对应属性键 "introduction"，类型为字符串
        "的优待政策是": {"key": "discountPolicy", "type": str}, # "的优待政策是" 对应属性键 "discountPolicy"，类型为字符串
        "的服务设施包括": {"key": "facilities", "type": str}, # "的服务设施包括" 对应属性键 "facilities"，类型为字符串
        "的URL是": {"key": "website", "type": str} # "的URL是" 对应属性键 "website"，类型为字符串
    }
    return mapping.get(predicate) # 返回与给定谓语匹配的属性详细信息，如果未找到则返回None

def import_triplets_to_neo4j(): # 定义一个函数，用于将三元组数据导入到Neo4j数据库
    """
    从三元组CSV文件导入数据到Neo4j数据库。
    创建节点和关系。
    """ # 函数的文档字符串，说明其功能和目的
    try: # 尝试执行以下代码块
        graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) # 创建一个Graph对象，连接到Neo4j数据库，使用指定的URI和认证信息
        graph.run("RETURN 1") # Test connection # 执行一个简单的Cypher查询来测试数据库连接
        print(f"成功连接到 Neo4j 数据库: {NEO4J_URI}") # 如果连接成功，打印成功连接的提示信息
    except Exception as e: # 如果在尝试连接数据库时发生任何异常
        print(f"无法连接到 Neo4j 数据库: {e}") # 打印无法连接数据库的错误信息，并显示异常详情
        print("请确保 Neo4j 服务正在运行，并且连接信息正确。") # 提示用户检查Neo4j服务状态和连接配置
        return # 结束函数的执行

    # 创建约束以提高性能和确保数据唯一性 # 在数据库中创建约束，以优化查询性能并保证节点名称的唯一性
    try: # 尝试执行以下代码块
        graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (j:景点) REQUIRE j.name IS UNIQUE") # 创建或确保存在一个约束：对于所有标签为"景点"的节点j，其name属性必须是唯一的
        graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:城市) REQUIRE c.name IS UNIQUE") # 创建或确保存在一个约束：对于所有标签为"城市"的节点c，其name属性必须是唯一的
        print("已确保景点和城市名称的唯一性约束存在或已创建。") # 打印约束已成功创建或已存在的提示信息
    except Exception as e: # 如果在创建约束时发生任何异常
        print(f"创建约束时出错 (可能是权限问题或约束已存在且有冲突，可忽略): {e}") # 打印创建约束时发生的错误信息，并提示可能的原因

    count_triplets_processed = 0 # 初始化已处理的三元组计数器为0
    count_nodes_created = 0 # A rough counter, MERGE handles actual creation # 初始化已创建的节点计数器为0（这是一个粗略的计数，因为MERGE操作会处理实际的创建逻辑）
    count_rels_created = 0 # 初始化已创建的关系计数器为0

    try: # 尝试执行以下代码块
        with open(input_csv_path, 'r', encoding='utf-8-sig') as csvfile: # 以只读模式打开指定的CSV文件，使用'utf-8-sig'编码以正确处理可能存在的BOM头
            reader = csv.DictReader(csvfile) # 创建一个csv.DictReader对象，它将CSV文件的每一行读取为一个字典
            if not reader.fieldnames or not all(f in reader.fieldnames for f in ['subject', 'predicate', 'object']): # 检查CSV文件的表头是否存在，并且是否包含必需的列名（'subject', 'predicate', 'object'）
                print(f"错误: CSV文件 {input_csv_path} 缺少必要的列: 'subject', 'predicate', 'object'") # 如果缺少必要的列，打印错误信息
                return # 结束函数的执行

            print(f"开始从 {input_csv_path} 读取三元组并导入 Neo4j...") # 打印开始读取和导入数据的提示信息
            
            tx = graph.begin() # Start a transaction for batching # 开始一个新的数据库事务，用于批量处理操作以提高效率

            for i, row in enumerate(reader): # 遍历CSV文件中的每一行数据（每一行都是一个字典）
                subject_name = row.get('subject') # 从当前行字典中获取'subject'（主体）的值
                predicate = row.get('predicate') # 从当前行字典中获取'predicate'（谓语）的值
                object_value_str = row.get('object') # 从当前行字典中获取'object'（客体）的值

                if not subject_name or not predicate or object_value_str is None or str(object_value_str).strip() == "": # 检查主体、谓语或客体是否为空或仅包含空白字符
                    # print(f"跳过不完整或空的客体三元组: 主体='{subject_name}', 谓语='{predicate}', 客体='{object_value_str}'") # （注释掉的代码）如果三元组不完整，打印跳过信息
                    continue # 跳过当前循环，处理下一个三元组

                subject_name = subject_name.strip() # 去除主体名称两端的空白字符
                predicate = predicate.strip() # 去除谓语两端的空白字符
                object_value_str = str(object_value_str).strip() # 将客体值转换为字符串并去除两端的空白字符

                # 1. 处理主体节点 (景点) - 确保节点存在 # 第一步：处理主体节点（景点），确保该节点在数据库中存在
                tx.run( # 在当前事务中执行Cypher查询
                    "MERGE (s:景点 {name: $name})", # MERGE语句：如果数据库中已存在标签为"景点"且name属性为指定值的节点s，则匹配该节点；否则，创建一个新的这样的节点
                    name=subject_name # 将subject_name作为参数传递给Cypher查询中的$name
                )
                # count_nodes_created += 1 # MERGE handles this, so this count is indicative # （注释掉的代码）节点创建计数器的更新（MERGE操作会处理实际创建，所以这是一个指示性计数）

                # 2. 根据谓语处理属性或关系 # 第二步：根据谓语的类型，处理节点的属性或节点间的关系
                prop_details = get_property_details(predicate) # 调用get_property_details函数获取当前谓语对应的属性详细信息

                if prop_details:  # 此谓语定义主体的属性 # 如果prop_details不为None，表示这个谓语定义的是主体的属性
                    prop_key = prop_details["key"] # 获取属性的键名（例如 "address", "rating"）
                    prop_type = prop_details["type"] # 获取属性的期望数据类型（例如 str, float）
                    
                    try: # 尝试执行以下代码块
                        value_to_set = None # 初始化要设置的属性值为None
                        if prop_type == float: # 如果期望类型是浮点数
                            value_to_set = float(object_value_str) # 将客体字符串转换为浮点数
                        elif prop_type == int: # Example if you had int types # 如果期望类型是整数（示例，当前映射中没有整数类型）
                             value_to_set = int(float(object_value_str)) # 先转换为浮点数再转换为整数，以处理可能的小数点
                        else: # str # 如果期望类型是字符串（或其他未明确处理的类型）
                            value_to_set = object_value_str # 直接使用原始的客体字符串
                        
                        if value_to_set is not None: # 如果成功转换或获取了值
                             tx.run( # 在当前事务中执行Cypher查询
                                f"MATCH (s:景点 {{name: $name}}) SET s.{{prop_key}} = $value", # MATCH语句：匹配标签为"景点"且name属性为指定值的节点s，然后SET语句：设置该节点的指定属性（由prop_key动态指定）为$value
                                name=subject_name, value=value_to_set # 将subject_name和转换后的value_to_set作为参数传递
                            )
                    except ValueError as ve: # 如果在类型转换过程中发生ValueError（例如，无法将字符串转换为浮点数）
                        print(f"警告: 无法转换属性 '{prop_key}' 的值 '{object_value_str}' (景点: {subject_name}) 为 {prop_type}. 错误: {ve}. 将尝试作为字符串存储。") # 打印警告信息，说明转换失败的原因，并提示将尝试以字符串形式存储
                        tx.run( # 在当前事务中执行Cypher查询
                           f"MATCH (s:景点 {{name: $name}}) SET s.{prop_key} = $value_str", # 设置属性为原始的字符串值
                           name=subject_name, value_str=object_value_str # 将subject_name和原始的object_value_str作为参数传递
                       )
                    except Exception as ex: # 如果在设置属性时发生其他任何未预料的异常
                        print(f"错误: 设置属性 '{prop_key}' 时发生意外错误 (景点: {subject_name}, 值: {object_value_str}). 错误: {ex}") # 打印错误信息，包括属性键、景点名称、值和异常详情

                elif predicate == "属于城市": # 如果谓语是"属于城市"，表示这是一个关系
                    city_name = object_value_str # 客体值即为城市名称
                    if city_name: # 如果城市名称不为空
                        tx.run( # 在当前事务中执行Cypher查询
                            """
                            MATCH (s:景点 {name: $s_name}) # 匹配名为$s_name的景点节点s
                            MERGE (c:城市 {name: $c_name}) # MERGE城市节点c，如果不存在则创建
                            MERGE (s)-[r:属于城市]->(c) # MERGE从景点s到城市c的"属于城市"关系r，如果不存在则创建
                            """, # 多行Cypher查询字符串
                            s_name=subject_name, c_name=city_name # 将subject_name和city_name作为参数传递
                        )
                        # count_nodes_created +=1 # For city # （注释掉的代码）城市节点创建计数器更新
                        # count_rels_created +=1 # （注释掉的代码）关系创建计数器更新
                else: # 如果谓语既不是已定义的属性也不是"属于城市"关系
                    # print(f"提示: 未知或不直接处理的谓语: '{predicate}' (主体: '{subject_name}', 客体: '{object_value_str}')。") # （注释掉的代码）打印未知谓语的提示信息
                    pass # 不做任何操作

                count_triplets_processed += 1 # 已处理的三元组计数器加1
                if (i + 1) % 500 == 0: # Commit every 500 triplets # 每处理500条三元组
                    print(f"已处理 {count_triplets_processed} 条三元组，正在提交事务...") # 打印提交事务的提示信息
                    graph.commit(tx) # 提交当前事务中的所有操作到数据库
                    tx = graph.begin() # Start a new transaction # 开始一个新的事务，用于下一批操作
            
            graph.commit(tx) # Commit any remaining operations # 提交循环结束后剩余在事务中的操作
            print(f"\n成功处理 {count_triplets_processed} 条三元组。") # 打印成功处理的总三元组数量
            print("请在 Neo4j Browser 中检查导入的数据。例如，运行 'MATCH (n:景点) RETURN n LIMIT 25'") # 提示用户如何在Neo4j Browser中检查数据
            print("或 'MATCH (c:城市) RETURN c LIMIT 25'") # 提示检查城市节点的示例查询
            print("或 'MATCH p=()-[r:属于城市]->() RETURN p LIMIT 10'") # 提示检查关系的示例查询


    except FileNotFoundError: # 如果在打开CSV文件时发生FileNotFoundError
        print(f"错误: CSV文件未找到 '{input_csv_path}'") # 打印文件未找到的错误信息
    except csv.Error as csve: # 如果在读取CSV文件时发生csv.Error（例如格式错误）
        print(f"CSV文件读取错误 '{input_csv_path}': {csve}") # 打印CSV读取错误的错误信息
    except Exception as e: # 如果在导入过程中发生其他任何未被捕获的严重异常
        print(f"导入过程中发生严重错误: {e}") # 打印严重错误的错误信息
        import traceback # 导入traceback模块，用于获取详细的异常堆栈信息
        traceback.print_exc() # 打印完整的异常堆栈信息
        if 'tx' in locals() and tx.active: # 检查事务对象tx是否存在且仍处于活动状态
            tx.rollback() # 如果事务活动，则回滚事务，撤销未提交的更改
            print("事务已回滚。") # 打印事务已回滚的提示信息


if __name__ == "__main__": # 如果当前脚本是作为主程序直接运行（而不是被其他模块导入）
    print("开始将三元组数据导入 Neo4j...") # 打印开始导入数据的提示信息
    import_triplets_to_neo4j() # 调用import_triplets_to_neo4j函数执行导入操作
    print("导入脚本执行完成。") # 打印导入脚本执行完成的提示信息