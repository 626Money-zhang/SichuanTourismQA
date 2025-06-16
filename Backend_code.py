from flask import Flask, render_template, request  # 导入 Flask 类，用于创建 Web 应用；导入 render_template 函数，用于渲染 HTML 模板；导入 request 对象，用于处理客户端请求

# 导入问答系统的组件
from question_classifier import QuestionClassifier  # 导入问题分类器类
from question_parser import QuestionParser  # 导入问题解析器类
from answer_search import AnswerSearcher  # 导入答案搜索器类

# 导入环境变量处理
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print("警告: .env文件不存在，将使用默认值。请参考.env.example创建您的.env文件。")

# 导入API调用所需的库
import websocket  # 导入 WebSocket 客户端库，用于与讯飞星火 API 进行实时双向通信
import datetime  # 导入日期时间模块，用于生成时间戳
import hashlib  # 导入哈希库，用于生成签名
import base64  # 导入 Base64 编码模块
import hmac  # 导入 HMAC 算法模块，用于生成签名
import json  # 导入 JSON 模块，用于处理 JSON 数据格式
from urllib.parse import urlencode, quote  # 从 urllib.parse 模块导入 urlencode 函数，用于将字典编码为 URL 查询字符串；导入 quote 函数，用于 URL 编码特殊字符
from typing import List, Dict, Union  # 从 typing 模块导入类型提示，用于代码可读性和静态分析
import _thread  # 导入 _thread 模块，用于在单独的线程中运行 WebSocket，避免阻塞主线程
import threading  # 导入 threading 模块，用于创建线程
import uuid  # 导入 uuid 模块，用于生成唯一标识符

# --- 讯飞星火 Spark X1 WebSocket 服务接口认证信息 ---
# 优先从环境变量加载配置，如果不存在则使用默认值
APPID = os.getenv("SPARK_APPID", "your_APPID")  # 设置讯飞星火应用的 APPID
APISECRET = os.getenv("SPARK_APISECRET", "your_APISecret")  # 设置讯飞星火应用的 APISecret
APIKEY = os.getenv("SPARK_APIKEY", "your_APIKey")  # 设置讯飞星火应用的 APIKey

# 检查API配置是否已设置
if "your_" in APPID or "your_" in APISECRET or "your_" in APIKEY:
    print("警告: 讯飞星火API配置未完成。如需使用API功能，请在.env文件中设置正确的值。")

# 服务信息
SPARK_X1_WEBSOCKET_HOST = "spark-api.xf-yun.com"  # 定义讯飞星火 WebSocket 服务的主机地址
SPARK_X1_WEBSOCKET_PATH = "/v1/x1"  # 定义讯飞星火 WebSocket 服务的路径
SPARK_X1_WEBSOCKET_URL_BASE = f"wss://{SPARK_X1_WEBSOCKET_HOST}{SPARK_X1_WEBSOCKET_PATH}"  # 构建基础的 WebSocket URL

# 全局变量，用于存储WebSocket响应
ws_response_handler = {  # 初始化一个字典，用于存储 WebSocket 的响应信息
    "full_response": "",  # 存储从 API 接收到的完整响应文本
    "is_finished": False,  # 标记 API 响应是否已完全接收
    "error_message": None  # 存储 API 调用过程中发生的错误信息
}

# 存储用户对话历史
chat_history = {}  # 初始化一个空字典，用于存储不同用户的对话历史；键为用户ID，值为对话列表

# 存储API查询结果
api_results = {}  # 初始化一个空字典，用于存储API查询结果；键为查询ID，值为结果字典

app = Flask(__name__)  # 创建一个 Flask 应用实例

# 初始化问答系统的核心组件
# 这会在 Flask 应用启动时执行一次
try:  # 使用 try-except 块来捕获初始化过程中可能发生的异常
    classifier = QuestionClassifier()  # 创建问题分类器实例
    parser = QuestionParser()  # 创建问题解析器实例
    searcher = AnswerSearcher()  # 创建答案搜索器实例
    print("问答系统组件初始化成功。")  # 打印初始化成功的消息
except Exception as e:  # 捕获所有可能的异常
    print(f"错误：问答系统组件初始化失败: {e}")  # 打印初始化失败的错误信息
    classifier = None  # 将分类器设置为空
    parser = None  # 将解析器设置为空
    searcher = None  # 将搜索器设置为空


