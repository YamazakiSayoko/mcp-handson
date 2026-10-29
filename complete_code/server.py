"""
社内ITヘルプデスクAIエージェント - MCPサーバー

MCP (Model Context Protocol) の公式Python SDKを使ってMCPサーバーを作る練習用です。

ツール一覧:
- ping:            接続確認用のテストツール
- search_faq:      社内ITヘルプデスクのダミーFAQを検索するツール
- register_ticket: 問い合わせ内容をチケットとしてJSONファイルに保存するツール

注意: register_ticket は「実行すると実際にファイルへ書き込む」更新系のツールです。
このツールを安全に使うため、Claude APIと接続するクライアント側(agent_core.py)で
「ユーザーの確認が取れるまでは実行しない」という制御を別途入れています。
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from faq_data import FAQ_DATA

TICKETS_FILE = Path(__file__).parent / "tickets.json"

# MCPサーバーのインスタンスを作成する。
# ここで指定した名前は、MCP Inspectorなどの画面に表示される。
mcp = MCPServer("it-helpdesk-server")


@mcp.tool()
def ping(message: str) -> str:
    """接続確認用のテストツール。渡した文字列をそのまま返す。"""
    return f"pong: {message}"


@mcp.tool()
def search_faq(query: str) -> str:
    """社内ITヘルプデスクのFAQを検索する。

    VPN接続、パスワードのリセット、社内Wi-Fi接続など、よくある社内IT問い合わせ
    について、ユーザーの質問文(query)に関連するFAQが見つかれば、その対処方法を返す。
    該当するFAQが見つからない場合は、その旨を伝える文字列を返す。

    例: 「VPNにつながらない」「パスワードを忘れた」「Wi-Fiに接続できない」
    """
    query_lower = query.lower()
    matched = [
        entry
        for entry in FAQ_DATA
        if any(keyword.lower() in query_lower for keyword in entry["keywords"])
    ]

    if not matched:
        return "該当するFAQが見つかりませんでした。情報システム部のヘルプデスクへお問い合わせください。"

    results = [
        f"【{entry['category']}】{entry['question']}\n{entry['answer']}"
        for entry in matched
    ]
    return "\n\n".join(results)


@mcp.tool()
def register_ticket(category: str, description: str) -> str:
    """問い合わせ内容をヘルプデスクのチケットとしてローカルのJSONファイルに登録する。

    このツールは実際にファイルへ書き込みを行う更新系のツールのため、
    クライアント側のアプリケーションは、ユーザー本人の明確な同意を得てから
    このツールを呼び出す設計になっている(Claudeが勝手に実行することはない)。

    引数:
        category:    問い合わせの分類（例: "VPN", "パスワード", "Wi-Fi", "その他"）
        description: 問い合わせ内容の詳細
    """
    tickets = []
    if TICKETS_FILE.exists():
        tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))

    new_ticket = {
        "id": len(tickets) + 1,
        "category": category,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tickets.append(new_ticket)
    TICKETS_FILE.write_text(json.dumps(tickets, ensure_ascii=False, indent=2), encoding="utf-8")

    return f"チケットを登録しました（チケット番号: {new_ticket['id']}）"


if __name__ == "__main__":
    # デフォルトでは stdio (標準入出力) でサーバーを起動する。
    # MCP InspectorやClaudeは、このプログラムをサブプロセスとして起動し
    # 標準入出力を通じてツールの一覧取得・実行をやり取りする。
    mcp.run()
