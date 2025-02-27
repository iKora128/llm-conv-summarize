"""
会話分析のためのモジュール
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

import google.generativeai as genai
from google import genai as genai_new
from dotenv import load_dotenv

from utils.structured_output import SchemaType, create_analysis_schema, create_final_output_schema

# 環境変数の読み込み
load_dotenv()

class ConversationAnalyzer:
    """
    LLM同士の会話を分析するためのクラス
    """
    
    def __init__(self):
        """
        ConversationAnalyzerの初期化
        """
        # API Keyの設定
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # クライアントの初期化
        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
            self.genai_client = genai_new.Client(api_key=self.google_api_key)
        else:
            self.genai_client = None
        
        # モデル設定
        self.model_name = "gemini-2.0-flash"
        self.fallback_model_name = "gemini-1.5-pro"
        
    def _format_conversation_for_analysis(self, conversation: List[Dict[str, Any]]) -> str:
        """
        会話履歴を分析用のテキスト形式に変換する
        
        Args:
            conversation: 会話履歴
            
        Returns:
            分析用のテキスト
        """
        formatted_text = "# 会話履歴\n\n"
        
        for message in conversation:
            role = message["role"]
            content = message["content"]
            
            role_label = "人間" if role == "human" else "アシスタント"
            formatted_text += f"## {role_label}\n{content}\n\n"
            
        return formatted_text
    
    def analyze_conversation(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        会話履歴を分析する
        
        Args:
            conversation: 会話履歴
            
        Returns:
            分析結果
        """
        if not self.google_api_key:
            return {"error": "Google API Keyが設定されていません。"}
        
        try:
            # 会話履歴をテキスト形式に変換
            conversation_text = self._format_conversation_for_analysis(conversation)
            
            # 中間分析用のプロンプト
            intermediate_prompt = f"""
            以下は人間とAIアシスタントの会話履歴です。この会話を詳細に分析してください。
            
            {conversation_text}
            
            分析には以下の項目を含めてください：
            1. 会話から抽出された主張
            2. 会話で扱われたトピック
            3. 会話の要約
            4. 感情分析
            5. 会話の自然さの分析（特に人間役の発言がどれだけ人間らしいか）
            
            分析は客観的かつ詳細に行ってください。
            """
            
            # 中間分析スキーマ
            intermediate_schema = create_analysis_schema()
            
            # 中間分析の実行
            try:
                # 新しいAPIを使用
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=intermediate_prompt,
                    config=genai_new.types.GenerateContentConfig(
                        response_schema=intermediate_schema
                    )
                )
                intermediate_result = response.text
                
                # JSONに変換
                try:
                    intermediate_analysis = json.loads(intermediate_result)
                except:
                    # JSONパースに失敗した場合は、テキストをそのまま使用
                    intermediate_analysis = {"raw_text": intermediate_result}
            except Exception as e:
                # エラーが発生した場合はフォールバックモデルを使用
                print(f"Gemini 2.0 Flash使用中にエラー発生: {str(e)}。フォールバックモデルを使用します。")
                model = genai.GenerativeModel(model_name=self.fallback_model_name)
                response = model.generate_content(
                    intermediate_prompt,
                    generation_config={"response_schema": intermediate_schema}
                )
                
                # JSONに変換
                try:
                    intermediate_analysis = json.loads(response.text)
                except:
                    # JSONパースに失敗した場合は、テキストをそのまま使用
                    intermediate_analysis = {"raw_text": response.text}
            
            # 最終分析用のプロンプト
            final_prompt = f"""
            以下は人間とAIアシスタントの会話履歴の中間分析結果です。この分析結果を元に、最終的な分析レポートを作成してください。
            
            中間分析結果:
            {json.dumps(intermediate_analysis, ensure_ascii=False, indent=2)}
            
            最終分析レポートには以下の項目を含めてください：
            1. 会話のタイトル
            2. 会話の要約
            3. 重要なポイント
            4. 主要なトピック
            5. 人間役の分析（自然さ、強み、弱み、改善提案）
            6. アシスタントの分析（役立ち度、正確さ、強み、弱み）
            7. 会話全体の質の評価
            
            分析は客観的かつ詳細に行ってください。
            """
            
            # 最終分析スキーマ
            final_schema = create_final_output_schema()
            
            # 最終分析の実行
            try:
                # 新しいAPIを使用
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=final_prompt,
                    config=genai_new.types.GenerateContentConfig(
                        response_schema=final_schema
                    )
                )
                final_result = response.text
                
                # JSONに変換
                try:
                    final_analysis = json.loads(final_result)
                except:
                    # JSONパースに失敗した場合は、テキストをそのまま使用
                    final_analysis = {"raw_text": final_result}
            except Exception as e:
                # エラーが発生した場合はフォールバックモデルを使用
                print(f"Gemini 2.0 Flash使用中にエラー発生: {str(e)}。フォールバックモデルを使用します。")
                model = genai.GenerativeModel(model_name=self.fallback_model_name)
                response = model.generate_content(
                    final_prompt,
                    generation_config={"response_schema": final_schema}
                )
                
                # JSONに変換
                try:
                    final_analysis = json.loads(response.text)
                except:
                    # JSONパースに失敗した場合は、テキストをそのまま使用
                    final_analysis = {"raw_text": response.text}
            
            # 中間分析と最終分析を結合
            analysis_result = {
                "intermediate_analysis": intermediate_analysis,
                "final_analysis": final_analysis,
                "meta": {
                    "timestamp": datetime.now().isoformat(),
                    "model": self.model_name
                }
            }
            
            return analysis_result
            
        except Exception as e:
            return {"error": f"会話分析中にエラーが発生しました: {str(e)}"}
    
    def generate_report(self, analysis_result: Dict[str, Any], format: str = "html") -> str:
        """
        分析結果からレポートを生成する
        
        Args:
            analysis_result: 分析結果
            format: レポート形式（html, markdown）
            
        Returns:
            レポート
        """
        if "error" in analysis_result:
            return f"<h1>エラー</h1><p>{analysis_result['error']}</p>" if format == "html" else f"# エラー\n\n{analysis_result['error']}"
            
        if format == "html":
            return self._generate_html_report(analysis_result)
        else:
            return self._generate_markdown_report(analysis_result)
    
    def _generate_html_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        HTMLレポートを生成する
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            HTMLレポート
        """
        final = analysis_result.get("final_analysis", {})
        
        html = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{final.get("title", "会話分析レポート")}</title>
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
                h1, h2, h3 {{
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
                .summary {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #4caf50;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .key-points {{
                    margin: 20px 0;
                }}
                .key-points li {{
                    margin-bottom: 10px;
                }}
                .analysis-section {{
                    margin: 30px 0;
                }}
                .rating {{
                    font-weight: bold;
                    color: #2196f3;
                }}
                .strengths {{
                    color: #4caf50;
                }}
                .weaknesses {{
                    color: #f44336;
                }}
                .topics-list {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                    margin: 15px 0;
                }}
                .topic-tag {{
                    background-color: #e1f5fe;
                    color: #0288d1;
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 0.9em;
                }}
                .overall {{
                    font-size: 1.2em;
                    text-align: center;
                    margin: 30px 0;
                    padding: 15px;
                    background-color: #e8f5e9;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <h1>{final.get("title", "会話分析レポート")}</h1>
            
            <div class="container">
                <h2>概要</h2>
                <div class="summary">
                    {final.get("summary", "要約情報がありません。")}
                </div>
                
                <h2>重要ポイント</h2>
                <ul class="key-points">
        """
        
        for point in final.get("key_points", []):
            html += f"<li>{point}</li>"
            
        html += """
                </ul>
                
                <h2>トピック</h2>
                <div class="topics-list">
        """
        
        for topic in final.get("topics", []):
            html += f'<span class="topic-tag">{topic}</span>'
            
        html += """
                </div>
            </div>
            
            <div class="container analysis-section">
                <h2>人間役の分析</h2>
        """
        
        human = final.get("human_analysis", {})
        html += f"""
                <p>人間らしさ: <span class="rating">{human.get("naturalness", "評価なし")}</span></p>
                
                <h3>強み</h3>
                <ul class="strengths">
        """
        
        for strength in human.get("strengths", []):
            html += f"<li>{strength}</li>"
            
        html += """
                </ul>
                
                <h3>弱み</h3>
                <ul class="weaknesses">
        """
        
        for weakness in human.get("weaknesses", []):
            html += f"<li>{weakness}</li>"
            
        html += f"""
                </ul>
                
                <h3>改善提案</h3>
                <p>{human.get("improvement", "改善提案がありません。")}</p>
            </div>
            
            <div class="container analysis-section">
                <h2>アシスタントの分析</h2>
        """
        
        assistant = final.get("assistant_analysis", {})
        html += f"""
                <p>役立ち度: <span class="rating">{assistant.get("helpfulness", "評価なし")}</span></p>
                <p>正確さ: <span class="rating">{assistant.get("accuracy", "評価なし")}</span></p>
                
                <h3>強み</h3>
                <ul class="strengths">
        """
        
        for strength in assistant.get("strengths", []):
            html += f"<li>{strength}</li>"
            
        html += """
                </ul>
                
                <h3>弱み</h3>
                <ul class="weaknesses">
        """
        
        for weakness in assistant.get("weaknesses", []):
            html += f"<li>{weakness}</li>"
            
        html += f"""
                </ul>
            </div>
            
            <div class="overall">
                <h2>総合評価</h2>
                <p>会話の質: <span class="rating">{final.get("overall_quality", "評価なし")}</span></p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_markdown_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        Markdownレポートを生成する
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            Markdownレポート
        """
        final = analysis_result.get("final_analysis", {})
        
        markdown = f"""# {final.get("title", "会話分析レポート")}

## 概要

{final.get("summary", "要約情報がありません。")}

## 重要ポイント

"""
        
        for point in final.get("key_points", []):
            markdown += f"- {point}\n"
            
        markdown += "\n## トピック\n\n"
        
        for topic in final.get("topics", []):
            markdown += f"- {topic}\n"
            
        human = final.get("human_analysis", {})
        markdown += f"""
## 人間役の分析

人間らしさ: **{human.get("naturalness", "評価なし")}**

### 強み

"""
        
        for strength in human.get("strengths", []):
            markdown += f"- {strength}\n"
            
        markdown += "\n### 弱み\n\n"
        
        for weakness in human.get("weaknesses", []):
            markdown += f"- {weakness}\n"
            
        markdown += f"""
### 改善提案

{human.get("improvement", "改善提案がありません。")}

"""
        
        assistant = final.get("assistant_analysis", {})
        markdown += f"""
## アシスタントの分析

役立ち度: **{assistant.get("helpfulness", "評価なし")}**
正確さ: **{assistant.get("accuracy", "評価なし")}**

### 強み

"""
        
        for strength in assistant.get("strengths", []):
            markdown += f"- {strength}\n"
            
        markdown += "\n### 弱み\n\n"
        
        for weakness in assistant.get("weaknesses", []):
            markdown += f"- {weakness}\n"
            
        markdown += f"""
## 総合評価

会話の質: **{final.get("overall_quality", "評価なし")}**
"""
        
        return markdown 