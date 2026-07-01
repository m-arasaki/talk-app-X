import os
import json
import requests
import boto3
import time

from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError

CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
handler = WebhookHandler(CHANNEL_SECRET)

dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client(
    "bedrock-runtime",
    region_name="ap-northeast-1"
)

TABLE_NAME = 'ChatHistory'
MODEL_ID = "openai.gpt-oss-safeguard-120b"

# 署名検証用の関数
def verification(body, signature):
    """ Webhookからのリクエストの正当性をチェックし、ハンドラに応答処理を移譲する """

    try:
        handler.handle(body, signature)
        return True
    # 署名検証で失敗した場合、例外を出す。
    except InvalidSignatureError as e:
        print(f"Invalid Signature. Error Message: {e}")
        return False

def generate_response(user_message):

    body = {
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ],
        "max_completion_tokens": 500
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body)
    )

    result = json.loads(response["body"].read())

    return result["choices"][0]["message"]["content"]


def lambda_handler(event, context):
    
    # 署名処理
   body = event["body"]
   signature = event["headers"]["x-line-signature"]
   if not verification(body, signature):
       return "Bad Request"


   CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
   table = dynamodb.Table(TABLE_NAME)

   print(event)

   try:
       body = json.loads(event["body"])

       session_id = body["events"][0]["source"]["userId"]

       # # eventsが空リスト、または存在しないなら検証リクエスト
       if not body.get("events"):
           print("LINE Webhookの検証リクエストを受信しました。")
           return "OK"
  
       replyToken = body["events"][0]["replyToken"]
       receivedText = body["events"][0]["message"]["text"]

       llm_response = generate_response(receivedText)
      
       url = "https://api.line.me/v2/bot/message/reply"
       header = {
           "Content-Type": "application/json",
           "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
       }
       body = json.dumps({
           "replyToken": replyToken,
           "messages": [
               {
                   "type": "text",
                   "text": llm_response
               }
           ]
       })
      
       res = requests.post(url=url, headers=header, data=body)
       print(res.text)

       table.put_item(
           Item={
               'session_id': session_id,
               'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
               'user_text': receivedText,
               'bot_text': llm_response
           }
       )

      
       return "OK"


   except Exception as e:
       print(f"エラーが発生しました {e}")