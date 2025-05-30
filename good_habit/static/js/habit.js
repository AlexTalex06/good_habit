
document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.btn-complete');
    buttons.forEach(button => {
        button.addEventListener('click', function (e) {
            confetti();
        });
    });
});

function confetti() {
    alert("🎉 ¡Hábito completado! 🎉");
}
