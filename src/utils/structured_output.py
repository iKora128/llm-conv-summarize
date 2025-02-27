"""
構造化出力のためのユーティリティ
"""
from enum import Enum
from typing import Dict, List, Any, Optional, Union

class SchemaType(str, Enum):
    """
    JSONスキーマのタイプ
    """
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

class ResponseSchema:
    """
    構造化出力のためのスキーマ定義
    """
    def __init__(
        self,
        type: SchemaType,
        properties: Optional[Dict[str, Any]] = None,
        items: Optional[Dict[str, Any]] = None,
        required: Optional[List[str]] = None,
        description: Optional[str] = None
    ):
        self.type = type
        self.properties = properties
        self.items = items
        self.required = required
        self.description = description
        
    def to_dict(self) -> Dict[str, Any]:
        """
        スキーマをJSON形式の辞書に変換する
        
        Returns:
            JSON形式の辞書
        """
        schema = {"type": self.type}
        
        if self.properties:
            schema["properties"] = self.properties
            
        if self.items:
            schema["items"] = self.items
            
        if self.required:
            schema["required"] = self.required
            
        if self.description:
            schema["description"] = self.description
            
        return schema

def create_analysis_schema() -> Dict[str, Any]:
    """
    中間分析用のスキーマを作成する
    
    Returns:
        中間分析用のスキーマ
    """
    return {
        "type": SchemaType.OBJECT,
        "properties": {
            "claims": {
                "type": SchemaType.ARRAY,
                "description": "会話から抽出された主張",
                "items": {
                    "type": SchemaType.OBJECT,
                    "properties": {
                        "text": {
                            "type": SchemaType.STRING,
                            "description": "主張の内容"
                        },
                        "source": {
                            "type": SchemaType.STRING,
                            "description": "主張の情報源（人間かアシスタントか）"
                        },
                        "evidence": {
                            "type": SchemaType.STRING,
                            "description": "主張の根拠となる会話内の発言"
                        },
                        "certainty": {
                            "type": SchemaType.STRING,
                            "description": "主張の確からしさ（高い、中程度、低い）"
                        }
                    },
                    "required": ["text", "source", "evidence", "certainty"]
                }
            },
            "topics": {
                "type": SchemaType.ARRAY,
                "description": "会話で扱われたトピック",
                "items": {
                    "type": SchemaType.OBJECT,
                    "properties": {
                        "name": {
                            "type": SchemaType.STRING,
                            "description": "トピック名"
                        },
                        "description": {
                            "type": SchemaType.STRING,
                            "description": "トピックの説明"
                        },
                        "relevance": {
                            "type": SchemaType.STRING,
                            "description": "会話全体におけるトピックの関連性（高い、中程度、低い）"
                        }
                    },
                    "required": ["name", "description", "relevance"]
                }
            },
            "summary": {
                "type": SchemaType.STRING,
                "description": "会話の要約（500文字程度）"
            },
            "sentiment": {
                "type": SchemaType.OBJECT,
                "description": "会話の感情分析",
                "properties": {
                    "human": {
                        "type": SchemaType.STRING,
                        "description": "人間の感情（ポジティブ、ニュートラル、ネガティブなど）"
                    },
                    "assistant": {
                        "type": SchemaType.STRING,
                        "description": "アシスタントの感情（ポジティブ、ニュートラル、ネガティブなど）"
                    },
                    "overall": {
                        "type": SchemaType.STRING,
                        "description": "会話全体の感情的な雰囲気"
                    }
                },
                "required": ["human", "assistant", "overall"]
            },
            "naturalness": {
                "type": SchemaType.OBJECT,
                "description": "会話の自然さの分析",
                "properties": {
                    "human_like": {
                        "type": SchemaType.STRING,
                        "description": "人間役の発言がどれだけ人間らしいか（1-10のスケール）"
                    },
                    "reasoning": {
                        "type": SchemaType.STRING,
                        "description": "人間らしさの評価理由"
                    },
                    "improvement": {
                        "type": SchemaType.STRING,
                        "description": "より人間らしくするための改善点"
                    }
                },
                "required": ["human_like", "reasoning", "improvement"]
            }
        },
        "required": ["claims", "topics", "summary", "sentiment", "naturalness"]
    }

def create_final_output_schema() -> Dict[str, Any]:
    """
    最終出力用のスキーマを作成する
    
    Returns:
        最終出力用のスキーマ
    """
    return {
        "type": SchemaType.OBJECT,
        "properties": {
            "title": {
                "type": SchemaType.STRING,
                "description": "会話の内容を表すタイトル"
            },
            "summary": {
                "type": SchemaType.STRING,
                "description": "会話の要約（1000文字程度）"
            },
            "key_points": {
                "type": SchemaType.ARRAY,
                "description": "会話の重要なポイント",
                "items": {
                    "type": SchemaType.STRING
                }
            },
            "topics": {
                "type": SchemaType.ARRAY,
                "description": "会話で扱われた主要なトピック",
                "items": {
                    "type": SchemaType.STRING
                }
            },
            "human_analysis": {
                "type": SchemaType.OBJECT,
                "description": "人間役の分析",
                "properties": {
                    "naturalness": {
                        "type": SchemaType.STRING,
                        "description": "人間らしさの評価（1-10のスケール）"
                    },
                    "strengths": {
                        "type": SchemaType.ARRAY,
                        "description": "人間らしい点",
                        "items": {
                            "type": SchemaType.STRING
                        }
                    },
                    "weaknesses": {
                        "type": SchemaType.ARRAY,
                        "description": "人間らしくない点",
                        "items": {
                            "type": SchemaType.STRING
                        }
                    },
                    "improvement": {
                        "type": SchemaType.STRING,
                        "description": "より人間らしくするための提案"
                    }
                },
                "required": ["naturalness", "strengths", "weaknesses", "improvement"]
            },
            "assistant_analysis": {
                "type": SchemaType.OBJECT,
                "description": "アシスタントの分析",
                "properties": {
                    "helpfulness": {
                        "type": SchemaType.STRING,
                        "description": "役立ち度の評価（1-10のスケール）"
                    },
                    "accuracy": {
                        "type": SchemaType.STRING,
                        "description": "情報の正確さの評価（1-10のスケール）"
                    },
                    "strengths": {
                        "type": SchemaType.ARRAY,
                        "description": "アシスタントの強み",
                        "items": {
                            "type": SchemaType.STRING
                        }
                    },
                    "weaknesses": {
                        "type": SchemaType.ARRAY,
                        "description": "アシスタントの弱み",
                        "items": {
                            "type": SchemaType.STRING
                        }
                    }
                },
                "required": ["helpfulness", "accuracy", "strengths", "weaknesses"]
            },
            "overall_quality": {
                "type": SchemaType.STRING,
                "description": "会話全体の質の評価（1-10のスケール）"
            }
        },
        "required": ["title", "summary", "key_points", "topics", "human_analysis", "assistant_analysis", "overall_quality"]
    } 