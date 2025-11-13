// static/js/system_chart.js

async function fetchSystemInfo() {
    try {
        const res = await fetch("/api/system/info");
        if (!res.ok) {
            console.error("Failed to fetch system info:", res.status);
            return;
        }
        const data = await res.json();

        // ----- CPU -----
        const cpu = data.cpu_percent ?? 0;
        const cpuOverall = document.getElementById("cpu-overall");
        const cpuBar = document.getElementById("cpu-bar");

        if (cpuOverall && cpuBar) {
            cpuOverall.textContent = cpu.toFixed(1);
            cpuBar.style.width = Math.min(cpu, 100) + "%";
        }

        // ----- Memory -----
        const mem = data.memory || {};
        const memPercent = mem.percent ?? 0;
        const memPercentEl = document.getElementById("mem-percent");
        const memBar = document.getElementById("mem-bar");
        const memText = document.getElementById("mem-text");

        if (memPercentEl && memBar) {
            memPercentEl.textContent = memPercent.toFixed(1);
            memBar.style.width = Math.min(memPercent, 100) + "%";
        }

        if (memText && mem.total != null && mem.used != null) {
            const toGB = v => (v / (1024 ** 3)).toFixed(1) + " GB";
            memText.textContent = `사용 중: ${toGB(mem.used)} / 전체: ${toGB(mem.total)}`;
        }

        // ----- Disk -----
        const disk = data.disk || {};
        const diskPercentEl = document.getElementById("disk-percent");
        const diskBar = document.getElementById("disk-bar");
        const diskUsedEl = document.getElementById("disk-used");
        const diskTotalEl = document.getElementById("disk-total");

        if (diskPercentEl && diskBar && disk.percent != null) {
            diskPercentEl.textContent = disk.percent.toFixed(1) + "%";
            diskBar.style.width = Math.min(disk.percent, 100) + "%";
        }

        if (diskUsedEl && diskTotalEl && disk.used != null && disk.total != null) {
            const toGB = v => (v / (1024 ** 3)).toFixed(1) + " GB";
            diskUsedEl.textContent = toGB(disk.used);
            diskTotalEl.textContent = toGB(disk.total);
        }

        // ----- GPU -----
        const gpu = data.gpu || null;
        const gpuSummary = document.getElementById("gpu-summary");
        const gpuBar = document.getElementById("gpu-bar");
        const gpuMem = document.getElementById("gpu-mem");
        const gpuTemp = document.getElementById("gpu-temp");
        const gpuLoad = document.getElementById("gpu-load");
        const gpuValue = document.getElementById("gpu-value");

        if (!gpu) {
            if (gpuSummary) gpuSummary.textContent = "GPU 없음 또는 정보를 가져올 수 없습니다.";
            if (gpuBar) gpuBar.style.width = "0%";
            if (gpuLoad) gpuLoad.textContent = "-";
            if (gpuValue) gpuValue.style.display = "none";
        } else {
            if (gpuSummary) {
                gpuSummary.textContent = `${gpu.name}`;
            }
            if (gpuBar) gpuBar.style.width = Math.min(gpu.load_percent, 100) + "%";
            if (gpuLoad) gpuLoad.textContent = gpu.load_percent.toFixed(1);

            if (gpuMem && gpu.mem_used != null && gpu.mem_total != null) {
                gpuMem.textContent = `메모리: ${gpu.mem_used.toFixed(0)} MB / ${gpu.mem_total.toFixed(0)} MB (${gpu.mem_percent.toFixed(1)}%)`;
            }
            if (gpuTemp && gpu.temperature != null) {
                gpuTemp.textContent = `온도: ${gpu.temperature}℃`;
            }
        }

        // ----- Top Processes -----
        const procBody = document.getElementById("proc-body");
        if (procBody) {
            const procs = data.processes || [];
            if (!procs.length) {
                procBody.innerHTML = `
                    <tr><td colspan="4" class="table-empty">
                        프로세스 정보를 가져올 수 없습니다.
                    </td></tr>`;
            } else {
                procBody.innerHTML = procs.map(p => `
                    <tr>
                        <td>${p.pid || '-'}</td>
                        <td>${(p.name || 'N/A').substring(0, 30)}</td>
                        <td>${(p.cpu_percent || 0).toFixed(1)}%</td>
                        <td>${(p.memory_percent || 0).toFixed(1)}%</td>
                    </tr>
                `).join("");
            }
        }

    } catch (err) {
        console.error("system info error:", err);
    }
}

// 첫 로드 + 2초마다 갱신 (너무 자주 호출하면 서버 부하)
fetchSystemInfo();
setInterval(fetchSystemInfo, 2000);