def get_tourist_answer(question_str: str, user_id: str = "default_user"):  # 定义获取旅游问答答案的函数
    """
    处理用户问题并从问答系统获取答案。
    先尝试从本地知识图谱获取答案，如果找不到再使用API。
    """
    if not all([classifier, parser, searcher]):  # 检查问答系统的所有组件是否都已成功初始化
        return "抱歉，问答系统未能正确初始化，无法处理您的问题。"  # 如果有组件未初始化，则返回错误信息

    res_classify = classifier.classify(question_str)  # 调用问题分类器对用户输入的问题进行分类

    if not res_classify or not res_classify.get('args'):  # 检查分类结果是否存在，以及是否包含 'args'（通常是识别出的实体）
        # 没有识别出景点实体，使用API回答
        print("没有识别出景点实体，转向API寻求回答...")  # 打印提示信息
        waiting_msg = "正在思考中，由于没有识别到相关景点信息，正在联网查询更多资源，请稍等片刻..."
        print(waiting_msg)
        query_id = str(uuid.uuid4())  # 生成一个唯一的查询ID
        # 在后台线程中处理API请求
        threading.Thread(target=lambda: process_api_query(question_str, user_id, query_id)).start()
        return waiting_msg, query_id  # 返回等待提示和查询ID

    if not res_classify.get('question_types'):  # 检查分类结果中是否包含问题类型
        attraction_name_keys = list(res_classify.get('args', {}).keys())  # 获取识别出的景点名称列表
        example_attraction = attraction_name_keys[0] if attraction_name_keys else "该景点"  # 选择第一个景点名称作为示例，如果列表为空则使用默认值
        return f"抱歉，我理解您在问关于\"{example_attraction}\"的信息，但我不太明白您具体想了解哪个方面。您可以问我关于景点的地址、开放时间、简介等信息。"  # 返回提示信息，引导用户提问更具体的问题

    cypher_queries = parser.parser_main(res_classify)  # 调用问题解析器将分类结果转换为 Cypher 查询语句

    if not cypher_queries:  # 检查是否成功生成了 Cypher 查询语句
        # 无法构建有效查询，使用API回答
        print("无法构建有效的数据库查询，转向API寻求回答...")  # 打印提示信息
        waiting_msg = "正在思考中，由于无法构建有效的查询，正在联网查询更多资源，请稍等片刻..."
        print(waiting_msg)
        query_id = str(uuid.uuid4())  # 生成一个唯一的查询ID
        # 在后台线程中处理API请求
        threading.Thread(target=lambda: process_api_query(question_str, user_id, query_id)).start()
        return waiting_msg, query_id  # 返回等待提示和查询ID

    answers_list = searcher.search_main(cypher_queries)  # 调用答案搜索器执行 Cypher 查询并获取答案列表

    if not answers_list:  # 检查是否从知识图谱中找到了答案
        # 本地知识图谱没有找到答案，使用API回答
        print("本地知识图谱没有找到答案，转向API寻求回答...")  # 打印提示信息
        waiting_msg = "正在思考中，由于本地知识库中未找到相关信息，正在联网查询更多资源，请稍等片刻..."
        print(waiting_msg)
        query_id = str(uuid.uuid4())  # 生成一个唯一的查询ID
        # 在后台线程中处理API请求
        threading.Thread(target=lambda: process_api_query(question_str, user_id, query_id)).start()
        return waiting_msg, query_id  # 返回等待提示和查询ID

    # 找到本地答案，直接返回
    return "\n".join(answers_list)  # 将答案列表中的所有答案用换行符连接起来并返回


