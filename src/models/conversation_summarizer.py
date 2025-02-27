import os
import json
from datetime import datetime
from typing import List, Dict, Any

import google.generativeai as genai
from google import genai as genai_new
from dotenv import load_dotenv

from utils.structured_output import create_conversation_summary_schema

# 環境変数の読み込み
load_dotenv()

class ConversationSummarizer:
    """
    会話のまとめを作成するクラス
    """
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
            self.genai_client = genai_new.Client(api_key=self.google_api_key)
        else:
            self.genai_client = None
        
        # モデル設定
        self.model_name = "gemini-2.0-flash"
        self.fallback_model_name = "gemini-1.5-pro"

    def _format_conversation(self, conversation: List[Dict[str, Any]]) -> str:
        """
        会話履歴をカジュアルな日本語のテキストに変換する
        """
        formatted_text = "会話の履歴だよ:\n\n"
        for msg in conversation:
            role = msg.get("role", "")
            content = msg.get("content", "")
            role_label = "人間" if role == "human" else "アシスタント"
            formatted_text += f"{role_label}: {content}\n\n"
        return formatted_text

    def summarize_conversation(self, conversation: List[Dict[str, Any]], system_prompt: str) -> Dict[str, Any]:
        """
        会話履歴とシステムプロンプトから会話のまとめを生成する

        Args:
            conversation: 会話履歴
            system_prompt: 利用されたシステムプロンプト

        Returns:
            まとめ結果（辞書形式）
        """
        if not self.google_api_key:
            return {"error": "Google API Keyが設定されていません。"}

        try:
            conversation_text = self._format_conversation(conversation)
            prompt = f"""
以下はLLM同士のカジュアルな会話だよ。

【会話履歴】
{conversation_text}
【システムプロンプト】
{system_prompt}

上記の会話をまとめるね。以下の3つの情報を含めて、日常会話のようなフランクな口調でまとめて:
1. profile: 基本的なプロフィール（例: 生年月日、履歴書的な情報）
2. episode: 会話のエピソード記憶。可能ならタイムスタンプも入れて、回ごとに記録してね。
3. next: 次回会ったときに聞くと喜ばれる話題
"""
            
            summary_schema = create_conversation_summary_schema()
            
            try:
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=genai_new.types.GenerateContentConfig(
                        response_schema=summary_schema
                    )
                )
                result_text = response.text
                try:
                    summary = json.loads(result_text)
                except Exception as e:
                    summary = {"raw_text": result_text}
            except Exception as e:
                print(f"{self.model_name}でエラー発生: {str(e)}。フォールバックモデルを使用します。")
                try:
                    response = self.genai_client.models.generate_content(
                        model=self.fallback_model_name,
                        contents=prompt,
                        config=genai_new.types.GenerateContentConfig(
                            response_schema=summary_schema
                        )
                    )
                    result_text = response.text
                    try:
                        summary = json.loads(result_text)
                    except Exception as e:
                        summary = {"raw_text": result_text}
                except Exception as e2:
                    return {"error": f"会話のまとめ生成中にエラーが発生しました: {str(e2)}"}
            
            # タイムスタンプを追加
            summary["timestamp"] = datetime.now().isoformat()
            
            return summary
        except Exception as e:
            return {"error": f"会話まとめ中にエラーが発生しました: {str(e)}"} 