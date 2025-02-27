"""
会話履歴をHTMLに変換するユーティリティ
"""
from datetime import datetime
from typing import List, Dict, Any

def generate_chat_html(conversation: List[Dict[str, Any]], title: str = "LLM会話履歴") -> str:
    """
    会話履歴をHTMLに変換する
    
    Args:
        conversation: 会話履歴
        title: HTMLのタイトル
        
    Returns:
        HTML文字列
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
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
            .chat-container {{
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
            }}
            .message {{
                margin-bottom: 15px;
                padding: 10px 15px;
                border-radius: 18px;
                max-width: 80%;
                position: relative;
            }}
            .human {{
                background-color: #e1ffc7;
                margin-left: auto;
                border-bottom-right-radius: 0;
            }}
            .assistant {{
                background-color: #f0f0f0;
                margin-right: auto;
                border-bottom-left-radius: 0;
            }}
            .timestamp {{
                font-size: 0.7em;
                color: #999;
                margin-top: 5px;
                text-align: right;
            }}
            h1 {{
                text-align: center;
                color: #2c3e50;
            }}
            .role-label {{
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .human .role-label {{
                color: #4caf50;
            }}
            .assistant .role-label {{
                color: #2196f3;
            }}
            .meta-info {{
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 20px;
                font-size: 0.9em;
            }}
            .meta-info h2 {{
                margin-top: 0;
                font-size: 1.2em;
                color: #2c3e50;
            }}
            .meta-info p {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
    """
    
    # メタ情報があれば追加
    if len(conversation) > 0 and "meta" in conversation[0]:
        meta = conversation[0]["meta"]
        html_content += """
        <div class="meta-info">
            <h2>会話情報</h2>
        """
        
        if "assistant_model" in meta:
            html_content += f"<p><strong>アシスタントモデル:</strong> {meta['assistant_model']}</p>"
        
        if "human_model" in meta:
            html_content += f"<p><strong>人間役モデル:</strong> {meta['human_model']}</p>"
            
        if "timestamp" in meta:
            timestamp = datetime.fromisoformat(meta["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            html_content += f"<p><strong>作成日時:</strong> {timestamp}</p>"
            
        html_content += "</div>"
    
    html_content += '<div class="chat-container">'
    
    for message in conversation:
        if "role" not in message:
            continue
            
        role = message["role"]
        content = message["content"]
        timestamp = ""
        
        if "timestamp" in message:
            timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        
        role_label = "人間" if role == "human" else "アシスタント"
        
        html_content += f"""
        <div class="message {role}">
            <div class="role-label">{role_label}</div>
            <div class="content">{content.replace('\n', '<br>')}</div>
            <div class="timestamp">{timestamp}</div>
        </div>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    return html_content 