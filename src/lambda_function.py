import os
import json
import requests


def lambda_handler(event, context):
   CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]


   print(event)


   try:
       body = json.loads(event["body"])


       # # eventsが空リスト、または存在しないなら検証リクエスト
       if not body.get("events"):
           print("LINE Webhookの検証リクエストを受信しました。")
           return "OK"
  
       replyToken = body["events"][0]["replyToken"]
       receivedText = body["events"][0]["message"]["text"]
      
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
                   "text": receivedText
               }
           ]
       })
      
       res = requests.post(url=url, headers=header, data=body)
       print(res.text)
      
       return "OK"


   except Exception as e:
       raise(f"エラーが発生しました {e}")

