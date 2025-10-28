// Lazar Stanivukovic 0590/2022
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('rezervacijaForm');
    const input = document.getElementById('datum_vreme');
    const errorMsg = document.getElementById('error_message');

    form.addEventListener('submit', function (event) {
        errorMsg.style.display = 'none';
        errorMsg.textContent = '';

        const now = new Date();
        const selected = new Date(input.value);

        if (selected < now) {
            errorMsg.textContent = "Ne možete napraviti rezervaciju za prošli datum.";
            errorMsg.style.display = 'block';
            event.preventDefault();
            return;
        }

        const hours = selected.getHours();
        const minutes = selected.getMinutes();
        if (hours < 8 || (hours === 23 && minutes > 0) || hours > 23) {
            errorMsg.textContent = "Rezervacije se mogu praviti samo između 08:00 i 23:00.";
            errorMsg.style.display = 'block';
            event.preventDefault();
        }
    });
});