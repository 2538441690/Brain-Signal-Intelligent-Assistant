# app.py (多用户版本，修复登录/注册分离和自动创建对话)
import streamlit as st
import uuid
from agent.react_agent import ReactAgent
from utils.conversation_db import (
    create_conversation, get_all_conversations, delete_conversation,
    get_messages, update_conversation_title, get_conversation,
    authenticate_user, create_user
)

st.set_page_config(page_title="脑信号解码智能助手", layout="wide")

# 初始化 session_state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
if "show_register" not in st.session_state:
    st.session_state.show_register = False   # False=登录界面, True=注册界面

def auto_login(username, password):
    """注册成功后自动登录"""
    user_id = authenticate_user(username, password)
    if user_id:
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        st.session_state.username = username
        # 为新用户创建一个会话（如果还没有）
        convs = get_all_conversations(user_id)
        if not convs:
            new_id = str(uuid.uuid4())
            create_conversation(new_id, user_id, "新对话")
            st.session_state.current_conv_id = new_id
        else:
            st.session_state.current_conv_id = convs[0]["id"]
        st.rerun()
    else:
        st.error("自动登录失败，请手动登录")

def show_login():
    st.title("🔐 用户登录 / 注册")
    
    if not st.session_state.show_register:
        # ---------- 登录表单 ----------
        with st.form("login_form"):
            login_username = st.text_input("用户名")
            login_password = st.text_input("密码", type="password")
            login_submit = st.form_submit_button("登录")
            if login_submit:
                if not login_username or not login_password:
                    st.error("请填写用户名和密码")
                else:
                    user_id = authenticate_user(login_username, login_password)
                    if user_id:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user_id
                        st.session_state.username = login_username
                        # 检查是否有会话，没有则创建
                        convs = get_all_conversations(user_id)
                        if convs:
                            st.session_state.current_conv_id = convs[0]["id"]
                        else:
                            new_id = str(uuid.uuid4())
                            create_conversation(new_id, user_id, "新对话")
                            st.session_state.current_conv_id = new_id
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
        
        # 切换到注册界面的按钮
        if st.button("还没有账号？立即注册"):
            st.session_state.show_register = True
            st.rerun()
    
    else:
        # ---------- 注册表单 ----------
        with st.form("register_form"):
            reg_username = st.text_input("用户名")
            reg_password = st.text_input("密码", type="password")
            reg_confirm = st.text_input("确认密码", type="password")
            register_submit = st.form_submit_button("注册")
            if register_submit:
                if not reg_username or not reg_password:
                    st.error("用户名和密码不能为空")
                elif reg_password != reg_confirm:
                    st.error("两次输入的密码不一致")
                else:
                    user_id = create_user(reg_username, reg_password)
                    if user_id:
                        st.success("注册成功！正在自动登录...")
                        # 自动登录
                        auto_login(reg_username, reg_password)
                    else:
                        st.error("用户名已存在")
        
        # 返回登录界面的按钮
        if st.button("← 返回登录"):
            st.session_state.show_register = False
            st.rerun()

def show_logout():
    with st.sidebar:
        st.write(f"👤 当前用户: {st.session_state.username}")
        if st.button("🚪 退出登录"):
            for key in ["authenticated", "user_id", "username", "current_conv_id"]:
                st.session_state[key] = None
            st.rerun()

# ------------------ 主应用 ------------------
if not st.session_state.authenticated:
    show_login()
else:
    show_logout()
    st.title("🧠 脑信号解码智能助手")

    # 初始化 Agent（全局单例）
    if "agent" not in st.session_state:
        st.session_state.agent = ReactAgent()

    # 确保 current_conv_id 存在（登录时已创建，但防御）
    if "current_conv_id" not in st.session_state:
        convs = get_all_conversations(st.session_state.user_id)
        if convs:
            st.session_state.current_conv_id = convs[0]["id"]
        else:
            new_id = str(uuid.uuid4())
            create_conversation(new_id, st.session_state.user_id, "新对话")
            st.session_state.current_conv_id = new_id

    # 侧边栏：会话管理
    with st.sidebar:
        st.subheader("📋 对话历史")
        if st.button("➕ 新建对话", use_container_width=True):
            new_id = str(uuid.uuid4())
            create_conversation(new_id, st.session_state.user_id, "新对话")
            st.session_state.current_conv_id = new_id
            st.rerun()

        st.divider()
        convs = get_all_conversations(st.session_state.user_id)
        if not convs:
            st.info("暂无对话记录")
        else:
            for conv in convs:
                col1, col2 = st.columns([4, 1])
                with col1:
                    title = conv["title"]
                    if len(title) > 20:
                        title = title[:20] + "..."
                    if conv["id"] == st.session_state.current_conv_id:
                        button_label = f"✅ **{title}**"
                    else:
                        button_label = title
                    if st.button(button_label, key=conv["id"], use_container_width=True):
                        st.session_state.current_conv_id = conv["id"]
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{conv['id']}"):
                        delete_conversation(conv["id"], st.session_state.user_id)
                        if conv["id"] == st.session_state.current_conv_id:
                            remaining = get_all_conversations(st.session_state.user_id)
                            if remaining:
                                st.session_state.current_conv_id = remaining[0]["id"]
                            else:
                                new_id = str(uuid.uuid4())
                                create_conversation(new_id, st.session_state.user_id, "新对话")
                                st.session_state.current_conv_id = new_id
                        st.rerun()
            st.divider()

        if st.button("🗑️ 清空当前对话", use_container_width=True):
            from utils.conversation_db import clear_conversation_messages
            clear_conversation_messages(st.session_state.current_conv_id, st.session_state.user_id)
            st.rerun()

        st.divider()
        if st.button("🔧 查看所有工具", use_container_width=True):
            from agent.tools.tool_registry import tool_registry
            all_tools = tool_registry.get_all_tools()
            if all_tools:
                st.success(f"📦 当前共加载 {len(all_tools)} 个工具")
                with st.expander("点击展开工具列表", expanded=True):
                    for tool in all_tools:
                        st.markdown(f"**{tool.name}**")
                        st.caption(tool.description or "无描述")
                        st.divider()
            else:
                st.info("暂无可用工具")

    # 主区域：显示消息
    conv_id = st.session_state.current_conv_id
    messages = get_messages(conv_id, st.session_state.user_id)
    for msg in messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # 自动更新会话标题
    if messages:
        first_user_msg = next((m for m in messages if m["role"] == "user"), None)
        if first_user_msg:
            conv_info = get_conversation(conv_id, st.session_state.user_id)
            if conv_info and conv_info["title"] == "新对话":
                new_title = first_user_msg["content"][:20] + ("..." if len(first_user_msg["content"]) > 20 else "")
                update_conversation_title(conv_id, st.session_state.user_id, new_title)
                st.rerun()

    # 输入框
    prompt = st.chat_input("请输入您的问题...")
    if prompt:
        st.chat_message("user").write(prompt)
        response_placeholder = st.chat_message("assistant").empty()
        full_response = ""
        try:
            for chunk in st.session_state.agent.execute_stream(prompt, conv_id, st.session_state.user_id):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
        except Exception as e:
            response_placeholder.error(f"发生错误: {e}")
        st.rerun()