document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorMessage.textContent = '';

        const formData = new FormData(loginForm);
        const body = new URLSearchParams(formData);

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: body
            });

            if (response.ok) {
                const data = await response.json();
                sessionStorage.setItem('accessToken', data.access_token);
                window.location.href = '/dashboard';
            } else {
                const errorData = await response.json();
                errorMessage.textContent = errorData.detail || 'Nom d\'utilisateur ou mot de passe incorrect.';
            }
        } catch (error) {
            console.error('Erreur de connexion:', error);
            errorMessage.textContent = 'Une erreur est survenue. Veuillez réessayer.';
        }
    });
});