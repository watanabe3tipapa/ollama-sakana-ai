"""
GradioベースのMVP UIで、Ollamaモデル（ローカル）を実行します。
- ローカルでOllamaが起動している必要があります（デフォルト: http://localhost:11434）
- デフォルトモデル: llama3.2
"""

import json
import os
import time
from typing import Dict, List

import gradio as gr
import httpx
from playwright.sync_api import sync_playwright

DEFAULT_MODEL = "qwen3.5"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_ollama_models() -> List[str]:
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{OLLAMA_BASE_URL}/api/tags")
        if resp.status_code == 200:
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return [DEFAULT_MODEL]


def refresh_models():
    return gr.Dropdown(choices=get_ollama_models())


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_ollama_models = get_ollama_models()
SESSION_HISTORY: Dict[str, List[Dict]] = {}
_active_requests: Dict[str, Dict] = {}


# ---- Helpers ----
def make_session_id() -> str:
    return str(int(time.time() * 1000))


def add_history(user_id: str, item: dict):
    SESSION_HISTORY.setdefault(user_id, []).insert(0, item)
    SESSION_HISTORY[user_id] = SESSION_HISTORY[user_id][:50]


def get_history(user_id: str):
    return SESSION_HISTORY.get(user_id, [])


def call_ollama_model(model_id: str, prompt: str, params: dict) -> tuple[bool, str]:
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model_id,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
            "num_predict": params.get("max_new_tokens", 128),
        },
    }
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, json=payload)
    except httpx.RequestError as e:
        return False, f"[NETWORK_ERROR] {e}"
    if resp.status_code != 200:
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        return False, f"[API_ERROR {resp.status_code}] {err}"
    try:
        data = resp.json()
        if "response" in data:
            return True, data["response"]
        return True, json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return False, f"[PARSE_ERROR] {e}"


def stream_chunks(
    text: str, session_id: str, chunk_size: int = 80, delay: float = 0.03
):
    buf = ""
    for i in range(0, len(text), chunk_size):
        if session_id in _active_requests and _active_requests[session_id].get(
            "cancelled"
        ):
            yield "[CANCELLED]"
            return
        chunk = text[i : i + chunk_size]
        buf += chunk
        yield buf
        time.sleep(delay)
    yield "[DONE]"


# ---- Gradio callbacks ----
SAMPLES = [
    {"title": "フリートーク", "prompt": ""},
    {"title": "要約", "prompt": "以下を200文字以内で日本語で要約してください：\n\n"},
    {"title": "質問応答", "prompt": "ユーザー: {question}\nアシスタント:"},
    {"title": "メール下書き", "prompt": "宛先: {name}\n件名: {subject}\n本文:\n"},
    {"title": "メッセージ下書き", "prompt": "送信先: {recipient}\n內容:\n"},
]


def on_model_type_change(model_type):
    if model_type == "Sakana AI":
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        )
    return gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)


def on_sample_change(choice):
    for s in SAMPLES:
        if s["title"] == choice:
            return s["prompt"]
    return ""


def start_generation(
    model_id,
    prompt,
    temperature,
    top_p,
    max_new_tokens,
    save_history,
    user_id,
):
    if not model_id:
        yield "", "モデルを選択してください", "{}", make_session_id()
        return
    session_id = make_session_id()
    _active_requests[session_id] = {"cancelled": False}
    params = {
        "temperature": float(temperature),
        "top_p": float(top_p),
        "max_new_tokens": int(max_new_tokens),
    }
    ok, result = call_ollama_model(model_id, prompt, params)
    meta = json.dumps(
        {
            "model": model_id,
            "temperature": temperature,
            "top_p": top_p,
            "max_new_tokens": max_new_tokens,
        },
        ensure_ascii=False,
    )
    if not ok:
        _active_requests.pop(session_id, None)
        yield "", f"{result}", meta, session_id  # error -> show in output box
        return
    # Stream simulated
    for partial in stream_chunks(result, session_id):
        if partial == "[CANCELLED]":
            yield partial, "", meta, session_id
            _active_requests.pop(session_id, None)
            return
        if partial == "[DONE]":
            # finalization: save history if requested
            if save_history:
                add_history(
                    user_id,
                    {
                        "model": model_id,
                        "prompt": prompt,
                        "output": result,
                        "meta": meta,
                        "time": time.time(),
                    },
                )
            _active_requests.pop(session_id, None)
            yield result, "", meta, session_id
            return
        yield partial, "", meta, session_id


