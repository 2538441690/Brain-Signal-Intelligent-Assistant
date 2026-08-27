# 脑信号解码智能助手

## 1. 项目描述

本项目是一个面向脑机接口（BCI）与脑信号解码领域的智能对话助手，基于多Agent协同架构（Supervisor模式）构建，由 1个主管Agent（对话协调员） 和 4个专家Agent 协同完成复杂任务：

📚 知识检索专家：基于RAG向量库检索脑信号解码专业论文、算法原理、硬件指南及常见问题解答。

📊 解码监控专家：查询解码准确率、信号质量、可用特征提取算法，并支持在线解码模拟。

📝 报告生成专家：遵循固定流程生成个人月度脑信号解码报告（获取被试ID → 获取月份 → 注入上下文 → 拉取外部实验记录 → 撰写报告）。

🛠 实用工具专家：提供数学计算、日期查询、天气查询和高德地图坐标查询等通用能力。

主管Agent负责理解用户意图，自主决定委派给哪个（些）专家，并整合各专家的返回结果，输出完整、专业的回答。系统封装了RAG知识库检索、脑科学实验记录模拟等本地能力，并集成了高德地图地理编码服务。前端基于 Streamlit 构建，支持流式打字机效果，交互体验流畅。

在技术架构上，Agent核心使用 LangChain 的 create_agent 和中间件机制实现，模型采用通义千问（qwen-turbo）和 DashScope 嵌入向量模型。知识库管理基于 Chroma 向量数据库，支持从 PDF、TXT 文档中提取内容、分块、向量化存储及 MD5 去重。各专家Agent拥有独立的工具集，主管Agent通过委派工具进行路由，中间件实现了统一的日志监控、异常捕获和报告场景的动态提示词切换。

系统已通过 ngrok 实现内网穿透，提供演示地址如下：

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
```

### 2.3 启动应用

在项目根目录执行：

```bash
streamlit run app.py
```
    
## 3.公网访问演示说明
(1) 打开演示链接，本地部署后可打开本地链接。  

(2) 首次使用请点击“还没有账号？立即注册”，创建新用户。  
    如果想直接使用，请登录账号：
    账号：wangzhixun
    密码：2538441690
    <img width="1787" height="493" alt="PixPin_2026-06-01_20-17-07" src="https://github.com/user-attachments/assets/c387bff8-5649-4508-9e0f-f9fddd44f5e5" />


(3) 登录后即可进行对话，支持以下自然语言请求：
    日常对话；
    脑信号领域相关对话；
    脑信号领域报告生成；
    兴趣点搜索、路径规划；
    数学计算；
    日期、天气查询。  
    <img width="1856" height="826" alt="PixPin_2026-06-01_20-17-30" src="https://github.com/user-attachments/assets/f4868a7c-3f99-4393-93ee-2b501121d434" />

    
(4) 左侧侧边栏可管理多个会话（新建、删除、切换）。  

(5) 点击“🔧 查看所有工具”可查看当前可用的全部工具列表。
