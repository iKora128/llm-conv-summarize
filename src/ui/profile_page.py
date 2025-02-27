"""
ユーザープロファイル表示ページのモジュール
"""
import os
import json
import streamlit as st
from datetime import datetime

from models.user_profile_extractor import UserProfileExtractor

def render_profile_page():
    """
    ユーザープロファイル表示ページをレンダリングする
    """
    st.title("ユーザープロファイル")
    
    # タブで機能を選択
    tab1, tab2 = st.tabs(["プロファイル抽出", "プロファイル閲覧"])
    
    with tab1:
        st.subheader("会話履歴からプロファイルを抽出")
        
        # conversationsディレクトリが存在しない場合は作成
        os.makedirs("conversations", exist_ok=True)
        
        # 会話履歴ファイルの一覧を取得
        conversation_files = [f for f in os.listdir("conversations") if f.endswith(".json") and f.startswith("conversation_")]
        
        if not conversation_files:
            st.warning("会話履歴ファイルが見つかりません。まずは会話を実行して保存してください。")
        else:
            # ファイル選択
            selected_file = st.selectbox(
                "会話履歴ファイル",
                options=conversation_files,
                format_func=lambda x: f"{x} ({datetime.fromtimestamp(os.path.getmtime(os.path.join('conversations', x))).strftime('%Y-%m-%d %H:%M:%S')})"
            )
            
            # 抽出ボタン
            extract_button = st.button("プロファイルを抽出")
            
            if extract_button and selected_file:
                # 会話履歴の読み込み
                with open(os.path.join("conversations", selected_file), "r", encoding="utf-8") as f:
                    conversation = json.load(f)
                
                # プロファイル抽出の実行
                with st.spinner("ユーザープロファイルを抽出しています..."):
                    extractor = UserProfileExtractor()
                    user_profile = extractor.extract_user_profile(conversation)
                    
                    # プロファイルの保存
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    json_file = f"user_profiles/user_profile_{timestamp}.json"
                    extractor.save_user_profile(user_profile, json_file)
                    
                    # HTMLの生成と保存
                    html_file = f"user_profiles/user_profile_{timestamp}.html"
                    html_content = extractor.generate_user_profile_html(user_profile, html_file)
                    
                    st.success(f"プロファイル抽出が完了しました。結果を保存しました:\n- JSON: {json_file}\n- HTML: {html_file}")
                    
                    # プロファイルの表示
                    st.subheader("抽出されたプロファイル")
                    
                    # 基本プロフィール
                    st.markdown("### 基本プロフィール")
                    st.markdown(f"""
                    <div style="
                        padding: 1rem;
                        border-radius: 0.5rem;
                        margin-bottom: 1rem;
                        background-color: #f8f9fa;
                        border-left: 4px solid #4caf50;
                    ">
                        {user_profile.get("profile", "情報なし").replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # コンテキスト情報
                    st.markdown("### コンテキスト情報")
                    st.markdown(f"""
                    <div style="
                        padding: 1rem;
                        border-radius: 0.5rem;
                        margin-bottom: 1rem;
                        background-color: #f8f9fa;
                        border-left: 4px solid #2196f3;
                    ">
                        {user_profile.get("context", "情報なし").replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 次回の会話トピック
                    st.markdown("### 次回の会話トピック")
                    st.markdown(f"""
                    <div style="
                        padding: 1rem;
                        border-radius: 0.5rem;
                        margin-bottom: 1rem;
                        background-color: #f8f9fa;
                        border-left: 4px solid #ff9800;
                    ">
                        {user_profile.get("next", "情報なし").replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # JSONファイルのダウンロードボタン
                    with open(json_file, "r", encoding="utf-8") as f:
                        json_content = f.read()
                        
                    st.download_button(
                        label="JSONプロファイルをダウンロード",
                        data=json_content,
                        file_name=f"user_profile_{timestamp}.json",
                        mime="application/json"
                    )
                    
                    # HTMLファイルのダウンロードボタン
                    with open(html_file, "r", encoding="utf-8") as f:
                        html_content = f.read()
                        
                    st.download_button(
                        label="HTMLプロファイルをダウンロード",
                        data=html_content,
                        file_name=f"user_profile_{timestamp}.html",
                        mime="text/html"
                    )
    
    with tab2:
        st.subheader("保存されたプロファイルを閲覧")
        
        # user_profilesディレクトリが存在しない場合は作成
        os.makedirs("user_profiles", exist_ok=True)
        
        # プロファイルファイルの一覧を取得
        json_files = [f for f in os.listdir("user_profiles") if f.endswith(".json")]
        html_files = [f for f in os.listdir("user_profiles") if f.endswith(".html")]
        
        if not json_files and not html_files:
            st.warning("保存されたプロファイルが見つかりません。まずはプロファイルを抽出してください。")
        else:
            # 表示形式を選択
            view_format = st.radio(
                "表示形式",
                options=["HTML形式", "JSON形式"],
                index=0
            )
            
            if view_format == "HTML形式":
                if not html_files:
                    st.warning("HTML形式のプロファイルファイルが見つかりません。")
                else:
                    # ファイル選択
                    selected_html = st.selectbox(
                        "HTML形式のプロファイル",
                        options=html_files,
                        format_func=lambda x: f"{x} ({datetime.fromtimestamp(os.path.getmtime(os.path.join('user_profiles', x))).strftime('%Y-%m-%d %H:%M:%S')})",
                        key="html_select"
                    )
                    
                    if selected_html:
                        # HTMLファイルの読み込みと表示
                        with open(os.path.join("user_profiles", selected_html), "r", encoding="utf-8") as f:
                            html_content = f.read()
                        
                        st.components.v1.html(html_content, height=600, scrolling=True)
                        
                        # HTMLファイルのダウンロードボタン
                        st.download_button(
                            label="HTMLファイルをダウンロード",
                            data=html_content,
                            file_name=selected_html,
                            mime="text/html"
                        )
            
            else:  # JSON形式
                if not json_files:
                    st.warning("JSON形式のプロファイルファイルが見つかりません。")
                else:
                    # ファイル選択
                    selected_json = st.selectbox(
                        "JSON形式のプロファイル",
                        options=json_files,
                        format_func=lambda x: f"{x} ({datetime.fromtimestamp(os.path.getmtime(os.path.join('user_profiles', x))).strftime('%Y-%m-%d %H:%M:%S')})",
                        key="json_select"
                    )
                    
                    if selected_json:
                        # JSONファイルの読み込みと表示
                        with open(os.path.join("user_profiles", selected_json), "r", encoding="utf-8") as f:
                            user_profile = json.load(f)
                        
                        # 基本プロフィール
                        st.markdown("### 基本プロフィール")
                        st.markdown(f"""
                        <div style="
                            padding: 1rem;
                            border-radius: 0.5rem;
                            margin-bottom: 1rem;
                            background-color: #f8f9fa;
                            border-left: 4px solid #4caf50;
                        ">
                            {user_profile.get("profile", "情報なし").replace(chr(10), '<br>')}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # コンテキスト情報
                        st.markdown("### コンテキスト情報")
                        st.markdown(f"""
                        <div style="
                            padding: 1rem;
                            border-radius: 0.5rem;
                            margin-bottom: 1rem;
                            background-color: #f8f9fa;
                            border-left: 4px solid #2196f3;
                        ">
                            {user_profile.get("context", "情報なし").replace(chr(10), '<br>')}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 次回の会話トピック
                        st.markdown("### 次回の会話トピック")
                        st.markdown(f"""
                        <div style="
                            padding: 1rem;
                            border-radius: 0.5rem;
                            margin-bottom: 1rem;
                            background-color: #f8f9fa;
                            border-left: 4px solid #ff9800;
                        ">
                            {user_profile.get("next", "情報なし").replace(chr(10), '<br>')}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # JSONファイルのダウンロードボタン
                        with open(os.path.join("user_profiles", selected_json), "r", encoding="utf-8") as f:
                            json_content = f.read()
                            
                        st.download_button(
                            label="JSONファイルをダウンロード",
                            data=json_content,
                            file_name=selected_json,
                            mime="application/json"
                        ) 