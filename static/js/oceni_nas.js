// Aleksa Sekulic 0021/2022


document.addEventListener('DOMContentLoaded', () => {
    const stars = document.querySelectorAll('.star');
    const ocenaInput = document.getElementById('ocena');
    const confirmBtn = document.querySelector('.confirm-btn');

    stars.forEach(star => {
        star.addEventListener('click', function() {
            const val = parseInt(this.getAttribute('data-value'));
            ocenaInput.value = val;
            confirmBtn.disabled = false;

            stars.forEach((s, i) => {
                s.innerHTML = i < val ? '★' : '☆';
                s.style.color = i < val ? '#B8860B' : '#000';
            });
        });
    });
});