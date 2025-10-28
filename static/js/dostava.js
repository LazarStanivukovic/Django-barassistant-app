// Lazar Stanivukovic 0590/2022

function getCSRFToken() {
    const name = 'csrftoken=';
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name)) return c.substring(name.length);
    }
    return '';
}

function updateStatus(id, newStatus) {
    fetch("", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify({ id: id, status: newStatus })
    })
    .then(response => {
        if (!response.ok) {
            alert("Greška pri ažuriranju statusa.");
        } else {
            const row = document.getElementById("dostava-" + id);
            if (newStatus !== "U TOKU" && row) {
                row.remove();


                const tbody = document.querySelector("table tbody");
                if (tbody && tbody.children.length === 0) {
                    const emptyRow = document.createElement("tr");
                    emptyRow.innerHTML = `
                        <td colspan="4" style="text-align:center;">
                            Trenutno nema aktivnih dostava.
                        </td>`;
                    tbody.appendChild(emptyRow);
                }
            }
        }
    })
    .catch(err => alert("Greška u mreži: " + err));
}