# API调用相关函数
def generate_auth_params():  # 定义生成讯飞星火 API 认证参数的函数
    """
    生成讯飞星火API认证所需的URL和请求头
    返回: 完整的WebSocket URL和日期头信息
    """
    # 构造URL
    host = SPARK_X1_WEBSOCKET_HOST  # 获取 WebSocket 主机地址
    path = SPARK_X1_WEBSOCKET_PATH  # 获取 WebSocket 路径
    
    # 生成RFC1123格式的时间戳
    # 使用 UTC 时间以避免时区问题，讯飞文档通常推荐 UTC
    now_utc = datetime.datetime.now(datetime.timezone.utc)  # 获取当前的 UTC 时间
    date_header_value = now_utc.strftime('%a, %d %b %Y %H:%M:%S GMT')  # 将当前 UTC 时间格式化为 RFC1123 字符串
    
    # 拼接字符串用于签名
    signature_origin = "host: " + host + "\n"  # 构建签名的原始字符串，包含 host
    signature_origin += "date: " + date_header_value + "\n"  # 在签名原始字符串中添加 date
    signature_origin += "GET " + path + " HTTP/1.1"  # 在签名原始字符串中添加请求方法、路径和 HTTP 版本
    
    # 进行hmac-sha256进行加密
    signature_sha = hmac.new(APISECRET.encode('utf-8'), signature_origin.encode('utf-8'),  # 使用 APISecret 对签名原始字符串进行 HMAC-SHA256 加密
                             digestmod=hashlib.sha256).digest()  # 获取加密后的摘要
    signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')  # 将加密摘要进行 Base64 编码
    
    authorization_origin = f'api_key="{APIKEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'  # 构建 Authorization 字段的原始字符串
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')  # 将 Authorization 原始字符串进行 Base64 编码
    
    # 将请求的鉴权参数元组拼装为字典 (用于URL query string)
    v = {  # 创建一个字典，包含认证所需的参数
        "authorization": authorization,  # 添加 Authorization 字段
        "date": date_header_value,  # 添加 Date 字段
        "host": host  # 添加 Host 字段
    }
    # 拼接鉴权参数，生成url
    url_with_auth = SPARK_X1_WEBSOCKET_URL_BASE + '?' + urlencode(v)  # 将认证参数编码为 URL 查询字符串并附加到基础 WebSocket URL 后面
    
    # 返回完整的URL和需要作为HTTP Header发送的Date
    return url_with_auth, date_header_value  # 返回构建好的带有认证参数的 WebSocket URL 和 Date 头信息

def on_message(ws, message):  # 定义处理 WebSocket 接收到消息的回调函数
    """
    处理WebSocket接收到的消息
    """
    global ws_response_handler  # 声明使用全局变量 ws_response_handler
    data = json.loads(message)  # 将接收到的 JSON 格式的消息字符串解析为 Python 字典
    header = data.get('header', {})  # 从消息数据中获取 'header' 部分，如果不存在则返回空字典
    code = header.get('code')  # 从 'header' 中获取状态码 'code'

    if code != 0:  # 检查状态码是否为 0 (0 通常表示成功)
        ws_response_handler["error_message"] = f"请求错误: code={code}, message={header.get('message', 'N/A')}, sid={header.get('sid', 'N/A')}"  # 如果状态码非 0，则构建错误信息
        print(f"\n{ws_response_handler['error_message']}")  # 打印错误信息
        ws_response_handler["is_finished"] = True  # 标记响应已完成（因为出错了）
        ws.close()  # 关闭 WebSocket 连接
        return  # 结束函数执行

    payload = data.get('payload', {})  # 从消息数据中获取 'payload' 部分
    choices = payload.get('choices', {})  # 从 'payload' 中获取 'choices' 部分
    status = choices.get('status')  # 从 'choices' 中获取响应状态 'status' (例如，0表示第一帧，1表示中间帧，2表示最后一帧)
    
    text_array = choices.get('text', [])  # 从 'choices' 中获取文本内容数组 'text'
    for text_item in text_array:  # 遍历文本内容数组
        content = text_item.get('content', '')  # 获取每个文本项的 'content'
        ws_response_handler["full_response"] += content  # 将获取到的内容追加到全局的完整响应中

    if status == 2:  # 检查响应状态是否为 2 (表示这是最后一帧数据)
        ws_response_handler["is_finished"] = True  # 标记响应已完成
        ws.close()  # 关闭 WebSocket 连接

def on_error(ws, error):  # 定义处理 WebSocket 发生错误的回调函数
    """
    处理WebSocket错误
    """
    global ws_response_handler  # 声明使用全局变量 ws_response_handler
    error_msg = f"WebSocket错误: {error}"  # 构建基础的错误信息
    if isinstance(error, websocket.WebSocketBadStatusException):  # 检查错误是否为 WebSocket 握手失败异常
        error_msg = f"WebSocket握手失败: Status {error.status_code} - {error.resp_body.decode() if error.resp_body else 'No body'}"  # 构建更详细的握手失败错误信息
    
    ws_response_handler["error_message"] = error_msg  # 将错误信息存储到全局变量中
    print(f"\n{ws_response_handler['error_message']}")  # 打印错误信息
    ws_response_handler["is_finished"] = True  # 标记响应已完成（因为出错了）

