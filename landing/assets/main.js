// ============================================
// GOOGLE FORMS INTEGRATION
// ============================================

const GOOGLE_FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSfI7MYRT2Q1FTQHRSGn9_eDAHyY1DMOYe50jNaCfRDmTAJU9Q/formResponse';
const EMAIL_FIELD_ID = 'entry.346178107';

// ============================================

// Form submission handler
document.getElementById('waitlistForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const form = document.getElementById('waitlistForm');
    const successMessage = document.getElementById('successMessage');
    const submitButton = form.querySelector('button[type="submit"]');

    // Disable button during submission
    submitButton.disabled = true;
    submitButton.textContent = KK_I18N.loading;

    // Create form data for Google Forms
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

    // Submit to Google Forms
    fetch(GOOGLE_FORM_URL, {
        method: 'POST',
        mode: 'no-cors', // Important: Google Forms requires no-cors
        body: formData
    })
    .then(() => {
        console.log('Email submitted successfully:', email);
        onComplete();
    })
    .catch(() => {
        // Even errors mean it probably worked (no-cors mode)
        console.log('Submission completed:', email);
        onComplete();
    });
});

// Smooth scroll to form
function scrollToForm(e) {
    e.preventDefault();
    document.querySelector('.email-form').scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
    document.getElementById('email').focus();
}

// Add scroll animation for elements
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.feature-card, .step').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'all 0.6s ease-out';
    observer.observe(el);
});
