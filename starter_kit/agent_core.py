"""
社内ITヘルプデスクAIエージェント - Claude API と MCPサーバーをつなぐ共通ロジック

client.py（ターミナル版）と app.py（ブラウザ版/Streamlit）の
両方から読み込んで使う、共通部分をまとめたモジュール。

register_ticket のような「実際にファイルを書き換える」更新系のツールは、
Claudeが呼びたいと言っても即座には実行しない。TOOLS_REQUIRING_CONFIRMATION に
含まれるツールは、いったん呼び出し元(client.py / app.py)に処理を差し戻し、
ユーザーの明確な承認が得られた場合にのみ resolve_confirmation() で実行する。
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "claude-haiku-4-5"

# server.py は、実行時のカレントディレクトリに関わらず、
# このファイル(agent_core.py)と同じフォルダにあるものを使う
SERVER_SCRIPT_PATH = str(Path(__file__).parent / "server.py")

# ここに含まれるツールは、Claudeが呼び出しを要求しても即実行せず、
# ユーザーの確認が取れるまで保留する
TOOLS_REQUIRING_CONFIRMATION = {"register_ticket"}


def mcp_tool_to_claude_tool(mcp_tool):
    """MCPサーバーのツール定義を、Claude APIが理解できる形式(辞書)に変換する。"""
    return {
        "name": mcp_tool.name,
        "description": mcp_tool.description or "",
        "input_schema": mcp_tool.input_schema,
    }


@asynccontextmanager
async def mcp_session():
    """MCPサーバー(server.py)をサブプロセスとして起動し、接続済みのセッションを返す。"""
    # sys.executable を使うことで、今実行中のPython(=仮想環境のPython)を確実に使う
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT_PATH])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def _execute_tools(session: ClientSession, blocks: list) -> list:
    """tool_useブロックのリストを実際に実行し、tool_resultのリストを返す。"""
    results = []
    for block in blocks:
        result = await session.call_tool(block.name, block.input)
        result_text = "".join(content.text for content in result.content if hasattr(content, "text"))
        results.append({"type": "tool_result", "tool_use_id": block.id, "content": result_text})
    return results


async def step_conversation(claude_client: anthropic.Anthropic, messages: list, on_tool_call=None) -> dict:
    """Claudeに1回問い合わせる。確認不要なツールはその場で実行してしまう。

    戻り値は以下のいずれか:
      {"status": "done", "answer": str}
          Claudeが最終回答を返した。
      {"status": "needs_confirmation", "pending": [...], "ready": [...]}
          確認が必要なツール呼び出し(pending)が含まれていた。
          同じターンで一緒に要求された確認不要なツール(ready)はまだ未実行。
          呼び出し元はユーザーに確認を取った上で resolve_confirmation() を呼ぶこと。
      {"status": "continue"}
          確認不要なツールだけが呼ばれ、その場で実行済み。
          呼び出し元はもう一度この関数を呼び出してループを続けること。
    """
    async with mcp_session() as session:
        tools_result = await session.list_tools()
        claude_tools = [mcp_tool_to_claude_tool(t) for t in tools_result.tools]

        response = claude_client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=claude_tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            final_text = next((block.text for block in response.content if block.type == "text"), "")
            return {"status": "done", "answer": final_text}

        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

        if on_tool_call is not None:
            for block in tool_use_blocks:
                on_tool_call(block.name, block.input)

        pending = [b for b in tool_use_blocks if b.name in TOOLS_REQUIRING_CONFIRMATION]
        ready = [b for b in tool_use_blocks if b.name not in TOOLS_REQUIRING_CONFIRMATION]

        if pending:
            return {"status": "needs_confirmation", "pending": pending, "ready": ready}

        tool_results = await _execute_tools(session, ready)
        messages.append({"role": "user", "content": tool_results})
        return {"status": "continue"}


async def resolve_confirmation(messages: list, pending: list, ready: list, approved: bool) -> None:
    """needs_confirmation で保留されたツール呼び出しを解決する。

    approved=True なら実際にMCPツールを実行し、False ならキャンセル扱いにする。
    結果はmessagesに追加される(戻り値はなし。呼び出し元はこの後 drive_until_pause を
    再度呼び出して、Claudeから最終的な回答を受け取ること)。
    """
    async with mcp_session() as session:
        tool_results = await _execute_tools(session, ready)

        for block in pending:
            if approved:
                result = await session.call_tool(block.name, block.input)
                result_text = "".join(content.text for content in result.content if hasattr(content, "text"))
            else:
                result_text = "ユーザーがキャンセルしました。この操作は実行されていません。"
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result_text})

    messages.append({"role": "user", "content": tool_results})


async def drive_until_pause(claude_client: anthropic.Anthropic, messages: list, on_tool_call=None) -> dict:
    """status が 'done' か 'needs_confirmation' になるまで step_conversation を繰り返す。"""
    while True:
        result = await step_conversation(claude_client, messages, on_tool_call=on_tool_call)
        if result["status"] != "continue":
            return result