def on_close(ws, close_status_code, close_msg):  # 定义处理 WebSocket 连接关闭的回调函数
    """
    处理WebSocket连接关闭
    """
    global ws_response_handler  # 声明使用全局变量 ws_response_handler
    if not ws_response_handler["is_finished"]:  # 检查响应是否已经被标记为完成
        ws_response_handler["is_finished"] = True  # 如果尚未标记，则标记为完成
    if close_status_code or close_msg:  # 检查是否存在关闭状态码或关闭消息
         if not ws_response_handler["error_message"] and (close_status_code != 1000 and close_status_code is not None): # 如果没有预设的错误信息，并且关闭状态码不是1000（正常关闭）
            ws_response_handler["error_message"] = f"WebSocket连接异常关闭: code={close_status_code}, msg={close_msg}"  # 构建连接异常关闭的错误信息
            print(f"\n{ws_response_handler['error_message']}")  # 打印错误信息

def on_open(ws, message_history: List[Dict[str, str]]):  # 定义处理 WebSocket 连接成功打开的回调函数
    """
    处理WebSocket连接打开事件，发送查询请求
    """
    global ws_response_handler  # 声明使用全局变量 ws_response_handler
    ws_response_handler["full_response"] = ""  # 重置完整响应内容为空字符串
    ws_response_handler["is_finished"] = False  # 重置响应完成标记为 False
    ws_response_handler["error_message"] = None  # 重置错误信息为 None
    
    request_payload = {  # 构建发送给 API 的请求体
        "header": {  # 请求头部分
            "app_id": APPID,  # 设置应用 ID
            "uid": "user_session_id"  # 设置用户会话 ID (这里是固定值，实际应用中应为动态生成或获取)
        },
        "parameter": {  # 参数部分
            "chat": {  # 对话参数
                "domain": "x1",  # 指定使用的模型版本或领域
                "temperature": 1.0,  # 设置生成文本的随机性 (温度)
                "max_tokens": 4096,  # 设置生成的最大 token 数量
                "auditing": "default"  # 设置内容审核策略
            }
        },
        "payload": {  # 负载部分
            "message": { "text": message_history }  # 包含用户对话历史的消息内容
        }
    }
    ws.send(json.dumps(request_payload))  # 将请求体序列化为 JSON 字符串并通过 WebSocket 发送

def get_answer_from_api(user_question: str, user_id: str = "default_user") -> str:  # 定义从讯飞星火 API 获取答案的函数
    """
    调用星火API获取问题的回答
    参数:
        user_question: 用户问题
        user_id: 用户标识，用于保存对话历史
    返回:
        API返回的回答文本
    """
    # 获取或初始化用户的对话历史
    if user_id not in chat_history:  # 检查该用户的对话历史是否已存在
        chat_history[user_id] = []  # 如果不存在，则初始化为空列表
    
    # 添加用户问题到对话历史
    user_history = chat_history[user_id]  # 获取指定用户的对话历史列表
    user_history.append({"role": "user", "content": user_question})  # 将当前用户的问题添加到历史记录中
    
    # 检查对话历史长度，过长则截断 (讯飞星火 API 对话历史有长度限制)
    while sum(len(msg["content"]) for msg in user_history) > 11000:  # 计算对话历史中所有消息内容的总长度，如果超过阈值
        if len(user_history) > 1:  # 如果历史记录不止一条
            user_history.pop(0)  # 则移除最早的一条记录 (先进先出)
        else:  # 如果只有一条记录（当前用户问题）且已超长
            break  # 则停止截断，避免移除当前问题
    
    # 调用API获取回答
    auth_url, date_for_header = generate_auth_params()  # 生成带认证参数的 WebSocket URL 和 Date 头
    handshake_headers = {  # 构建 WebSocket 握手时需要的请求头
        "Date": date_for_header,  # 设置 Date 头
        "Host": SPARK_X1_WEBSOCKET_HOST  # 设置 Host 头
    }
    
    ws = websocket.WebSocketApp(  # 创建 WebSocketApp 实例
        auth_url,  # 设置 WebSocket 连接的 URL
        header=handshake_headers,  # 设置握手请求头
        on_message=on_message,  # 注册接收消息的回调函数
        on_error=on_error,  # 注册发生错误的回调函数
        on_close=on_close,  # 注册连接关闭的回调函数
        on_open=lambda ws_app: on_open(ws_app, user_history)  # 注册连接打开的回调函数，使用 lambda 传递用户历史
    )
    
    global ws_response_handler  # 声明使用全局变量 ws_response_handler
    ws_response_handler["full_response"] = ""  # 在开始新的 API 调用前，重置完整响应
    ws_response_handler["is_finished"] = False  # 重置响应完成标记
    ws_response_handler["error_message"] = None  # 重置错误信息
    
    try:  # 使用 try-except 块捕获 WebSocket 运行过程中可能发生的异常
        ws.run_forever()  # 启动 WebSocket 客户端并保持运行，直到连接关闭或发生错误
    except Exception as e:  # 捕获所有可能的异常
        if not ws_response_handler["error_message"]:  # 如果全局错误信息尚未被设置
             ws_response_handler["error_message"] = f"WebSocket run_forever 异常: {e}"  # 则记录 run_forever 抛出的异常
        ws_response_handler["is_finished"] = True  # 标记响应已完成（因为出错了）
    
    # 获取API回答
    if ws_response_handler["error_message"]:  # 检查在 API 调用过程中是否发生了错误
        return f"API调用错误: {ws_response_handler['error_message']}"  # 如果有错误，则返回错误信息
    
    api_response = ws_response_handler["full_response"]  # 获取从 API 接收到的完整响应文本
    
    # 将API回答添加到对话历史
    user_history.append({"role": "assistant", "content": api_response})  # 将 API 的回答添加到用户的对话历史中
    
    return api_response  # 返回 API 的回答

