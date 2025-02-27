"""
会話分析ページのモジュール
"""
import os
import json
import streamlit as st
from datetime import datetime

from models.conversation_summarizer import ConversationSummarizer

def render_analysis_page():
    """
    会話まとめページをレンダリングする
    """
    st.title("会話まとめ")
    
    # 会話履歴の選択
    st.subheader("まとめ対象の会話履歴を選択")
    
    # conversationsディレクトリが存在しない場合は作成
    os.makedirs("conversations", exist_ok=True)
    
    # 会話履歴ファイルの一覧を取得
    conversation_files = [f for f in os.listdir("conversations") if f.endswith(".json")]
    
    if not conversation_files:
        st.warning("会話履歴ファイルが見つかりません。まずは会話を実行して保存してください。")
        return
    
    # ファイル選択
    selected_file = st.selectbox(
        "会話履歴ファイル",
        options=conversation_files,
        format_func=lambda x: f"{x} ({datetime.fromtimestamp(os.path.getmtime(os.path.join('conversations', x))).strftime('%Y-%m-%d %H:%M:%S')})"
    )
    
    # システムプロンプト入力
    st.subheader("システムプロンプト")
    system_prompt = st.text_area("システムプロンプトを入力してください", height=150)
    
    # まとめ実行ボタン
    summarize_button = st.button("会話をまとめる")
    
    if summarize_button and selected_file and system_prompt:
        # 会話履歴の読み込み
        with open(os.path.join("conversations", selected_file), "r", encoding="utf-8") as f:
            conversation = json.load(f)

        # まとめの実行
        with st.spinner("会話をまとめています..."):
            summarizer = ConversationSummarizer()
            summary_result = summarizer.summarize_conversation(conversation, system_prompt)
            
        st.subheader("まとめ結果")
        st.json(summary_result)
    elif summarize_button and not system_prompt:
        st.warning("システムプロンプトを入力してください。") 