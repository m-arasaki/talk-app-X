import boto3
import time
import os
from boto3.dynamodb.conditions import Key

# クライアントの初期化
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name='ap-northeast-1') # Bedrockが有効なリージョン

TABLE_NAME = 'ChatHistory'
MODEL_ID = 'openai.gpt-oss-safeguard-120b' 

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    
    # 1. 入力の受け取り
    session_id = event.get('session_id', 'default_user')
    user_message = event.get('message', '')
    
    # 2. DynamoDBから過去の会話履歴を取得 (直近10件など)
    response = table.query(
        KeyConditionExpression=Key('session_id').eq(session_id),
        ScanIndexForward=True, # 時系列順
        Limit=10
    )
    items = response.get('Items', [])
    
    # 3. Bedrock用のメッセージ形式に変換
    messages = []
    for item in items:
        messages.append({"role": "user", "content": [{"text": item['user_text']}]})
        messages.append({"role": "assistant", "content": [{"text": item['bot_text']}]})
    
    # 今回のユーザーメッセージを追加
    messages.append({"role": "user", "content": [{"text": user_message}]})
    
    try:
        # 4. Bedrockを呼び出し

        print("Sending to Bedrock:", messages)
        bedrock_response = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages,
            inferenceConfig={"maxTokens": 512, "temperature": 0.7}
        )
        print("returned")

        print("Bedrock Response:", bedrock_response)

        bot_text = bedrock_response['output']['message']['content'][1]['text']
        
        # 5. 会話履歴をDynamoDBに保存
        table.put_item(
            Item={
                'session_id': session_id,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'user_text': user_message,
                'bot_text': bot_text
            }
        )
        
        return {
            'statusCode': 200,
            'body': {'reply': bot_text}
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}