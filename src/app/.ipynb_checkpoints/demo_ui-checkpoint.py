import gradio as gr
import requests

# ==================== CONFIG ====================
API_URL = "http://0.0.0.0:9000/ask"

USER_AVATAR = "https://www.svgrepo.com/show/401101/angry-face.svg"
BOT_AVATAR = "https://www.svgrepo.com/show/401095/alien-monster.svg"


# ==================== CORE CHAT LOGIC ====================
def chat_stream(message, history):
    if not message.strip():
        return history, gr.update(value="", interactive=True)

    if history is None:
        history = []

    # 1️⃣ USER MESSAGE – HIỂN THỊ NGAY
    history.append({
        "role": "user",
        "content": message
    })

    # disable input khi đang chờ
    yield history, gr.update(value="", interactive=False)

    try:
        resp = requests.post(
            API_URL,
            json={"question": message},
            timeout=300
        )

        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])

            if sources:
                answer += "\n\n📚 **Nguồn tham khảo:**\n"
                answer += "\n".join([f"- {s}" for s in sources])

        else:
            answer = f"❌ Lỗi server ({resp.status_code})"

    except Exception as e:
        answer = f"❌ Lỗi kết nối: {e}"

    # 2️⃣ BOT MESSAGE
    history.append({
        "role": "assistant",
        "content": answer
    })

    # enable lại input
    yield history, gr.update(value="", interactive=True)


# ==================== UI ====================
with gr.Blocks(theme=gr.themes.Origin()) as demo:

    gr.Markdown(
        """
        # 🌾 Chuyên gia nông nghiệp cho nông dân Việt  
        **RAG + AI chẩn đoán bệnh cây trồng**
        """
    )

    chatbot = gr.Chatbot(
        height=480,
        avatar_images=(USER_AVATAR, BOT_AVATAR)
    )

    textbox = gr.Textbox(
        placeholder="Nhập câu hỏi về cây trồng...",
        show_label=False,
        autofocus=True
    )

    # ===== Suggested questions (NGAY DƯỚI INPUT) =====
    with gr.Row():
        q1 = gr.Button("🌱 Lá sầu riêng bị cháy là bệnh gì?", size="sm")
        q2 = gr.Button("🌾 Cách phòng bệnh đạo ôn trên lúa", size="sm")
        q3 = gr.Button("☕ Cà phê bị vàng lá xử lý thế nào?", size="sm")

    # ==================== EVENTS ====================

    # Enter để gửi
    textbox.submit(
        fn=chat_stream,
        inputs=[textbox, chatbot],
        outputs=[chatbot, textbox],
        queue=True
    )

    # Gợi ý → gửi THẲNG (KHÔNG update textbox trước)
    q1.click(
        fn=chat_stream,
        inputs=[gr.State("Lá sầu riêng bị cháy là bệnh gì?"), chatbot],
        outputs=[chatbot, textbox],
        queue=True
    )

    q2.click(
        fn=chat_stream,
        inputs=[gr.State("Cách phòng bệnh đạo ôn trên lúa"), chatbot],
        outputs=[chatbot, textbox],
        queue=True
    )

    q3.click(
        fn=chat_stream,
        inputs=[gr.State("Cà phê bị vàng lá xử lý thế nào?"), chatbot],
        outputs=[chatbot, textbox],
        queue=True
    )


# ==================== RUN ====================
if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True
    )
