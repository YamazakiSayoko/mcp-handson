"""
社内ITヘルプデスクAIエージェント - MCPサーバー（最小構成）

このファイルは、MCP (Model Context Protocol) の公式Python SDKを使って
最小構成のMCPサーバーを作る練習用です。

まずは "ping" という動作確認用のツールを1つだけ用意します。
本番用のFAQ検索ツールなどは、この後のステップで追加していきます。
"""

from mcp.server.mcpserver import MCPServer

# MCPサーバーのインスタンスを作成する。
# ここで指定した名前は、MCP Inspectorなどの画面に表示される。
mcp = MCPServer("it-helpdesk-server")


@mcp.tool()
def ping(message: str) -> str:
    """接続確認用のテストツール。渡した文字列をそのまま返す。"""
    return f"pong: {message}"


if __name__ == "__main__":
    # デフォルトでは stdio (標準入出力) でサーバーを起動する。
    # MCP InspectorやClaudeは、このプログラムをサブプロセスとして起動し
    # 標準入出力を通じてツールの一覧取得・実行をやり取りする。
    mcp.run()
