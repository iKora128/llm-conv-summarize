"""
LLM同士のチャット実験アプリケーション
"""
import os
import json
import time
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

from models.llm_manager import LLMManager
from utils.html_generator import generate_chat_html
from ui.history_page import render_history_page
from ui.analysis_page import render_analysis_page
from ui.profile_page import render_profile_page

# 環境変数の読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="LLM会話シミュレーター",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSSスタイル
st.markdown("""
<style>
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.human {
        background-color: #e1ffc7;
        border-bottom-right-radius: 0;
        margin-left: 20%;
    }
    .chat-message.assistant {
        background-color: #f0f0f0;
        border-bottom-left-radius: 0;
        margin-right: 20%;
    }
    .chat-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    .chat-role {
        font-weight: bold;
    }
    .chat-timestamp {
        font-size: 0.8rem;
        color: #888;
    }
    .chat-content {
        line-height: 1.5;
    }
    .stButton button {
        width: 100%;
    }
    .streaming-container {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        height: 300px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'llm_manager' not in st.session_state:
    st.session_state.llm_manager = LLMManager()
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'streaming_content' not in st.session_state:
    st.session_state.streaming_content = {"assistant": "", "human": ""}
if 'is_streaming' not in st.session_state:
    st.session_state.is_streaming = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "会話実験"

# サイドバー
with st.sidebar:
    st.title("LLM会話シミュレーター")
    
    # ページ選択
    st.subheader("ページ")
    page = st.radio(
        "ページを選択",
        options=["会話実験", "会話履歴", "会話分析", "ユーザープロファイル"],
        index=0,
        key="page_selection"
    )
    st.session_state.current_page = page
    
    if page == "会話実験":
        # モデル選択
        st.subheader("モデル設定")
        assistant_model = st.selectbox(
            "アシスタントモデル",
            options=["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
            index=0,
        )
        human_model = st.selectbox(
            "人間役モデル",
            options=["gpt-4o", "claude-3-opus", "claude-3-sonnet", "gemini-1.5-flash"],
            index=0,
        )
        
        # システムプロンプト設定
        st.subheader("システムプロンプト")
        assistant_system_prompt = st.text_area(
            "アシスタント用システムプロンプト",
            value="あなたは親切で役立つAIアシスタントです。ユーザーの質問に対して、正確で有益な情報を提供してください。",
            height=150,
        )
        human_system_prompt = st.text_area(
            "人間役用システムプロンプト",
            value="あなたは人間として振る舞ってください。AIアシスタントとの会話で、自然な返答をしてください。質問は具体的に、会話は自然に進めてください。チャット言葉ではなく、普通の話し言葉を使ってください。",
            height=150,
        )
        
        # 会話設定
        st.subheader("会話設定")
        num_turns = st.slider("会話ターン数", min_value=1, max_value=20, value=5)
        use_streaming = st.checkbox("ストリーミングモードを使用", value=True)
        
        # 保存形式
        st.subheader("保存形式")
        save_json = st.checkbox("JSONで保存", value=True)
        save_html = st.checkbox("HTMLで保存", value=True)

# 現在のページに応じたコンテンツを表示
if st.session_state.current_page == "会話実験":
    # メイン画面
    st.title("LLM同士の会話実験")
    
    # 初期プロンプト入力
    initial_prompt = st.text_area(
        "初期プロンプト（人間役の最初の発言）",
        value="こんにちは！最近、AIについて興味を持ち始めました。AIの基本的な仕組みについて教えてもらえますか？",
        height=100,
    )
    
    # 会話開始ボタン
    start_button = st.button("会話を開始")
    
    # ストリーミング表示用のコンテナ
    if use_streaming:
        streaming_container = st.empty()
    
    # 会話履歴表示用のコンテナ
    conversation_container = st.container()
    
    # 会話開始処理
    if start_button:
        # モデル設定の更新
        st.session_state.llm_manager.assistant_model = assistant_model
        st.session_state.llm_manager.human_model = human_model
        
        # ストリーミングコールバック関数
        def assistant_callback(chunk):
            st.session_state.streaming_content["assistant"] += chunk
            display_streaming()
            
        def human_callback(chunk):
            st.session_state.streaming_content["human"] += chunk
            display_streaming()
        
        # ストリーミング表示関数
        def display_streaming():
            with streaming_container.container():
                st.markdown("### リアルタイム生成中...")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### アシスタント")
                    st.markdown(st.session_state.streaming_content["assistant"])
                with col2:
                    st.markdown("#### 人間役")
                    st.markdown(st.session_state.streaming_content["human"])
        
        # ストリーミングモードの設定
        stream_callbacks = None
        if use_streaming:
            st.session_state.is_streaming = True
            st.session_state.streaming_content = {"assistant": "", "human": ""}
            stream_callbacks = {
                "assistant": assistant_callback,
                "human": human_callback
            }
        
        # 会話シミュレーション実行
        with st.spinner("LLM同士の会話をシミュレーションしています..."):
            conversation = st.session_state.llm_manager.simulate_conversation(
                initial_prompt=initial_prompt,
                assistant_system_prompt=assistant_system_prompt,
                human_system_prompt=human_system_prompt,
                num_turns=num_turns,
                stream=use_streaming,
                stream_callback=stream_callbacks
            )
            st.session_state.conversation_history = conversation
            st.session_state.is_streaming = False
        
        # 会話履歴の保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []
        
        # メタ情報を追加
        meta_info = {
            "meta": {
                "assistant_model": assistant_model,
                "human_model": human_model,
                "assistant_system_prompt": assistant_system_prompt,
                "human_system_prompt": human_system_prompt,
                "num_turns": num_turns,
                "timestamp": datetime.now().isoformat()
            }
        }
        conversation_with_meta = [meta_info] + conversation
        
        if save_json:
            json_file = f"conversations/conversation_{timestamp}.json"
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(conversation_with_meta, f, ensure_ascii=False, indent=2)
            saved_files.append(f"JSONファイル: {json_file}")
            
        if save_html:
            html_file = f"conversations/conversation_{timestamp}.html"
            os.makedirs(os.path.dirname(html_file), exist_ok=True)
            html_content = generate_chat_html(conversation_with_meta, title="LLM会話シミュレーション")
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            saved_files.append(f"HTMLファイル: {html_file}")
        
        if saved_files:
            st.success(f"会話履歴を保存しました:\n" + "\n".join(saved_files))
    
    # 会話履歴の表示
    with conversation_container:
        if st.session_state.conversation_history:
            st.subheader("会話履歴")
            for message in st.session_state.conversation_history:
                role = message["role"]
                content = message["content"]
                timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                
                role_label = "人間" if role == "human" else "アシスタント"
                
                st.markdown(f"""
                <div class="chat-message {role}">
                    <div class="chat-header">
                        <div class="chat-role">{role_label}</div>
                        <div class="chat-timestamp">{timestamp}</div>
                    </div>
                    <div class="chat-content">{content.replace(chr(10), '<br>')}</div>
                </div>
                """, unsafe_allow_html=True)

elif st.session_state.current_page == "会話履歴":
    render_history_page()
    
elif st.session_state.current_page == "会話分析":
    render_analysis_page()
    
elif st.session_state.current_page == "ユーザープロファイル":
    render_profile_page()