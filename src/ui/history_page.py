"""
会話履歴閲覧ページのモジュール
"""
import os
import json
import streamlit as st
from datetime import datetime

def render_history_page():
    """
    会話履歴閲覧ページをレンダリングする
    """
    st.title("会話履歴")
    
    # conversationsディレクトリが存在しない場合は作成
    os.makedirs("conversations", exist_ok=True)
    
    # 会話履歴ファイルの一覧を取得
    json_files = [f for f in os.listdir("conversations") if f.endswith(".json") and f.startswith("conversation_")]
    html_files = [f for f in os.listdir("conversations") if f.endswith(".html") and f.startswith("conversation_")]
    
    if not json_files and not html_files:
        st.warning("会話履歴ファイルが見つかりません。まずは会話を実行して保存してください。")
        return
    
    # タブで表示形式を選択
    tab1, tab2 = st.tabs(["HTML形式", "JSON形式"])
    
    with tab1:
        if not html_files:
            st.warning("HTML形式の会話履歴ファイルが見つかりません。")
        else:
            # ファイル選択
            selected_html = st.selectbox(
                "HTML形式の会話履歴",
                options=html_files,
                format_func=lambda x: f"{x} ({datetime.fromtimestamp(os.path.getmtime(os.path.join('conversations', x))).strftime('%Y-%m-%d %H:%M:%S')})",
                key="html_select"
            )
            
            if selected_html:
                # HTMLファイルの読み込みと表示
                with open(os.path.join("conversations", selected_html), "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                st.components.v1.html(html_content, height=600, scrolling=True)
                
                # HTMLファイルのダウンロードボタン
                st.download_button(
                    label="HTMLファイルをダウンロード",
                    data=html_content,
                    file_name=selected_html,
                    mime="text/html"
                )
    
    with tab2:
        if not json_files:
            st.warning("JSON形式の会話履歴ファイルが見つかりません。")
        else:
            # ファイル選択
            selected_json = st.selectbox(
                "JSON形式の会話履歴",
                options=json_files,
                format_func=lambda x: f"{x} ({datetime.fromtimestamp(os.path.getmtime(os.path.join('conversations', x))).strftime('%Y-%m-%d %H:%M:%S')})",
                key="json_select"
            )
            
            if selected_json:
                # JSONファイルの読み込みと表示
                with open(os.path.join("conversations", selected_json), "r", encoding="utf-8") as f:
                    conversation = json.load(f)
                
                # 会話履歴の表示
                for message in conversation:
                    if "role" not in message:
                        continue
                        
                    role = message["role"]
                    content = message["content"]
                    timestamp = ""
                    
                    if "timestamp" in message:
                        timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                    
                    role_label = "人間" if role == "human" else "アシスタント"
                    
                    st.markdown(f"""
                    <div style="
                        padding: 1rem;
                        border-radius: 0.5rem;
                        margin-bottom: 1rem;
                        background-color: {'#e1ffc7' if role == 'human' else '#f0f0f0'};
                        {'margin-left: 20%;' if role == 'human' else 'margin-right: 20%;'}
                    ">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <div style="font-weight: bold;">{role_label}</div>
                            <div style="font-size: 0.8rem; color: #888;">{timestamp}</div>
                        </div>
                        <div>{content.replace(chr(10), '<br>')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # JSONファイルのダウンロードボタン
                with open(os.path.join("conversations", selected_json), "r", encoding="utf-8") as f:
                    json_content = f.read()
                    
                st.download_button(
                    label="JSONファイルをダウンロード",
                    data=json_content,
                    file_name=selected_json,
                    mime="application/json"
                ) 