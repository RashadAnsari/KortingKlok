const GOOGLE_FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSfI7MYRT2Q1FTQHRSGn9_eDAHyY1DMOYe50jNaCfRDmTAJU9Q/formResponse';
const EMAIL_FIELD_ID = 'entry.346178107';

document.getElementById('waitlistForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const form = document.getElementById('waitlistForm');
    const successMessage = document.getElementById('successMessage');
    const submitButton = form.querySelector('button[type="submit"]');

    submitButton.disabled = true;
    submitButton.textContent = KK_I18N.loading;

    const formData = new FormData();
    formData.append(EMAIL_FIELD_ID, email);

    function onComplete() {
        form.style.display = 'none';
        successMessage.classList.add('show');

        setTimeout(() => {
            form.style.display = 'block';
            successMessage.classList.remove('show');
            form.reset();
            submitButton.disabled = false;
            submitButton.textContent = KK_I18N.submit;
        }, 5000);
    }

    fetch(GOOGLE_FORM_URL, {
        method: 'POST',
        mode: 'no-cors',
        body: formData
    })
    .then(() => {
        console.log('Email submitted successfully:', email);
        onComplete();
    })
    .catch(() => {
        console.log('Submission completed:', email);
        onComplete();
    });
});

function scrollToForm(e) {
    e.preventDefault();
    document.querySelector('.email-form').scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
    document.getElementById('email').focus();
}
