(function() {
    var STORAGE_KEY = 'kk_consent';

    function activateAnalytics() {
        if (typeof gtag === 'function') {
            gtag('config', 'G-1LYJD5CSZ2');
        }
        if (typeof window._activateFirebaseAnalytics === 'function') {
            window._activateFirebaseAnalytics();
        } else {
            window._kkAnalyticsConsented = true;
        }
    }

    function dismiss(value) {
        localStorage.setItem(STORAGE_KEY, value);
        var banner = document.getElementById('consentBanner');
        if (banner) banner.remove();
    }

    // Already decided — act immediately, no banner needed
    var existing = localStorage.getItem(STORAGE_KEY);
    if (existing === 'accepted') {
        activateAnalytics();
        return;
    }
    if (existing === 'rejected') {
        return;
    }

    // No decision yet — render the banner
    var banner = document.createElement('div');
    banner.id = 'consentBanner';
    banner.className = 'consent-banner';
    banner.innerHTML =
        '<div class="consent-banner__content"><p>' + KK_I18N.consentText + '</p></div>' +
        '<div class="consent-banner__actions">' +
            '<button class="consent-banner__btn consent-banner__btn--reject">' + KK_I18N.consentReject + '</button>' +
            '<button class="consent-banner__btn consent-banner__btn--accept">' + KK_I18N.consentAccept + '</button>' +
        '</div>';

    banner.querySelector('.consent-banner__btn--accept').addEventListener('click', function() {
        dismiss('accepted');
        activateAnalytics();
    });

    banner.querySelector('.consent-banner__btn--reject').addEventListener('click', function() {
        dismiss('rejected');
    });

    document.body.appendChild(banner);
})();