def do_cancel(session_id):
    if session_id in _active_requests:
        _active_requests[session_id]["cancelled"] = True
        return "キャンセル要求を送信しました"
    return "実行中のリクエストはありません"


def do_clear():
    return "", "", "", make_session_id()


def do_download(text):
    if not text:
        return None
    b = text.encode("utf-8")
    return ("output.txt", b)


def refresh_history(user_id):
    items = get_history(user_id)
    if not items:
        return "履歴はありません"
    lines = []
    for it in items:
        lines.append(
            f"### {it['model']}\n**Prompt:**\n```\n{it['prompt']}\n```\n**Output (先頭):**\n```\n{it['output'][:500]}\n```\n"
        )
    return "\n\n".join(lines)


# ---- Gradio UI ----
with gr.Blocks(title="Ollama Model Runner") as demo:
    gr.Markdown("## Ollama Model Runner (Local)")

    with gr.Row():
        with gr.Column(scale=2):
            model_type = gr.Radio(
                ["Ollama", "Sakana AI"],
                label="モデルタイプ",
                value="Ollama",
            )
            with gr.Row():
                model_dropdown = gr.Dropdown(
                    label="Model",
                    choices=_ollama_models,
                    value=_ollama_models[0] if _ollama_models else DEFAULT_MODEL,
                )
                refresh_btn = gr.Button("🔄", size="sm")
            sample_dropdown = gr.Dropdown(
                [s["title"] for s in SAMPLES],
                label="サンプル",
                value=SAMPLES[0]["title"],
            )
            prompt_box = gr.Textbox(label="Prompt", lines=8, value=SAMPLES[0]["prompt"])
            with gr.Row():
                temp_slider = gr.Slider(
                    minimum=0.0, maximum=2.0, value=0.7, label="temperature"
                )
                top_p_slider = gr.Slider(
                    minimum=0.0, maximum=1.0, value=0.9, label="top_p"
                )
            max_tokens = gr.Number(label="max_new_tokens", value=128, precision=0)
            with gr.Row():
                clear_btn = gr.Button("クリア")
                cancel_btn = gr.Button("キャンセル", variant="stop")
                run_btn = gr.Button("実行")
                sakana_btn = gr.Button("Sakana AIに送信", visible=False)
            save_switch = gr.Checkbox(label="履歴に保存", value=True)
            gr.Markdown("### サンプル一覧")
            gr.Markdown(
                "\n".join([f"- **{s['title']}**: {s['prompt']}" for s in SAMPLES])
            )

        with gr.Column(scale=3):
            with gr.Tab("Ollama"):
                stream_output = gr.Textbox(label="出力（ストリーミング表示）", lines=16)
                output_area = gr.HTML(label="完全出力")
                meta_info = gr.Textbox(label="メタ情報", lines=3)
                with gr.Row():
                    download_btn = gr.Button("ダウンロード")
                    history_btn = gr.Button("履歴を更新")
            with gr.Tab("Sakana Chat"):
                gr.Markdown(
                    "### [Sakana Chat](https://chat.sakana.ai) - 新しいAIチャットサービス"
                )
                gr.HTML(
                    '<iframe src="https://chat.sakana.ai" width="100%" height="600px" style="border:2px solid #e0e0e0; border-radius:8px;" allow="clipboard-write"></iframe>'
                )
                gr.Markdown("*注意: 日本国内からのみアクセス可能*")

    # hidden state
    session_id_state = gr.Textbox(value=make_session_id(), visible=False)
    user_id_state = gr.Textbox(value="default_user", visible=False)
    history_box = gr.Markdown()

    # events
    model_type.change(
        fn=on_model_type_change,
        inputs=model_type,
        outputs=[model_dropdown, refresh_btn, temp_slider],
    )
    model_type.change(
        fn=lambda x: (
            gr.update(visible=False) if x == "Sakana AI" else gr.update(visible=True)
        ),
        inputs=model_type,
        outputs=run_btn,
    )
    model_type.change(
        fn=lambda x: (
            gr.update(visible=True) if x == "Sakana AI" else gr.update(visible=False)
        ),
        inputs=model_type,
        outputs=sakana_btn,
    )
    sample_dropdown.change(
        fn=on_sample_change, inputs=sample_dropdown, outputs=prompt_box
    )

    run_btn.click(
        fn=lambda model_id, prompt, temperature, top_p, max_new_tokens, save_history, user_id: (
            start_generation(
                model_id,
                prompt,
                temperature,
                top_p,
                max_new_tokens,
                save_history,
                user_id,
            )
        ),
        inputs=[
            model_dropdown,
            prompt_box,
            temp_slider,
            top_p_slider,
            max_tokens,
            save_switch,
            user_id_state,
        ],
        outputs=[stream_output, output_area, meta_info, session_id_state],
    )

    def send_to_sakana(prompt):
        if not prompt:
            return "", "プロンプトを入力してください", "{}", make_session_id()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                page.goto("https://chat.sakana.ai", timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)

                page.wait_for_timeout(3000)
                textarea = page.query_selector("textarea")
                if textarea:
                    textarea.fill(prompt)
                else:
                    editable = page.query_selector('[contenteditable="true"]')
                    if editable:
                        editable.fill(prompt)

                page.wait_for_timeout(5000)

                add_history(
                    "default_user",
                    {
                        "model": "Sakana AI",
                        "prompt": prompt,
                        "output": "(ブラウザで開きました)",
                        "meta": "{}",
                        "time": time.time(),
                    },
                )

                html = f"""
                <div style="padding:15px;background:#d4edda;border-radius:8px;">
                    <p style="color:#155724;"><strong>✓ Sakana Chatを開きました！</strong></p>
                    <p style="font-size:14px;">プロンプト: {prompt[:100]}...</p>
                </div>
                """
                return prompt, html, "{}", make_session_id()

        except Exception as e:
            import traceback

            html = f"""
            <div style="padding:15px;background:#f8d7da;border-radius:8px;">
                <p style="color:#721c24;"><strong>エラー:</strong> {str(e)}</p>
                <pre style="background:#fff;padding:10px;white-space:pre-wrap;">{traceback.format_exc()}</pre>
            </div>
            """
            return prompt, html, "{}", make_session_id()

    sakana_btn.click(
        fn=send_to_sakana,
        inputs=[prompt_box],
        outputs=[stream_output, output_area, meta_info, session_id_state],
    )

    refresh_btn.click(fn=refresh_models, outputs=[model_dropdown])
    cancel_btn.click(fn=do_cancel, inputs=[session_id_state], outputs=[meta_info])
    clear_btn.click(
        fn=do_clear, outputs=[prompt_box, stream_output, output_area, session_id_state]
    )
    download_btn.click(
        fn=do_download, inputs=[output_area], outputs=[gr.File(label="ダウンロード")]
    )
    history_btn.click(fn=refresh_history, inputs=[user_id_state], outputs=[history_box])

    model_type.change(
        fn=lambda x: (
            gr.update(visible=False) if x == "Sakana AI" else gr.update(visible=True)
        ),
        inputs=model_type,
        outputs=save_switch,
    )
    model_type.change(
        fn=lambda x: (
            gr.update(visible=False) if x == "Sakana AI" else gr.update(visible=True)
        ),
        inputs=model_type,
        outputs=max_tokens,
    )
    model_type.change(
        fn=lambda x: (
            gr.update(visible=False) if x == "Sakana AI" else gr.update(visible=True)
        ),
        inputs=model_type,
        outputs=top_p_slider,
    )

demo.launch()
