import json

def lambda_handler(event, context):
    # 1. bodyを取得（空の場合は空の辞書の文字列表記を入れる）
    body_str = event.get("body", "{}")
    
    # 2. bodyが文字列の場合、辞書にパースする
    try:
        if isinstance(body_str, str):
            body = json.loads(body_str)
        else:
            body = body_str
    except Exception:
        body = {}
    
    # 3. メッセージの作成
    name = body.get('name', 'Guest')
    message = f"Hello {name}! From Lambda and GitHub Actions."
    
    # 4. レスポンスの返却
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': message
        }, ensure_ascii=False) # 日本語が含まれる場合は ensure_ascii=False が便利です
    }