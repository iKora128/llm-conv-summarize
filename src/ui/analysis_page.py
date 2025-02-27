"""
会話分析ページのモジュール
"""
import os
import json
import streamlit as st
from datetime import datetime

from models.conversation_analyzer import ConversationAnalyzer

def render_analysis_page():
    """
    会話分析ページをレンダリングする
    """
    st.title("会話分析")
    
    # 会話履歴の選択
    st.subheader("分析する会話を選択")
    
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
    
    # 分析ボタン
    analyze_button = st.button("会話を分析")
    
    if analyze_button and selected_file:
        # 会話履歴の読み込み
        with open(os.path.join("conversations", selected_file), "r", encoding="utf-8") as f:
            conversation = json.load(f)
        
        # 会話分析の実行
        with st.spinner("会話を分析しています..."):
            analyzer = ConversationAnalyzer()
            analysis_result = analyzer.analyze_conversation(conversation)
            
            # 分析結果の保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file = f"conversations/analysis_{timestamp}.json"
            with open(analysis_file, "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            # HTMLレポートの生成と保存
            html_report = analyzer.generate_report(analysis_result, format="html")
            html_file = f"conversations/analysis_{timestamp}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_report)
            
            st.success(f"分析が完了しました。結果を保存しました:\n- JSON: {analysis_file}\n- HTML: {html_file}")
            
            # 分析結果の表示
            st.subheader("分析結果")
            
            # タブで表示
            tab1, tab2 = st.tabs(["レポート", "JSON"])
            
            with tab1:
                st.components.v1.html(html_report, height=600, scrolling=True)
                
                # HTMLファイルのダウンロードボタン
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    
                st.download_button(
                    label="HTMLレポートをダウンロード",
                    data=html_content,
                    file_name=f"analysis_{timestamp}.html",
                    mime="text/html"
                )
            
            with tab2:
                st.json(analysis_result)
                
                # JSONファイルのダウンロードボタン
                with open(analysis_file, "r", encoding="utf-8") as f:
                    json_content = f.read()
                    
                st.download_button(
                    label="JSON分析結果をダウンロード",
                    data=json_content,
                    file_name=f"analysis_{timestamp}.json",
                    mime="application/json"
                ) 