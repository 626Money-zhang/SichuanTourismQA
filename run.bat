@echo off
REM 四川旅游知识图谱问答系统启动脚本
REM 此脚本会激活虚拟环境并启动系统

echo 四川旅游知识图谱问答系统

REM 检查虚拟环境是否存在
if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 检查依赖是否已安装
if not exist venv\Lib\site-packages\flask (
    echo 安装依赖...
    pip install -r requirements.txt
)

:menu
cls
echo.
echo ====== 四川旅游知识图谱问答系统 ======
echo.
echo  [1] 启动Web服务
echo  [2] 启动命令行聊天
echo  [3] 导入知识图谱数据
echo  [4] 爬取旅游数据
echo  [5] 运行测试
echo  [0] 退出
echo.
echo ====================================
echo.

set /p choice=请选择要执行的操作 (0-5): 

if "%choice%"=="1" (
    echo 启动Web服务...
    python src\main.py web
    pause
    goto menu
)
if "%choice%"=="2" (
    echo 启动命令行聊天...
    python src\main.py chat
    goto menu
)
if "%choice%"=="3" (
    echo 导入知识图谱数据...
    python src\main.py import
    pause
    goto menu
)
if "%choice%"=="4" (
    echo 爬取旅游数据...
    python src\main.py crawl
    pause
    goto menu
)
if "%choice%"=="5" (
    echo 运行测试...
    python src\main.py test
    pause
    goto menu
)
if "%choice%"=="0" (
    echo 退出系统...
    goto end
) else (
    echo 输入错误，请重新选择！
    timeout /t 2 >nul
    goto menu
)

:end
echo 感谢使用四川旅游知识图谱问答系统！
deactivate
