# スターターキット（参加者用）

このフォルダの**中身**を、作業用フォルダ（`mcp-helpdesk-agent`）にコピーして使います。
`starter_kit` フォルダごとではなく、中に入っているファイルだけをコピーしてください。

## 含まれているもの
- `requirements.txt` … 必要なライブラリの一覧（`pip install -r requirements.txt` でまとめてインストール）
- `faq_data.py` … ダミーのFAQデータ（そのまま使用）
- `agent_core.py` … Claude APIとMCPサーバーをつなぐコード（完成済み）
- `client.py` … ターミナル版のクライアント（完成済み）
- `app.py` … ブラウザ版のチャット画面（Streamlit、完成済み）
- `.env.example` … APIキーを書く `.env` の見本

## 含まれていないもの
- `server.py` … **ハンズオン本編で、自分で作成します**（これが今回の学習の中心です）
- `venv/` … 作業用フォルダで、自分で作成します
- `.env` … `.env.example` をコピーして、自分で作成します

## .env の作り方
作業用フォルダで次のコマンドを実行し、`your-api-key-here` の部分を、当日共有されたAPIキーに置き換えて保存します。

```powershell
Copy-Item .env.example .env
code .env
```

APIキーは、画面共有やスクリーンショットに写さないでください。
