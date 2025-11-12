// static/app.js
document.addEventListener("DOMContentLoaded", function () {
    const sendBtn = document.getElementById("send");
    const messageInput = document.getElementById("message");
    const chatContainer = document.getElementById("chatContainer");
    const emptyState = document.getElementById("emptyState");

    // 채팅 히스토리 저장
    let chatHistory = [];

    // 빈 상태 숨기기
    function hideEmptyState() {
        if (emptyState) {
            emptyState.style.display = "none";
        }
    }

    // 빈 상태 보이기
    function showEmptyState() {
        if (emptyState && chatHistory.length === 0) {
            emptyState.style.display = "flex";
        }
    }

    // 메시지 추가 (사용자)
    function addUserMessage(message) {
        hideEmptyState();
        const messageId = Date.now();
        chatHistory.push({ id: messageId, role: "user", content: message });

        const messageGroup = document.createElement("div");
        messageGroup.className = "message-group message-user";
        messageGroup.innerHTML = `
            <div class="message-header">
                <div class="message-avatar">U</div>
                <span class="message-name">사용자</span>
            </div>
            <div class="message-content">${escapeHtml(message)}</div>
        `;

        chatContainer.appendChild(messageGroup);
        scrollToBottom();
        // 메시지 추가 후 입력창이 보이도록 스크롤
        setTimeout(() => {
            scrollToInput();
        }, 150);
    }

    // 메시지 추가 (어시스턴트) - 타이핑 효과
    function addAssistantMessage(content, isStreaming = false) {
        hideEmptyState();
        const messageId = Date.now();
        
        const messageGroup = document.createElement("div");
        messageGroup.className = "message-group message-assistant";
        messageGroup.setAttribute("data-message-id", messageId);
        
        if (isStreaming) {
            messageGroup.innerHTML = `
                <div class="message-header">
                    <div class="message-avatar">AI</div>
                    <span class="message-name">AI Assistant</span>
                </div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
                <div class="message-actions">
                    <button class="copy-button" onclick="copyMessage(this)" title="복사">📋</button>
                </div>
            `;
        } else {
            messageGroup.innerHTML = `
                <div class="message-header">
                    <div class="message-avatar">AI</div>
                    <span class="message-name">AI Assistant</span>
                </div>
                <div class="message-content">${renderMarkdown(content)}</div>
                <div class="message-actions">
                    <button class="copy-button" onclick="copyMessage(this)" title="복사">📋</button>
                </div>
            `;
            // 코드 하이라이팅 적용
            setTimeout(() => {
                highlightCode(messageGroup);
            }, 0);
        }

        chatContainer.appendChild(messageGroup);
        
        if (!isStreaming) {
            chatHistory.push({ id: messageId, role: "assistant", content: content });
            scrollToBottom();
            // 응답 완료 후 입력창이 보이도록 스크롤
            setTimeout(() => {
                scrollToInput();
            }, 150);
        }

        return messageGroup;
    }

    // 스트리밍 효과로 텍스트 표시 (마크다운 렌더링 포함)
    function typeWriter(element, text, speed = 20) {
        return new Promise((resolve) => {
            element.innerHTML = "";
            let i = 0;
            let lastRenderTime = 0;
            const renderThrottle = 50; // 50ms마다 렌더링 (성능 최적화)
            
            const typingInterval = setInterval(() => {
                if (i < text.length) {
                    const now = Date.now();
                    const partialText = text.substring(0, i + 1);
                    
                    // 렌더링 쓰로틀링 (너무 자주 렌더링하지 않음)
                    if (now - lastRenderTime > renderThrottle || i === 0) {
                        try {
                            element.innerHTML = renderMarkdown(partialText);
                            highlightCode(element);
                            lastRenderTime = now;
                        } catch (error) {
                            // 렌더링 에러 시 텍스트로 대체
                            element.textContent = partialText;
                        }
                    }
                    i++;
                    scrollToBottom();
                    // 타이핑 중에도 입력창이 보이도록 스크롤
                    if (i % 10 === 0) {
                        scrollToInput();
                    }
                } else {
                    clearInterval(typingInterval);
                    // 최종 렌더링 (항상 마크다운 적용)
                    try {
                        element.innerHTML = renderMarkdown(text);
                        highlightCode(element);
                    } catch (error) {
                        element.textContent = text;
                    }
                    scrollToBottom();
                    scrollToInput();
                    resolve();
                }
            }, speed);
        });
    }

    // 메시지 업데이트
    function updateAssistantMessage(messageGroup, content, isTruncated = false) {
        const contentElement = messageGroup.querySelector(".message-content");
        const typingIndicator = messageGroup.querySelector(".typing-indicator");
        
        if (typingIndicator) {
            typingIndicator.remove();
        }

        // 잘린 응답인 경우 경고 배지 추가
        if (isTruncated && !messageGroup.querySelector(".truncated-warning")) {
            const warningBadge = document.createElement("div");
            warningBadge.className = "truncated-warning";
            warningBadge.innerHTML = "⚠️ 응답이 토큰 제한으로 잘렸습니다";
            messageGroup.appendChild(warningBadge);
        }

        // 스트리밍 효과 적용
        typeWriter(contentElement, content).then(() => {
            const messageId = parseInt(messageGroup.getAttribute("data-message-id"));
            const existingMessage = chatHistory.find(m => m.id === messageId);
            if (!existingMessage) {
                chatHistory.push({ id: messageId, role: "assistant", content: content, truncated: isTruncated });
            } else {
                existingMessage.content = content;
                existingMessage.truncated = isTruncated;
            }
            // 응답 완료 후 입력창이 보이도록 스크롤
            scrollToInput();
        });
    }

    // HTML 이스케이프 (사용자 메시지용)
    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // 마크다운 렌더링 (AI 응답용)
    function renderMarkdown(text) {
        if (typeof marked === 'undefined') {
            // marked 라이브러리가 없으면 텍스트 그대로 반환
            return escapeHtml(text);
        }
        
        // marked 옵션 설정
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: false,
            mangle: false
        });
        
        try {
            return marked.parse(text);
        } catch (error) {
            console.error('Markdown parsing error:', error);
            return escapeHtml(text);
        }
    }

    // 코드 하이라이팅 적용
    function highlightCode(element) {
        if (typeof Prism !== 'undefined') {
            const codeBlocks = element.querySelectorAll('pre code');
            codeBlocks.forEach(block => {
                // 이미 하이라이팅된 경우 스킵
                if (block.parentElement.classList.contains('language-')) {
                    return;
                }
                try {
                    Prism.highlightElement(block);
                } catch (error) {
                    // 하이라이팅 실패 시 무시
                    console.warn('Code highlighting failed:', error);
                }
            });
        }
    }

    // 스크롤 하단으로 (더 부드럽게)
    function scrollToBottom(smooth = false) {
        if (smooth) {
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        } else {
            // 즉시 스크롤
            requestAnimationFrame(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });
        }
    }
    
    // 입력창이 보이도록 하단으로 스크롤
    function scrollToInput() {
        requestAnimationFrame(() => {
            const inputArea = document.querySelector('.input-area');
            if (inputArea) {
                inputArea.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
        });
    }

    // 텍스트 영역 자동 높이 조절
    function autoResizeTextarea() {
        messageInput.style.height = "auto";
        messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + "px";
    }

    // 전송 함수
    async function send() {
        const message = messageInput.value.trim();
        if (!message) {
            return;
        }

        // 사용자 메시지 추가
        addUserMessage(message);
        
        // 입력 초기화
        messageInput.value = "";
        autoResizeTextarea();

        // 전송 중 UI 잠금
        sendBtn.disabled = true;
        messageInput.disabled = true;
        sendBtn.classList.add("loading");

        // 로딩 메시지 표시
        const loadingMessage = addAssistantMessage("", true);

        try {
            const response = await fetch("/api/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            });
            
            const data = await response.json();

            if (data.ok) {
                // 스트리밍 효과로 응답 표시 (잘림 여부 포함)
                const isTruncated = data.truncated || false;
                updateAssistantMessage(loadingMessage, data.answer, isTruncated);
            } else {
                updateAssistantMessage(loadingMessage, "에러: " + (data.error || "Unknown"));
            }
        } catch (error) {
            updateAssistantMessage(loadingMessage, "요청 실패: " + error.message);
        } finally {
            // 잠금 해제
            messageInput.disabled = false;
            sendBtn.disabled = false;
            sendBtn.classList.remove("loading");
            // 입력창 포커스 및 스크롤
            scrollToInput();
            setTimeout(() => {
                messageInput.focus();
            }, 100);
        }
    }

    // 전역 복사 함수 (마크다운 제거하고 순수 텍스트만)
    window.copyMessage = function(button) {
        const messageGroup = button.closest(".message-group");
        const contentElement = messageGroup.querySelector(".message-content");
        // HTML에서 순수 텍스트 추출
        const text = contentElement.textContent || contentElement.innerText;

        navigator.clipboard.writeText(text).then(() => {
            const originalText = button.textContent;
            button.textContent = "✓";
            button.style.color = "var(--accent-color)";
            setTimeout(() => {
                button.textContent = originalText;
                button.style.color = "";
            }, 2000);
        }).catch(() => {
            alert("복사에 실패했습니다.");
        });
    };

    // 이벤트 리스너
    sendBtn.addEventListener("click", send);

    // Enter 전송 (Shift+Enter는 줄바꿈)
    messageInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send();
        }
    });

    // 텍스트 영역 자동 높이 조절
    messageInput.addEventListener("input", autoResizeTextarea);

    // 초기 포커스
    messageInput.focus();
});
