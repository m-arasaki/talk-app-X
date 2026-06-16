import os
import json
import requests
import boto3
import time

dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client(
    "bedrock-runtime",
    region_name="ap-northeast-1"
)

TABLE_NAME = 'ChatHistory'
MODEL_ID = "openai.gpt-oss-safeguard-120b"


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