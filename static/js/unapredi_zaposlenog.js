// Sofija Pavlovic 0340/2022
document.addEventListener("DOMContentLoaded", () => {
    const selects = document.querySelectorAll("table select");

    selects.forEach(select => {
        select.addEventListener("change", (e) => {
            const row = e.target.closest("tr");
            const idInput = row.querySelector('input[name="id"]');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const noviTip = e.target.value;

            const data = new FormData();
            data.append("id", idInput.value);
            data.append("akcija", "sacuvaj");
            data.append("tip", noviTip);

            fetch("", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: data
            })
            .then(response => {
                if (!response.ok) throw new Error("Greška prilikom slanja podataka.");
                return response.text();
            })
            .then(() => {
                console.log("Tip zaposlenog uspešno promenjen.");
            })
            .catch(error => {
                console.error(error);
                alert("Došlo je do greške prilikom ažuriranja tipa zaposlenog.");
            });
        });
    });
});
