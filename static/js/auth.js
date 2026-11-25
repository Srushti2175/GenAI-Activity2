// Authentication page helpers for Krishi Sakhi

function togglePasswordVisibility(inputId, buttonEl) {
    const input = document.getElementById(inputId);
    const icon = buttonEl.querySelector('i');
    if (!input) return;

    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

function fillDemoCredentials() {
    const idField = document.getElementById('identifier');
    const pwField = document.getElementById('password');
    if (idField) idField.value = 'demo@krishisakhi.in';
    if (pwField) pwField.value = 'demo123';
}

function fillDemoSignup() {
    const nameField = document.getElementById('name');
    const phoneField = document.getElementById('phone');
    const idField = document.getElementById('identifier');
    const locField = document.getElementById('location');
    const cropsField = document.getElementById('crops');
    const pwField = document.getElementById('signupPassword');
    const langField = document.getElementById('language');

    if (nameField) nameField.value = 'तुकाराम जाधव (Tukaram Jadhav)';
    if (phoneField) phoneField.value = '9850123456';
    if (idField) idField.value = 'tukaram@krishisakhi.in';
    if (locField) locField.value = 'पुणे, महाराष्ट्र (Pune, Maharashtra)';
    if (cropsField) cropsField.value = 'ऊस व भाजीपाला (Sugarcane & Vegetables)';
    if (pwField) pwField.value = 'farmer@123';
    if (langField) langField.value = 'mr';
}
