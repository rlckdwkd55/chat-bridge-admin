// static/js/chat.js

document.addEventListener("DOMContentLoaded", () => {
    const sendBtn = document.getElementById("chatSendBtn");
    const messageInput = document.getElementById("chatInput");
    const chatContainer = document.getElementById("chatMessages");

    if (!sendBtn || !messageInput || !chatContainer) {
        console.error("chat elements not found");
        return;
    }

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

    // 에러 등 즉시 텍스트 표시
    function setAssistantText(element, text) {
        const body = element.querySelector(".chat-message-body");
        if (!body) return;
        body.textContent = text;
        scrollToBottom();
    }

    // 스트리밍(타자 효과)처럼 보이게 출력
    function streamAssistantText(element, text, speed = 25) {
        const body = element.querySelector(".chat-message-body");
        if (!body) return;

        body.textContent = ""; // 로딩 점 제거
        let index = 0;

        const timer = setInterval(() => {
            body.textContent += text.charAt(index);
            index += 1;
            scrollToBottom();

            if (index >= text.length) {
                clearInterval(timer);
            }
        }, speed);
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
                setAssistantText(loadingEl, errorText);
                return;
            }

            const answer = data.answer || "(응답이 없습니다.)";
            // 여기서부터 스트리밍처럼 표시
            streamAssistantText(loadingEl, answer);
        } catch (err) {
            console.error(err);
            setAssistantText(loadingEl, "요청 중 오류가 발생했습니다.");
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
