# 四川旅游知识图谱问答系统

## 项目目录结构
```
SichuanTourismQA/
├── src/                   # 源代码目录
│   ├── data/              # 数据处理相关代码
│   │   ├── crawler.py     # 数据爬取模块
│   │   └── preprocess.py  # 数据预处理模块
│   ├── models/            # 核心模型
│   │   ├── classifier.py  # 问题分类器
│   │   ├── parser.py      # 问题解析器
│   │   └── searcher.py    # 答案搜索器
│   ├── utils/             # 工具函数
│   │   ├── config.py      # 配置管理
│   │   └── logger.py      # 日志工具
│   ├── api/               # API服务
│   │   └── server.py      # Web服务器
│   └── main.py            # 主程序入口
├── data/                  # 数据文件
│   ├── raw/               # 原始数据
│   ├── processed/         # 处理后的数据
│   └── knowledge_graph/   # 知识图谱数据
├── dict/                  # 词典文件
│   └── attraction_name.txt # 景点名称词典
├── tests/                 # 测试代码
├── logs/                  # 日志文件
├── templates/             # Web前端模板
├── requirements.txt       # 依赖包列表
├── .env.example           # 环境变量模板
├── .gitignore             # Git忽略文件
├── README.md              # 项目说明
└── LICENSE                # 开源许可证
```

## 项目重构建议

1. **源代码重组**：
   - 将现有代码按功能分类迁移到 `src` 目录下的相应子目录
   - `question_classifier.py` -> `src/models/classifier.py`
   - `question_parser.py` -> `src/models/parser.py`
   - `answer_search.py` -> `src/models/searcher.py`
   - `Backend_code.py` -> `src/api/server.py`
   - `tourist_qa_main.py` -> `src/main.py`

2. **数据文件重组**：
   - 将CSV数据文件移至 `data` 目录下的相应子目录
   - 爬虫相关代码移至 `src/data/crawler.py`
   - 数据预处理脚本移至 `src/data/preprocess.py`

3. **工具和配置分离**：
   - 创建 `src/utils/config.py` 管理配置信息
   - 创建 `src/utils/logger.py` 集中管理日志功能

4. **测试用例添加**：
   - 为核心功能添加单元测试
   - 添加系统集成测试

这种结构将使项目更加模块化、可维护，并符合Python项目的最佳实践。
