# 完成版コード（答え合わせ・追いつき用）

ハンズオンで詰まったときや、答え合わせをしたいときに使います。
まずは自分で書いてみて、どうしても先に進めないときに使ってください。

## 構成

| ファイル | 内容 | 使う場面 |
|---|---|---|
| `checkpoints/server_step3_ping_only.py` | `ping` ツールのみの最小構成 | `ping` ツールを作るところで詰まったとき |
| `checkpoints/server_step5_with_faq.py` | `ping` + `search_faq` | FAQ検索ツール（`search_faq`）を作るところで詰まったとき |
| `server.py` | `ping` + `search_faq` + `register_ticket`（発展課題まで含む完成形） | 発展課題に取り組むとき、最終形を確認したいとき |
| `agent_core.py` / `client.py` / `app.py` / `faq_data.py` / `.env.example` | スターターキットと同じ内容 | スターターキットのものを使います |

ファイル名の `step3`・`step5` は、教材を作り始めたころの番号です。スライドのSTEP3・STEP5とは対応していません。

## 使い方
作業用フォルダ（`mcp-helpdesk-agent`）の `server.py` を、該当するファイルの中身で置き換えると、その段階に追いつけます。
（例：`checkpoints/server_step5_with_faq.py` をコピーして名前を `server.py` に変え、作業用フォルダの `server.py` に上書きする）

必要なライブラリは、`starter_kit/requirements.txt` でインストールしたものと同じです。
