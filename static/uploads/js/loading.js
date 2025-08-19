function statusClassFromText(text) {
  if (text === "ขาด") return "status-absent";
  if (text === "สาย")  return "status-late";
  return "status-present"; // ค่าเริ่มต้น: เช็กชื่อเรียบร้อย
}

function loadAttendance() {
  fetch("/attendance_api")
    .then((response) => response.json())
    .then((data) => {
      const table = document.getElementById("attendance-table");
      table.innerHTML = "";

      if (!Array.isArray(data) || data.length === 0) {
        table.innerHTML = `<tr><td colspan="6">ไม่มีข้อมูลการเช็คชื่อ</td></tr>`;
        return;
      }

      data.forEach((row) => {
        const tr = document.createElement("tr");
        const statusClass = statusClassFromText(row.status);

        tr.innerHTML = `
          <td>${row.id}</td>
          <td>${row.name}</td>
          <td>
            <img src="${row.image_url}"
                 width="60" height="60"
                 onerror="this.src='/static/uploads/default.png'">
          </td>
          <td>${row.date}</td>
          <td>${row.time}</td>
          <td class="${statusClass}">${row.status}</td>
        `;
        table.appendChild(tr);
      });
    })
    .catch((err) => {
      console.error("โหลดข้อมูลล้มเหลว:", err);
      const table = document.getElementById("attendance-table");
      table.innerHTML = `<tr><td colspan="6">โหลดข้อมูลล้มเหลว</td></tr>`;
    });
}

// โหลดครั้งแรก
loadAttendance();

// โหลดซ้ำทุก 5 วินาที (รีเฟรชแบบเรียลไทม์)
setInterval(loadAttendance, 5000);
