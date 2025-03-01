import os
import json
from datetime import datetime
from typing import List, Dict, Any

import google.generativeai as genai
from google import genai as genai_new
from dotenv import load_dotenv

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
        self.model_name = "gemini-2.0-flash-lite"
        self.fallback_model_name = "gemini-2.0-flash"

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
以下はUserとAssistantのカジュアルな会話です。
次にUserとはなしたときに会話の記憶として引き出せるよう、以下の3つの情報を自然な文章でまとめてください。

【会話履歴】
{conversation_text}
【システムプロンプト】
{system_prompt}

以下の形式で、箇条書きではなく自然な文章で出力してください：

profile: その人となりや印象に残った特徴を自然な文章で書いてください
episode: この会話で話した内容や印象に残ったことを、ストーリー形式でまとめてください
next: 次回会ったときに話したい話題や、掘り下げたい内容を自然な文章で書いてください

出力例：
profile: 技術に興味があり、特にAIの分野に強い関心を持っている20代後半のエンジニア。話し方は丁寧だが、フランクな雰囲気で会話を楽しむタイプ。

episode: 今回の会話では主にAIの基本的な仕組みについて話し合った。特に機械学習の概念に興味を持っており、実際の応用例について具体的な質問をしていた。説明を聞きながら、自分なりの解釈を加えて理解を深めようとする姿勢が印象的だった。

next: 機械学習の実践的な応用について、特に画像認識や自然言語処理の具体例を紹介すると喜ばれそう。また、AIプロジェクトの始め方についても興味を持っているようなので、初心者向けの学習リソースや実践的なプロジェクトのアイデアを共有できると良いかもしれない。
"""
            try:
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                result_text = response.text
                try:
                    # プロンプトの形式に従ってパースを試みる
                    lines = result_text.strip().split('\n')
                    summary = {
                        "profile": "",
                        "episode": [],
                        "next": []
                    }
                    
                    current_key = None
                    for line in lines:
                        line = line.strip()
                        if line.startswith('profile:'):
                            current_key = 'profile'
                            summary['profile'] = line.replace('profile:', '').strip()
                        elif line.startswith('episode:'):
                            current_key = 'episode'
                        elif line.startswith('next:'):
                            current_key = 'next'
                        elif line and current_key:
                            if line.startswith('- '):
                                line = line[2:]  # 箇条書きの「- 」を削除
                            if current_key == 'episode':
                                summary['episode'].append(line)
                            elif current_key == 'next':
                                summary['next'].append(line)
                            elif current_key == 'profile' and not summary['profile']:
                                summary['profile'] = line

                except Exception as e:
                    summary = {"raw_text": result_text}
            except Exception as e:
                print(f"{self.model_name}でエラー発生: {str(e)}。フォールバックモデルを使用します。")
                try:
                    response = self.genai_client.models.generate_content(
                        model=self.fallback_model_name,
                        contents=prompt
                    )
                    result_text = response.text
                    try:
                        # プロンプトの形式に従ってパースを試みる
                        lines = result_text.strip().split('\n')
                        summary = {
                            "profile": "",
                            "episode": [],
                            "next": []
                        }
                        
                        current_key = None
                        for line in lines:
                            line = line.strip()
                            if line.startswith('profile:'):
                                current_key = 'profile'
                                summary['profile'] = line.replace('profile:', '').strip()
                            elif line.startswith('episode:'):
                                current_key = 'episode'
                            elif line.startswith('next:'):
                                current_key = 'next'
                            elif line and current_key:
                                if line.startswith('- '):
                                    line = line[2:]  # 箇条書きの「- 」を削除
                                if current_key == 'episode':
                                    summary['episode'].append(line)
                                elif current_key == 'next':
                                    summary['next'].append(line)
                                elif current_key == 'profile' and not summary['profile']:
                                    summary['profile'] = line

                    except Exception as e:
                        summary = {"raw_text": result_text}
                except Exception as e2:
                    return {"error": f"会話のまとめ生成中にエラーが発生しました: {str(e2)}"}
            
            # タイムスタンプを追加
            summary["timestamp"] = datetime.now().isoformat()
            
            return summary
        except Exception as e:
            return {"error": f"会話まとめ中にエラーが発生しました: {str(e)}"} 