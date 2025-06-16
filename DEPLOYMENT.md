# 四川旅游问答系统部署指南

本文档提供四川旅游知识图谱问答系统的完整部署流程，从环境准备到系统启动。

## 环境要求

- Python 3.8+
- Neo4j 4.0+（作为知识图谱存储）
- 讯飞星火认知大模型API账号（可选，用于补充知识库回答）

## 部署步骤

### 1. 准备环境

#### 1.1 安装 Python 环境

```bash
# 检查 Python 版本
python --version

# 如版本过低，请访问 https://www.python.org/downloads/ 下载安装最新版本
```

#### 1.2 安装 Neo4j

1. 从 [Neo4j 官网](https://neo4j.com/download/) 下载并安装 Neo4j Desktop
2. 创建一个新的数据库实例，设置用户名和密码
3. 启动数据库实例

### 2. 获取代码

```bash
# 克隆代码仓库
git clone https://github.com/your-username/SichuanTourismQA.git

# 进入项目目录
cd SichuanTourismQA
```

### 3. 安装依赖

```bash
# 创建并激活虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置系统

#### 4.1 创建配置文件

```bash
# 复制示例配置文件
copy .env.example .env
```

然后编辑 `.env` 文件，填入以下信息：

```
# Neo4j 数据库配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 讯飞星火API配置（可选）
SPARK_APPID=your_appid
SPARK_APIKEY=your_apikey
SPARK_APISECRET=your_apisecret

# Web服务配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

### 5. 数据导入

#### 5.1 准备知识图谱数据

如果您有自己的四川景点数据，可以将其转换为三元组格式，保存为CSV文件。项目中已经包含了示例数据：

- `景点知识图谱_三元组.csv`: 已处理的三元组数据

#### 5.2 导入数据到Neo4j

运行以下命令导入知识图谱数据：

```bash
python py2neo_data_import.py
```

### 6. 启动系统

#### 6.1 运行Web服务

```bash
python Backend_code.py
```

系统将在 `http://localhost:5000` 启动Web服务。

#### 6.2 使用命令行交互模式（可选）

如果您想通过命令行与系统交互，可以运行：

```bash
python tourist_qa_main.py
```

## 可能的问题及解决方案

### Neo4j连接问题

如果遇到Neo4j连接问题，请检查：
- Neo4j数据库是否已启动
- `.env`中的连接参数是否正确
- 防火墙是否允许7687端口的访问

### API调用失败

如果讯飞星火API调用失败：
- 检查API密钥是否正确
- 检查网络连接
- 查看API调用是否有次数限制

### 查询结果为空

如果查询结果总是为空：
- 检查是否已成功导入景点数据
- 在Neo4j Browser中验证数据是否存在
- 检查问题中的景点名称是否与数据库中的名称匹配

## 系统自定义扩展

### 添加新的景点数据

1. 准备新的景点数据CSV文件，格式与`景点知识图谱_三元组.csv`相同
2. 修改`py2neo_data_import.py`中的文件路径
3. 重新运行导入脚本

### 添加新的问题类型

1. 在`question_classifier.py`中添加新类型的关键词
2. 在`question_parser.py`中添加对应类型的Cypher查询语句生成逻辑
3. 在`answer_search.py`中添加新类型的回答处理逻辑

## 后续维护

- 定期更新景点数据以确保信息时效性
- 监控系统日志识别常见问题
- 根据用户反馈优化问题理解和答案生成
