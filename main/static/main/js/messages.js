document.addEventListener("DOMContentLoaded", function () {
    const messageBox = document.getElementById('messageBox');

    if (messageBox) {
        // Show the message box
        messageBox.classList.add('show');

        // After 3 seconds, hide the message
        setTimeout(function() {
            messageBox.classList.remove('show');
        }, 6000); // 3000ms = 3 seconds
    }
});