document.addEventListener("DOMContentLoaded", () => {
    const addBtn = document.getElementById("add-btn");
    const embedAllBtn = document.getElementById("embed-all-btn");
    const fileInput = document.getElementById("file-input");
    const tableBody = document.querySelector(".table tbody");
    const overlay = document.getElementById("loading-overlay");

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

    // 전체 임베딩 버튼
    if (embedAllBtn) {
        embedAllBtn.addEventListener("click", async () => {
            const ok = confirm("업로드된 모든 파일을 임베딩하시겠습니까?");
            if (!ok) return;

            overlay.style.display = "flex";
            embedAllBtn.disabled = true;

            try {
                const res = await fetch("/api/rag/embed-all", {
                    method: "POST",
                });
                const data = await res.json();

                if (res.ok && data.ok) {
                    alert("임베딩이 완료되었습니다.");
                    location.reload();
                } else {
                    alert(data.detail || data.error || "임베딩 실패");
                }
            } catch (err) {
                console.error(err);
                alert("임베딩 중 오류가 발생했습니다.");
            } finally {
                overlay.style.display = "none";
                embedAllBtn.disabled = false;
                embedAllBtn.textContent = "임베딩";
            }
        });
    }

    // 삭제 버튼
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
    });
});