def process_api_query(question_str: str, user_id: str, query_id: str) -> None:
    """
    在后台处理API查询，并将结果存储到全局变量中
    """
    try:
        result = get_answer_from_api(question_str, user_id)  # 调用API获取答案
        api_results[query_id] = {
            "status": "completed",
            "result": result,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = f"API查询处理异常: {str(e)}"
        print(error_msg)
        api_results[query_id] = {
            "status": "error",
            "result": error_msg,
            "timestamp": datetime.datetime.now().isoformat()
        }

@app.route('/', methods=['GET', 'POST'])  # 定义 Flask 应用的路由和允许的 HTTP 方法 (GET 和 POST)
def home():  # 定义处理该路由请求的函数
    question = None  # 初始化问题变量为空
    answer = None  # 初始化答案变量为空
    error_message = None  # 初始化错误信息变量为空
    query_id = None  # 初始化查询ID为空

    if not all([classifier, parser, searcher]):  # 再次检查问答系统组件是否都已初始化
        error_message = "错误：问答系统核心组件未成功加载，请检查服务器日志。"  # 设置错误信息
        return render_template("index.html", error_message=error_message)  # 渲染 HTML 模板并传递错误信息

    if request.method == 'POST':  # 检查当前请求是否为 POST 方法 (通常是用户提交了问题)
        question = request.form.get('question', '').strip()  # 从 POST 请求的表单数据中获取用户输入的问题，并去除首尾空格
        if question:  # 检查问题是否为空
            try:  # 使用 try-except 块捕获处理问题过程中可能发生的异常
                # 从请求中获取用户ID，或为每个会话生成唯一ID
                user_id = request.cookies.get('user_id', 'default_user')  # 尝试从请求的 cookie 中获取用户 ID，如果不存在则使用默认值
                result = get_tourist_answer(question, user_id)  # 调用核心问答函数获取答案
                
                # 检查返回值类型，处理异步API情况
                if isinstance(result, tuple) and len(result) == 2:
                    answer, query_id = result
                else:
                    answer = result
            except Exception as e:  # 捕获所有可能的异常
                print(f"处理问题 '{question}' 时发生错误: {e}")  # 在服务器端打印错误日志
                error_message = f"抱歉，处理您的问题时发生了一个内部错误。请稍后再试。"  # 设置用户友好的错误提示信息
        else:  # 如果用户提交的问题为空
            pass  # 不做任何处理，或者可以设置提示信息 error_message = "请输入一个问题。"

    return render_template("index.html", question=question, answer=answer, error_message=error_message, query_id=query_id)  # 渲染 HTML 模板并传递问题、答案和错误信息

@app.route('/get_api_result/<query_id>', methods=['GET'])
def get_api_result(query_id):
    """
    获取指定查询ID的API查询结果
    """
    result = api_results.get(query_id, {})
    if not result:
        return json.dumps({"status": "not_found", "result": "找不到对应的查询结果"})
    
    return json.dumps(result)

if __name__ == '__main__':  # 检查当前脚本是否作为主程序直接运行
    print("启动 Flask Web 服务器...")  # 打印启动服务器的提示信息
    app.run(host='0.0.0.0', port=5000, debug=True)  # 运行 Flask 开发服务器，监听所有网络接口的 5000 端口，并开启调试模式
