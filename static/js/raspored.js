// Sofija Pavlovic 0340/2022

document.addEventListener("DOMContentLoaded", () => {
    const floor = document.querySelector(".floor");
    const saveBtn = document.querySelector(".save-btn");
    const csrfToken = document.getElementById("csrf-token").value;

    let mode = null;
    let nextTableNumber = 1;

    document.querySelectorAll(".table").forEach(cell => {
        const num = parseInt(cell.textContent.trim());
        if (!isNaN(num) && num >= nextTableNumber) {
            nextTableNumber = num + 1;
        }
    });

    document.querySelectorAll('input[name="rezim"]').forEach(radio => {
        radio.addEventListener("change", e => {
            mode = e.target.value;
            document.querySelectorAll('input[name="rezim"]').forEach(r => {
                r.parentElement.classList.remove("active-mode");
            });
            e.target.parentElement.classList.add("active-mode");
        });
    });

    const state = {};
    document.querySelectorAll(".cell").forEach(cell => {
        const x = parseInt(cell.dataset.x);
        const y = parseInt(cell.dataset.y);
        state[`${x}_${y}`] = {
            x, y,
            sto: cell.classList.contains("table"),
            blocked: cell.classList.contains("blocked-cell"),
            broj_stola: cell.classList.contains("table") ? parseInt(cell.textContent.trim()) || null : null
        };
    });

    floor.addEventListener("click", e => {
        const cell = e.target.closest(".cell");
        if (!cell) return;

        const selectedRadio = document.querySelector('input[name="rezim"]:checked');
        if (!selectedRadio) return;

        mode = selectedRadio.value;

        const x = parseInt(cell.dataset.x);
        const y = parseInt(cell.dataset.y);
        const key = `${x}_${y}`;

        if (!state[key]) {
            state[key] = { x, y, sto: false, blocked: false, broj_stola: null };
        }

        if (mode === "prostor") {
            cell.classList.remove("table", "round");
            if (cell.classList.contains("blocked-cell")) {
                cell.classList.remove("blocked-cell");
                cell.classList.add("empty-cell");
                state[key].blocked = false;
            } else {
                cell.classList.remove("empty-cell");
                cell.classList.add("blocked-cell");
                state[key].blocked = true;
                state[key].sto = false;
                state[key].broj_stola = null;
                cell.textContent = "";
            }
            return;
        }

        if (mode === "stolovi") {
            if (cell.classList.contains("table")) {
                cell.classList.remove("table", "round");
                cell.classList.add("empty-cell");
                state[key].sto = false;
                state[key].broj_stola = null;
                cell.textContent = "";
            } else {
                cell.classList.remove("blocked-cell", "empty-cell");
                cell.classList.add("table", "round");
                state[key].sto = true;
                state[key].blocked = false;
                cell.textContent = nextTableNumber;
                state[key].broj_stola = nextTableNumber;
                nextTableNumber++;
            }
            return;
        }
    });

    saveBtn.addEventListener("click", async () => {
        try {
            const cells = Object.values(state);
            const response = await fetch(window.location.pathname, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ cells })
            });

            if (response.ok) {
                alert("Raspored uspešno sačuvan!");
            } else {
                alert("Greška pri čuvanju rasporeda.");
            }
        } catch (err) {
            console.error(err);
            alert("Greška pri komunikaciji sa serverom.");
        }
    });
});
