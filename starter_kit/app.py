"""
社内ITヘルプデスクAIエージェント - ブラウザUI (Streamlit)

ブラウザから自然言語で質問すると、Claudeが判断してMCPサーバーの
ツール(FAQ検索など)を呼び出し、その結果をもとに回答するチャット画面。

register_ticket のような更新系のツールが呼ばれた場合は、
「登録する/キャンセル」ボタンでユーザーの確認を取ってから実行する。
"""

import asyncio

import anthropic
import streamlit as st
from dotenv import load_dotenv

from agent_core import TOOLS_REQUIRING_CONFIRMATION, drive_until_pause, resolve_confirmation

load_dotenv()

st.set_page_config(page_title="社内ITヘルプデスク", page_icon="💬")
st.title("💬 社内ITヘルプデスクAIエージェント")
st.caption("VPN・パスワードリセット・Wi-Fi接続など、ITに関する質問を入力してください。")

# Claude APIクライアントは一度だけ作成し、session_stateに保存して使い回す
if "claude_client" not in st.session_state:
    st.session_state.claude_client = anthropic.Anthropic()

# Claudeに送る正式な会話履歴(Claude API形式)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 画面に表示するための簡易ログ
if "display_log" not in st.session_state:
    st.session_state.display_log = []

# 確認待ちのツール呼び出し情報(Noneなら確認待ちなし)
if "pending" not in st.session_state:
    st.session_state.pending = None


def add_message_to_log(role, text):
    st.session_state.display_log.append({"type": "message", "role": role, "text": text})


def on_tool_call(name, tool_input):
    # 確認が必要なツールは、この後の確認UIでまとめて表示するので、ここでは表示しない
    if name in TOOLS_REQUIRING_CONFIRMATION:
        return
    st.session_state.display_log.append({"type": "tool_call", "name": name, "input": tool_input})


def handle_result(result):
    """drive_until_pause() の戻り値に応じて、画面表示用の状態を更新する。"""
    if result["status"] == "done":
        add_message_to_log("assistant", result["answer"])
    elif result["status"] == "needs_confirmation":
        st.session_state.pending = result


# --- これまでの会話を画面に表示する ---
for item in st.session_state.display_log:
    if item["type"] == "tool_call":
        st.chat_message("assistant").info(f"🔧 ツール呼び出し: {item['name']}({item['input']})")
    else:
        st.chat_message(item["role"]).write(item["text"])

# --- 確認待ちのツール呼び出しがあれば、確認UIを表示する ---
if st.session_state.pending is not None:
    pending_blocks = st.session_state.pending["pending"]

    with st.chat_message("assistant"):
        st.warning("⚠️ 以下の内容で処理を実行しようとしています。内容を確認してください。")
        for block in pending_blocks:
            st.write(f"**ツール**: {block.name}")
            for key, value in block.input.items():
                st.write(f"- **{key}**: {value}")

        col1, col2 = st.columns(2)
        approved = col1.button("✅ 登録する", use_container_width=True)
        cancelled = col2.button("❌ キャンセル", use_container_width=True)

    if approved or cancelled:
        pending_info = st.session_state.pending
        add_message_to_log("user", "(確認結果) " + ("登録する" if approved else "キャンセル"))

        with st.spinner("処理しています..."):
            asyncio.run(
                resolve_confirmation(
                    st.session_state.messages,
                    pending_info["pending"],
                    pending_info["ready"],
                    approved,
                )
            )
            st.session_state.pending = None

            result = asyncio.run(
                drive_until_pause(st.session_state.claude_client, st.session_state.messages, on_tool_call=on_tool_call)
            )
        handle_result(result)
        st.rerun()

# --- 質問の入力欄(確認待ちの間は入力できないようにする) ---
user_input = st.chat_input(
    "質問を入力してください（例: VPNにつながらない）",
    disabled=st.session_state.pending is not None,
)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    add_message_to_log("user", user_input)
    st.chat_message("user").write(user_input)

    with st.spinner("Claudeが考えています..."):
        result = asyncio.run(
            drive_until_pause(st.session_state.claude_client, st.session_state.messages, on_tool_call=on_tool_call)
        )
    handle_result(result)
    st.rerun()
