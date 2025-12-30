import gradio as gr
import requests
import json
from datetime import datetime

# ==================== CONFIG ====================
LOGIC_API_URL = "http://localhost:9000/ask"
VISION_API_URL = "http://localhost:9001/analyze"

USER_AVATAR = "https://www.svgrepo.com/show/401101/angry-face.svg"
BOT_AVATAR = "https://www.svgrepo.com/show/401095/alien-monster.svg"


# ==================== LOGGING ====================
def log(title, data=None):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{ts}] ===== {title} =====")
    if data is not None:
        if isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(data)
    print("=" * 40)


# ==================== CORE LOGIC ====================
def chat_stream(message, history, image_input):
    # ===== EMPTY INPUT =====
    if not message.strip() and image_input is None:
        return (
            history,
            '<div class="vision-box">🧪 Kết quả Vision sẽ hiển thị ở đây</div>',
            gr.update(value="", interactive=True),
            gr.update(interactive=True)
        )

    if history is None:
        history = []

    # ===== USER MESSAGE =====
    user_content = []

    if image_input:
        user_content.append({"type": "image", "path": image_input})

    if message.strip():
        user_content.append({"type": "text", "text": message})

    history.append({"role": "user", "content": user_content})

    log("USER INPUT", {
        "text": message,
        "image": bool(image_input)
    })

    # ===== FIRST YIELD (VISION THINKING) =====
    yield (
        history,
        '<div class="vision-box">🤔 Đang phân tích ảnh...</div>',
        gr.update(value="", interactive=False),
        gr.update(interactive=False),
    )

    try:
        vision_html = ""
        symptoms = ""

        # ===== VISION =====
        if image_input:
            log("CALL VISION API", VISION_API_URL)

            with open(image_input, "rb") as f:
                v_res = requests.post(
                    VISION_API_URL,
                    files={"file": f},
                    timeout=60
                )

            log("VISION STATUS", v_res.status_code)

            if v_res.status_code == 200:
                v_json = v_res.json()
                symptoms = v_json.get("symptoms", "")
                log("VISION OUTPUT", symptoms)

                vision_html = f"""
                <div class="vision-box scrollable">
                    <h3>🧪 Kết quả từ Vision Model</h3>
                    {symptoms}
                </div>
                """
            else:
                vision_html = '<div class="vision-box">⚠️ Không phân tích được ảnh.</div>'
                log("VISION ERROR", v_res.text)

        # ===== ADD THINKING BUBBLE =====
        history.append({
            "role": "assistant",
            "content": "🧠 Đang suy luận chẩn đoán..."
        })

        yield (
            history,
            vision_html or '<div class="vision-box"></div>',
            gr.update(interactive=False),
            gr.update(interactive=False),
        )

        # ===== LOGIC =====
        final_question = (
            f"{symptoms}\n\nCâu hỏi: {message}"
            if symptoms else message
        )

        log("CALL LOGIC API", final_question)

        resp = requests.post(
            LOGIC_API_URL,
            json={"question": final_question},
            timeout=120
        )

        log("LOGIC STATUS", resp.status_code)

        if resp.status_code == 200:
            data = resp.json()
            log("LOGIC OUTPUT", data)

            answer = data.get("answer", "")
            sources = data.get("sources", [])
            if sources:
                answer += "\n\n📚 **Nguồn:**\n" + "\n".join(f"- {s}" for s in sources)
        else:
            answer = f"❌ Logic API lỗi {resp.status_code}"
            log("LOGIC ERROR", resp.text)

    except Exception as e:
        answer = f"❌ Lỗi hệ thống: {e}"
        log("EXCEPTION", str(e))

    # ===== REPLACE THINKING =====
    history[-1]["content"] = answer

    # ===== FINAL YIELD =====
    yield (
        history,
        vision_html or '<div class="vision-box"></div>',
        gr.update(value="", interactive=True),
        gr.update(interactive=True),
    )


# ==================== UI ====================
with gr.Blocks(
    theme=gr.themes.Origin(),
    css="""
    /* ================= IMAGE ================= */
    .vision-img img {
        max-height: 260px !important;
        width: 100%;
        object-fit: contain;
        border-radius: 8px;
        display: block;
    }

    /* ================= FIX SCROLLBAR MA ================= */
    .gr-markdown,
    .gr-markdown > div {
        overflow: hidden !important;
    }

    .vision-box {
        min-height: 260px;
        max-height: 260px;
        overflow: hidden;
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 8px;
        background: #fafafa;
        font-size: 14px;
        box-sizing: border-box;
    }

    .vision-box.scrollable {
        overflow-y: auto;
    }

    /* ================= DISABLE FOCUS BLINK ================= */
    textarea:focus,
    input:focus,
    button:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    """
) as demo:

    gr.Markdown("## 🌾 Trợ lý AI nông nghiệp cho nông dân Việt")

    with gr.Row():
        # ===== CHAT =====
        with gr.Column(scale=5):
            chatbot = gr.Chatbot(
                height=620,
                avatar_images=(USER_AVATAR, BOT_AVATAR)
            )
            textbox = gr.Textbox(
                placeholder="Nhập câu hỏi (có thể chỉ gửi ảnh)...",
                show_label=False
            )

        # ===== VISION PANEL =====
        with gr.Column(scale=2):
            image_input = gr.Image(
                type="filepath",
                label="📷 Ảnh cây trồng",
                elem_classes="vision-img"
            )

            vision_output = gr.Markdown(
                '<div class="vision-box">🧪 Kết quả Vision sẽ hiển thị ở đây</div>'
            )

    textbox.submit(
        chat_stream,
        inputs=[textbox, chatbot, image_input],
        outputs=[chatbot, vision_output, textbox, image_input]
    )


# ==================== LAUNCH ====================
if __name__ == "__main__":
    demo.queue(
        max_size=32,
        default_concurrency_limit=4
    ).launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True
    )
