"""
ユーザープロファイル抽出のためのモジュール
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from google import genai
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

class UserProfileExtractor:
    """
    会話履歴からユーザープロファイルを抽出するクラス
    """
    
    def __init__(self):
        """
        UserProfileExtractorの初期化
        """
        # API Keyの設定
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # クライアントの初期化
        if self.google_api_key:
            self.genai_client = genai.Client(api_key=self.google_api_key)
        else:
            self.genai_client = None
        
        # モデル設定
        self.model_name = "gemini-2.0-flash"
        self.fallback_model_name = "gemini-1.5-pro"
        
    def _format_conversation_for_extraction(self, conversation: List[Dict[str, Any]]) -> str:
        """
        会話履歴をプロファイル抽出用のテキスト形式に変換する
        
        Args:
            conversation: 会話履歴
            
        Returns:
            抽出用のテキスト
        """
        formatted_text = "# 会話履歴\n\n"
        
        for message in conversation:
            if "role" not in message:
                continue
                
            role = message["role"]
            content = message["content"]
            timestamp = ""
            
            if "timestamp" in message:
                timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            
            role_label = "人間" if role == "human" else "アシスタント"
            formatted_text += f"## {role_label} ({timestamp})\n{content}\n\n"
            
        return formatted_text
    
    def extract_user_profile(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        会話履歴からユーザープロファイルを抽出する
        
        Args:
            conversation: 会話履歴
            
        Returns:
            ユーザープロファイル
        """
        if not self.google_api_key:
            return {"error": "Google API Keyが設定されていません。"}
        
        try:
            # 会話履歴をテキスト形式に変換
            conversation_text = self._format_conversation_for_extraction(conversation)
            
            # プロファイル抽出用のプロンプト
            extraction_prompt = f"""
            以下は人間とAIアシスタントの会話履歴です。この会話から人間（ユーザー）に関する情報を抽出してください。
            
            {conversation_text}
            
            以下の3つのカテゴリに分けて情報を抽出してください：
            
            1. profile: ユーザーの基本的なプロフィール情報（生年月日、名前、職業、家族構成など）
            2. context: ユーザーとの会話から得られた一般的な記憶や情報（趣味、関心事、過去の経験など）。複数回の会話がある場合は、それぞれの日時も記録してください。
            3. next: 次回の会話で聞くべき質問や話題（「前回こういう話をしていたけど、その後どうなった？」など）
            
            それぞれのカテゴリについて、できるだけ詳細に、かつ自然な日本語で記述してください。
            情報が不明な場合は「情報なし」と記入してください。
            """
            
            # プロファイル抽出の実行
            try:
                # 新しいAPIを使用
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=extraction_prompt
                )
                extraction_text = response.text
            except Exception as e:
                # エラーが発生した場合はフォールバックモデルを使用
                print(f"Gemini 2.0 Flash使用中にエラー発生: {str(e)}。フォールバックモデルを使用します。")
                response = self.genai_client.models.generate_content(
                    model=self.fallback_model_name,
                    contents=extraction_prompt
                )
                extraction_text = response.text
            
            # 抽出結果をJSON形式に変換
            extraction_result = self._parse_extraction_result(extraction_text)
            
            # タイムスタンプを追加
            extraction_result["timestamp"] = datetime.now().isoformat()
            
            return extraction_result
            
        except Exception as e:
            return {"error": f"プロファイル抽出中にエラーが発生しました: {str(e)}"}
    
    def _parse_extraction_result(self, extraction_text: str) -> Dict[str, Any]:
        """
        抽出結果をJSON形式に変換する
        
        Args:
            extraction_text: 抽出結果のテキスト
            
        Returns:
            JSON形式の抽出結果
        """
        result = {
            "profile": "",
            "context": "",
            "next": ""
        }
        
        current_section = None
        section_content = []
        
        for line in extraction_text.split('\n'):
            line = line.strip()
            
            if not line:
                continue
                
            if "profile:" in line.lower() or "1." in line and "profile" in line.lower():
                current_section = "profile"
                section_content = []
            elif "context:" in line.lower() or "2." in line and "context" in line.lower():
                if current_section and section_content:
                    result[current_section] = '\n'.join(section_content).strip()
                current_section = "context"
                section_content = []
            elif "next:" in line.lower() or "3." in line and "next" in line.lower():
                if current_section and section_content:
                    result[current_section] = '\n'.join(section_content).strip()
                current_section = "next"
                section_content = []
            elif current_section:
                # セクション名や番号を除去
                if line.startswith(f"{current_section}:"):
                    line = line[len(f"{current_section}:"):].strip()
                section_content.append(line)
        
        # 最後のセクションを処理
        if current_section and section_content:
            result[current_section] = '\n'.join(section_content).strip()
        
        return result
    
    def save_user_profile(self, user_profile: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        ユーザープロファイルをJSONファイルに保存する
        
        Args:
            user_profile: ユーザープロファイル
            filename: 保存するファイル名（指定しない場合は現在の日時を使用）
            
        Returns:
            保存したファイルのパス
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_profiles/user_profile_{timestamp}.json"
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(user_profile, f, ensure_ascii=False, indent=2)
            
        return filename
    
    def load_user_profile(self, filename: str) -> Dict[str, Any]:
        """
        ユーザープロファイルをJSONファイルから読み込む
        
        Args:
            filename: 読み込むファイル名
            
        Returns:
            ユーザープロファイル
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"ユーザープロファイルの読み込み中にエラーが発生しました: {str(e)}"}
    
    def generate_user_profile_html(self, user_profile: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        ユーザープロファイルをHTMLファイルに変換する
        
        Args:
            user_profile: ユーザープロファイル
            filename: 保存するファイル名（指定しない場合は現在の日時を使用）
            
        Returns:
            保存したファイルのパス
        """
        if "error" in user_profile:
            return f"<h1>エラー</h1><p>{user_profile['error']}</p>"
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_profiles/user_profile_{timestamp}.html"
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # 改行をHTMLの<br>タグに置換
        profile_html = user_profile.get("profile", "情報なし").replace('\n', '<br>')
        context_html = user_profile.get("context", "情報なし").replace('\n', '<br>')
        next_html = user_profile.get("next", "情報なし").replace('\n', '<br>')
        
        # タイムスタンプのフォーマット
        timestamp_str = datetime.fromisoformat(user_profile.get("timestamp", datetime.now().isoformat())).strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ユーザープロファイル</title>
            <style>
                body {{
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                h1, h2 {{
                    color: #2c3e50;
                }}
                h1 {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                h2 {{
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                    margin-top: 30px;
                }}
                .section {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }}
                .timestamp {{
                    font-size: 0.8em;
                    color: #999;
                    text-align: right;
                    margin-top: 20px;
                }}
                .profile {{
                    border-left: 4px solid #4caf50;
                }}
                .context {{
                    border-left: 4px solid #2196f3;
                }}
                .next {{
                    border-left: 4px solid #ff9800;
                }}
            </style>
        </head>
        <body>
            <h1>ユーザープロファイル</h1>
            
            <div class="container">
                <h2>基本プロフィール</h2>
                <div class="section profile">
                    {profile_html}
                </div>
                
                <h2>コンテキスト情報</h2>
                <div class="section context">
                    {context_html}
                </div>
                
                <h2>次回の会話トピック</h2>
                <div class="section next">
                    {next_html}
                </div>
                
                <div class="timestamp">
                    作成日時: {timestamp_str}
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return filename 