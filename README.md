# 脑信号解码智能助手

## 1. 项目描述

本项目是一个面向脑机接口（BCI）与脑信号解码领域的智能对话助手，基于 ReAct 推理循环构建，能够自主调用多种工具完成专业问答、信息检索、地图查询、数学计算等任务。系统集成了 MCP 客户端，可动态注册云端工具服务（如天气、计算器、时间），同时通过 Skill 机制引入了高德地图综合服务（POI 搜索、步行路线规划、驾车路线规划等），并封装了 RAG 知识库检索、脑科学实验记录模拟等本地能力。用户通过 Streamlit 前端交互，支持多用户注册与登录，对话历史通过 MySQL 持久化存储，每个用户的会话完全隔离，并支持会话标题自动生成。

在技术架构上，Agent 核心使用 LangChain 实现，模型采用通义千问（qwen3-max）和 DashScope 嵌入向量模型。知识库管理基于 Chroma 向量数据库，支持从 PDF、TXT 文档中提取内容、分块、向量化存储及 MD5 去重。工具注册中心统一管理本地 `@tool` 装饰器工具和 MCP 远程工具，中间件实现了日志监控、异常捕获和报告场景的动态提示词切换。系统已通过 ngrok 实现内网穿透，提供演示地址如下：

**在线演示**：[https://poser-detached-napped.ngrok-free.dev](https://poser-detached-napped.ngrok-free.dev)

本项目功能完整、可交互，既可作为脑科学研究人员的问答工具，也可作为 Agent 技术的学习范例。代码结构清晰，注释齐全，支持横向扩展。

## 2. 代码部署

### 2.1 准备运行环境

- **Python 版本**：3.10 或更高。
- **安装 MySQL**：创建数据库 `agent_db`，并创建一个专用用户（例如 `agent_user`）。
- **安装依赖**：在项目根目录执行  
  ```bash
  pip install -r requirements.txt

### 2.2 配置文件与环境变量

手动创建 `.env` 文件，填入以下内容：

```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=agent_user
MYSQL_PASSWORD=你的数据库密码
MYSQL_DATABASE=agent_db

DASHSCOPE_API_KEY=你的通义千问API Key
AMAP_WEBSERVICE_KEY=你的高德地图API Key

### 2.3 启动应用

在项目根目录执行：

```bash
streamlit run app.py
    
3.公网访问演示说明
(1) 打开演示链接，本地部署后可打开本地链接。
(2) 首次使用请点击“还没有账号？立即注册”，创建新用户。
(3) 登录后即可进行对话，支持以下自然语言请求：
    日常对话；
    脑信号领域相关对话；
    脑信号领域报告生成；
    兴趣点搜索、路径规划；
    数学计算；
    日期、天气查询。
(4) 左侧侧边栏可管理多个会话（新建、删除、切换）。
(5) 点击“🔧 查看所有工具”可查看当前可用的全部工具列表。
