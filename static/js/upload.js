document.addEventListener("DOMContentLoaded", () => {
    const addBtn = document.getElementById("add-btn");
    const fileInput = document.getElementById("file-input");
    const tableBody = document.querySelector(".table tbody");

    if (!addBtn || !fileInput || !tableBody) return;

    // 1) 버튼 누르면 파일 선택창 열기
    addBtn.addEventListener("click", () => {
        fileInput.click();
    });

    // 2) 파일 선택되면 바로 업로드
    fileInput.addEventListener("change", async () => {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        addBtn.disabled = true;
        addBtn.textContent = "업로드 중...";

        try {
            const res = await fetch("/api/rag/upload", {
                method: "POST",
                body: formData,
            });
            const data = await res.json();

            if (res.ok && data.ok) {
                alert(`업로드 완료: ${data.filename}`);
                // 지금은 심플하게 새로고침으로 마무리
                location.reload();
            } else {
                alert(data.detail || data.error || "업로드 실패");
            }
        } catch (e) {
            console.error(e);
            alert("업로드 중 오류가 발생했습니다.");
        } finally {
            addBtn.disabled = false;
            addBtn.textContent = "＋";
            fileInput.value = "";
        }
    });

    tableBody.addEventListener("click", async (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;

        const action = btn.dataset.action;
        const filename = btn.dataset.filename;
        if (!filename) return;

        if (action === "delete") {
            const ok = confirm(`정말 삭제하시겠습니까?\n${filename}`);
            if (!ok) return;

            try {
                const res = await fetch(
                    `/api/rag/file/${encodeURIComponent(filename)}`,
                    { method: "DELETE" }
                );
                const data = await res.json();

                if (res.ok && data.ok) {
                    alert("삭제되었습니다.");
                    location.reload();
                } else {
                    alert(data.detail || data.error || "삭제 실패");
                }
            } catch (err) {
                console.error(err);
                alert("삭제 중 오류가 발생했습니다.");
            }
        }

        if (action === "embed") {
            try {
                btn.disabled = true;
                btn.textContent = "임베딩 중...";

                const res = await fetch(
                    `/api/rag/embed/${encodeURIComponent(filename)}`,
                    { method: "POST" }
                );
                const data = await res.json();

                if (res.ok && data.ok) {
                    alert("임베딩 완료.");
                    // 나중에 상태만 바꾸는 것도 가능하지만 지금은 새로고침으로 단순 처리
                    location.reload();
                } else {
                    alert(data.detail || data.error || "임베딩 실패");
                }
            } catch (err) {
                console.error(err);
                alert("임베딩 중 오류가 발생했습니다.");
            } finally {
                btn.disabled = false;
                btn.textContent = "임베딩";
            }
        }
    });
});