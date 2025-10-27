import os
from uuid import uuid4
import json
from flask import Flask
from flask_sock import Sock
from google import genai
from rag_handler import handle_retrieval, get_stream

# --- 初期設定 ---

# FlaskアプリケーションとWebSocketの初期化
app = Flask(__name__)
sock = Sock(app)

client = genai.Client(vertexai=True, project='arvato-developments', location='us-central1')


# --- WebSocketのエンドポイント定義 ---

@sock.route('/ws')
def websocket_connection(ws):
    """
    WebSocket接続を処理する関数。
    クライアントからメッセージを受信し、handleQuestionを介して応答をストリーミング送信する。
    """
    print("クライアントが接続しました。")
    try:
        while True:
            # この部分でメッセージが来るまで停滞しブロック。
            message = ws.receive()
            if message is None:
                # 接続が閉じた場合
                break

            final_context, language = handle_retrieval(message)
            stream = get_stream(inputText = message, docs = final_context, language = language)

            # この一連のやり取りにユニークなIDを付与
            response_id = str(uuid4())
            print(f"リクエスト受信 (ID: {response_id}): {message}")

            # handleQuestionジェネレータを使って、ストリーミング応答を送信
            for chunk in stream:
                response_data = {
                    "id": response_id,
                    "chunk": chunk,
                    "isFinal": False
                }
                ws.send(json.dumps(response_data))

            ws.send(json.dumps({"id": response_id, "chunk": '', "isFinal": False}))

    except Exception as e:
        print(f"WebSocketエラー: {e}")
    finally:
        print("クライアントが切断しました。")


# --- Flaskサーバーの起動 ---

if __name__ == '__main__':
    # 開発用のサーバーを起動
    # 本番環境ではGunicornやuWSGIなどのWSGIサーバーを使用してください
    app.run(host='0.0.0.0', port=5000, debug=True)