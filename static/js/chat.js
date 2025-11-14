// static/js/chat.js

document.addEventListener("DOMContentLoaded", () => {
    const sendBtn = document.getElementById("chatSendBtn");
    const messageInput = document.getElementById("chatInput");
    const chatContainer = document.getElementById("chatMessages");

    if (!sendBtn || !messageInput || !chatContainer) {
        console.error("chat elements not found");
        return;
    }

    let chatHistory = [];

    function getEmptyState() {
        return chatContainer.querySelector(".empty-state");
    }

    function hideEmptyState() {
        const empty = getEmptyState();
        if (empty) empty.remove();
    }

    // 공통 메시지 DOM 생성
    function createMessageElement(role, text) {
        const wrapper = document.createElement("div");
        wrapper.classList.add("chat-message", `chat-message-${role}`);

        const bubble = document.createElement("div");
        bubble.classList.add("chat-bubble");

        const header = document.createElement("div");
        header.classList.add("chat-message-header");
        header.textContent = role === "user" ? "나" : "AI";

        const body = document.createElement("div");
        body.classList.add("chat-message-body");
        body.textContent = text;

        bubble.appendChild(header);
        bubble.appendChild(body);
        wrapper.appendChild(bubble);
        return wrapper;
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
    }

    function addUserMessage(message) {
        hideEmptyState();
        const el = createMessageElement("user", message);
        chatContainer.appendChild(el);
        chatHistory.push({ role: "user", content: message });
        scrollToBottom();
    }

    function addAssistantMessage(text) {
        hideEmptyState();
        const el = createMessageElement("assistant", text);
        chatContainer.appendChild(el);
        chatHistory.push({ role: "assistant", content: text });
        scrollToBottom();
    }

    function addAssistantLoading() {
        hideEmptyState();
        const wrapper = document.createElement("div");
        wrapper.classList.add("chat-message", "chat-message-assistant");

        const bubble = document.createElement("div");
        bubble.classList.add("chat-bubble");

        const header = document.createElement("div");
        header.classList.add("chat-message-header");
        header.textContent = "AI";

        const body = document.createElement("div");
        body.classList.add("chat-message-body");

        body.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;

        bubble.appendChild(header);
        bubble.appendChild(body);
        wrapper.appendChild(bubble);
        chatContainer.appendChild(wrapper);
        scrollToBottom();
        return wrapper;
    }

    function updateAssistantLoading(element, text) {
        const body = element.querySelector(".chat-message-body");
        if (body) {
            body.textContent = text;
        }
    }

    async function send() {
        const message = messageInput.value.trim();
        if (!message) return;

        // UI 잠금
        sendBtn.disabled = true;
        messageInput.disabled = true;

        // 내 메시지 추가
        addUserMessage(message);
        messageInput.value = "";

        // 로딩 메시지
        const loadingEl = addAssistantLoading();

        try {
            const res = await fetch("/api/chat/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            });

            const data = await res.json();

            if (!res.ok || !data.ok) {
                const errorText = data.error || `요청 실패 (status ${res.status})`;
                updateAssistantLoading(loadingEl, errorText);
                return;
            }

            updateAssistantLoading(loadingEl, data.answer || "(응답이 없습니다.)");
        } catch (err) {
            console.error(err);
            updateAssistantLoading(loadingEl, "요청 중 오류가 발생했습니다.");
        } finally {
            sendBtn.disabled = false;
            messageInput.disabled = false;
            messageInput.focus();
        }
    }

    // 버튼 클릭
    sendBtn.addEventListener("click", send);

    // Enter 전송 (Shift+Enter는 줄바꿈)
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send();
        }
    });
});
