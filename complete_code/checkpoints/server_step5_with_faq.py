"""
社内ITヘルプデスクAIエージェント - MCPサーバー

MCP (Model Context Protocol) の公式Python SDKを使ってMCPサーバーを作る練習用です。

ツール一覧:
- ping:       接続確認用のテストツール
- search_faq: 社内ITヘルプデスクのダミーFAQを検索するツール
"""

from mcp.server.mcpserver import MCPServer

from faq_data import FAQ_DATA

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


if __name__ == "__main__":
    # デフォルトでは stdio (標準入出力) でサーバーを起動する。
    # MCP InspectorやClaudeは、このプログラムをサブプロセスとして起動し
    # 標準入出力を通じてツールの一覧取得・実行をやり取りする。
    mcp.run()
