"""
社内ITヘルプデスクAIエージェント - MCPクライアント(ターミナル版)

ターミナルから1つの質問をClaudeに投げて、回答を表示するだけの
シンプルな動作確認用プログラム。実際のやりとりの中身は agent_core.py にまとまっている。
"""

import asyncio

import anthropic
from dotenv import load_dotenv

from agent_core import drive_until_pause, resolve_confirmation

# .env ファイルから ANTHROPIC_API_KEY を読み込む
load_dotenv()


def on_tool_call(name, tool_input):
    print(f"  [Claudeがツールを呼び出しました: {name}({tool_input})]")


def ask_user_to_confirm(pending_blocks) -> bool:
    """確認が必要なツール呼び出しの内容を表示し、ターミナルでy/nの確認を取る。"""
    for block in pending_blocks:
        print("\n--- 以下の内容でチケットを登録しようとしています ---")
        for key, value in block.input.items():
            print(f"  {key}: {value}")
    answer = input("登録してよろしいですか？ (y/n): ")
    return answer.strip().lower() == "y"


async def main():
    claude_client = anthropic.Anthropic()  # ANTHROPIC_API_KEY を環境変数から自動で読み込む

    question = "VPNにつながらないんだけど、どうすればいい？"
    print(f"質問: {question}\n")

    messages = [{"role": "user", "content": question}]

    # Claudeが最終回答を返すまで、ツール実行や確認待ちを繰り返す
    while True:
        result = await drive_until_pause(claude_client, messages, on_tool_call=on_tool_call)

        if result["status"] == "done":
            print("\n=== Claudeの回答 ===")
            print(result["answer"])
            break

        if result["status"] == "needs_confirmation":
            approved = ask_user_to_confirm(result["pending"])
            await resolve_confirmation(messages, result["pending"], result["ready"], approved)
            # 承認/却下の結果をClaudeに伝えるため、ループを続けて再度問い合わせる
            continue


if __name__ == "__main__":
    asyncio.run(main())
