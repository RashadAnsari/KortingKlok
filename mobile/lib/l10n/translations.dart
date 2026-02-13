const Map<String, Map<String, String>> translations = {
  'en': {
    // Welcome screen
    'welcome_title': 'KortingKlok',
    'welcome_tagline': 'On time for every discount',
    'welcome_feature1_title': 'Real-time notifications',
    'welcome_feature1_desc':
        'Get an instant push notification the moment your favourite product goes on sale. Never miss a deal.',
    'welcome_feature2_title': 'All supermarkets',
    'welcome_feature2_desc':
        'Track deals at Albert Heijn, Jumbo and Lidl in one clear app. No need for five separate apps.',
    'welcome_feature3_title': 'Smart savings',
    'welcome_feature3_desc':
        'Track your favourite products and buy them when they go on sale. Save on the things you are already buying.',
    'welcome_get_started': 'Get started',
    'welcome_have_account': 'Already have an account?',
    'welcome_log_in_link': 'Log in',

    // Forgot password screen
    'forgot_title': 'Forgot password?',
    'forgot_subtitle': 'Enter your email and we\'ll send you a reset link',
    'forgot_button': 'Send reset link',
    'forgot_back_login': 'Back to login',
    'forgot_success_title': 'Email sent!',
    'forgot_success_desc': 'We sent a password reset link to {email}',

    // Login screen
    'login_title': 'Welcome back',
    'login_subtitle': 'Log in to continue',
    'login_email_label': 'Email address',
    'login_email_hint': 'your@email.com',
    'login_password_label': 'Password',
    'login_password_hint': '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022',
    'login_forgot_password': 'Forgot password?',
    'login_button': 'Log in',
    'login_or_continue': 'Or continue with',
    'login_google': 'Continue with Google',
    'login_apple': 'Continue with Apple',
    'login_no_account': 'Don\'t have an account?',
    'login_sign_up_link': 'Sign up',

    // Register screen
    'register_title': 'Create account',
    'register_subtitle': 'Start saving today',
    'register_display_name': 'Display name',
    'register_display_name_hint': 'Jan de Vries',
    'register_email_label': 'Email address',
    'register_email_hint': 'john@email.com',
    'register_password_label': 'Password',
    'register_password_hint':
        '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022',
    'register_button': 'Sign up',
    'register_or_continue': 'Or sign up with',
    'register_google': 'Continue with Google',
    'register_apple': 'Continue with Apple',
    'register_have_account': 'Already have an account?',
    'register_log_in_link': 'Log in',

    // Home screen
    'home_title': 'Today\'s Discounts',
    'home_all_stores': 'All stores',
    'home_view_offer': 'View Offer',
    'home_empty_title': 'No deals yet',
    'home_empty_subtitle':
        'Track products in Search and we\'ll notify you when they go on sale',

    // Search screen
    'search_placeholder': 'Search products at {store}...',
    'search_categories_title': 'Categories at {store}',
    'search_cat_deals': 'This week\'s deals',
    'search_cat_fresh': 'Fresh products',
    'search_cat_dairy': 'Dairy & Eggs',
    'search_cat_meat': 'Meat & Fish',
    'search_cat_drinks': 'Beverages',
    'search_no_categories': 'No categories found',
    'search_no_results': 'No products found',
    'error_generic': 'Something went wrong',
    'retry_button': 'Try again',

    // Product detail
    'detail_back': 'Back',
    'detail_on_sale_at': 'On sale at:',
    'detail_view_at': 'View at {store}',

    // Profile screen
    'profile_account': 'ACCOUNT',
    'profile_change_name': 'Change display name',
    'profile_change_password': 'Change password',
    'profile_preferences': 'PREFERENCES',
    'profile_language': 'Language',
    'profile_theme': 'Theme',
    'profile_notifications_section': 'NOTIFICATIONS',
    'profile_push_notifications': 'Push notifications',
    'profile_other': 'OTHER',
    'profile_help': 'Help & FAQ',
    'profile_privacy': 'Privacy policy',
    'profile_about': 'About KortingKlok',
    'profile_logout': 'Log out',
    'profile_change_email': 'Change email address',
    'profile_new_email_label': 'New email address',
    'profile_new_email_hint': 'new@email.com',
    'profile_current_password_label': 'Current password',
    'profile_new_password_label': 'New password',
    'profile_save': 'Save',
    'profile_name_updated': 'Display name updated',
    'profile_password_updated': 'Password updated',
    'profile_email_verify_sent':
        'Verification link sent to your new email address',

    // Theme options
    'theme_light': 'Light',
    'theme_dark': 'Dark',
    'theme_system': 'System',

    // Language options
    'lang_english': 'English \ud83c\uddec\ud83c\udde7',
    'lang_dutch': 'Nederlands \ud83c\uddf3\ud83c\uddf1',

    // Nav
    'nav_home': 'Home',
    'nav_search': 'Search',
    'nav_profile': 'Profile',

    // Product badges
    'badge_buy1get1': 'BUY 1 GET 1',
    'badge_half_price': '2ND HALF PRICE',

    // Validation
    'validation_required': 'This field is required',
    'validation_email_invalid': 'Enter a valid email address',
    'validation_password_min': 'Password must be at least 6 characters',

    // Auth errors
    'auth_error_invalid_credential': 'Invalid email or password',
    'auth_error_user_not_found': 'No account found for this email',
    'auth_error_email_in_use': 'This email is already in use',
    'auth_error_weak_password': 'Password too weak (min. 6 characters)',
    'auth_error_network': 'No internet connection',
    'auth_error_cancelled': 'Sign-in was cancelled',
    'auth_error_unknown': 'Something went wrong, please try again',
    'auth_error_wrong_password': 'Incorrect password',
    'auth_error_requires_recent_login': 'Please sign in again and try again',
  },
  'nl': {
    // Welcome screen
    'welcome_title': 'KortingKlok',
    'welcome_tagline': 'Op tijd bij iedere korting',
    'welcome_feature1_title': 'Real-time meldingen',
    'welcome_feature1_desc':
        'Krijg direct een push notificatie zodra jouw favoriete product in de bonus is. Nooit meer een deal missen.',
    'welcome_feature2_title': 'Alle supermarkten',
    'welcome_feature2_desc':
        'Volg aanbiedingen bij Albert Heijn, Jumbo \u00e9n Lidl in \u00e9\u00e9n overzichtelijke app. Geen vijf apps meer nodig.',
    'welcome_feature3_title': 'Slimme besparingen',
    'welcome_feature3_desc':
        'Track je favoriete producten en koop ze wanneer ze in de bonus zijn. Bespaar op de producten die je toch al koopt.',
    'welcome_get_started': 'Aan de slag',
    'welcome_have_account': 'Al een account?',
    'welcome_log_in_link': 'Log in',

    // Forgot password screen
    'forgot_title': 'Wachtwoord vergeten?',
    'forgot_subtitle': 'Voer je e-mailadres in en we sturen je een herstellink',
    'forgot_button': 'Herstellink versturen',
    'forgot_back_login': 'Terug naar inloggen',
    'forgot_success_title': 'E-mail verstuurd!',
    'forgot_success_desc': 'We stuurden een herstellink naar {email}',

    // Login screen
    'login_title': 'Welkom terug',
    'login_subtitle': 'Log in om door te gaan',
    'login_email_label': 'E-mailadres',
    'login_email_hint': 'jouw@email.nl',
    'login_password_label': 'Wachtwoord',
    'login_password_hint': '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022',
    'login_forgot_password': 'Wachtwoord vergeten?',
    'login_button': 'Inloggen',
    'login_or_continue': 'Of log in met',
    'login_google': 'Doorgaan met Google',
    'login_apple': 'Doorgaan met Apple',
    'login_no_account': 'Nog geen account?',
    'login_sign_up_link': 'Registreer',

    // Register screen
    'register_title': 'Account aanmaken',
    'register_subtitle': 'Begin met besparen',
    'register_display_name': 'Weergavenaam',
    'register_display_name_hint': 'Jan de Vries',
    'register_email_label': 'E-mailadres',
    'register_email_hint': 'jan@email.nl',
    'register_password_label': 'Wachtwoord',
    'register_password_hint':
        '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022',
    'register_button': 'Registreren',
    'register_or_continue': 'Of registreer met',
    'register_google': 'Doorgaan met Google',
    'register_apple': 'Doorgaan met Apple',
    'register_have_account': 'Al een account?',
    'register_log_in_link': 'Log in',

    // Home screen
    'home_title': 'Kortingen Vandaag',
    'home_all_stores': 'Alle winkels',
    'home_view_offer': 'Bekijk Aanbieding',
    'home_empty_title': 'Nog geen aanbiedingen',
    'home_empty_subtitle':
        'Volg producten via Zoeken en we laten je weten wanneer ze in de bonus zijn',

    // Search screen
    'search_placeholder': 'Zoek product bij {store}...',
    'search_categories_title': 'Categorie\u00ebn bij {store}',
    'search_cat_deals': 'Bonus deze week',
    'search_cat_fresh': 'Verse producten',
    'search_cat_dairy': 'Zuivel & Eieren',
    'search_cat_meat': 'Vlees & Vis',
    'search_cat_drinks': 'Dranken',
    'search_no_categories': 'Geen categorieën gevonden',
    'search_no_results': 'Geen producten gevonden',
    'error_generic': 'Er is iets misgegaan',
    'retry_button': 'Opnieuw proberen',

    // Product detail
    'detail_back': 'Terug',
    'detail_on_sale_at': 'In de bonus bij:',
    'detail_view_at': 'Bekijk bij {store}',

    // Profile screen
    'profile_account': 'ACCOUNT',
    'profile_change_name': 'Weergavenaam wijzigen',
    'profile_change_password': 'Wachtwoord wijzigen',
    'profile_preferences': 'VOORKEUREN',
    'profile_language': 'Taal',
    'profile_theme': 'Thema',
    'profile_notifications_section': 'NOTIFICATIES',
    'profile_push_notifications': 'Push notificaties',
    'profile_other': 'OVERIG',
    'profile_help': 'Help & FAQ',
    'profile_privacy': 'Privacy beleid',
    'profile_about': 'Over KortingKlok',
    'profile_logout': 'Uitloggen',
    'profile_change_email': 'E-mailadres wijzigen',
    'profile_new_email_label': 'Nieuw e-mailadres',
    'profile_new_email_hint': 'nieuw@email.nl',
    'profile_current_password_label': 'Huidig wachtwoord',
    'profile_new_password_label': 'Nieuw wachtwoord',
    'profile_save': 'Opslaan',
    'profile_name_updated': 'Weergavenaam bijgewerkt',
    'profile_password_updated': 'Wachtwoord bijgewerkt',
    'profile_email_verify_sent':
        'Verificatielink verstuurd naar je nieuwe e-mailadres',

    // Theme options
    'theme_light': 'Licht',
    'theme_dark': 'Donker',
    'theme_system': 'Systeem',

    // Language options
    'lang_english': 'English \ud83c\uddec\ud83c\udde7',
    'lang_dutch': 'Nederlands \ud83c\uddf3\ud83c\uddf1',

    // Nav
    'nav_home': 'Home',
    'nav_search': 'Zoeken',
    'nav_profile': 'Profiel',

    // Product badges
    'badge_buy1get1': '1+1 GRATIS',
    'badge_half_price': '2e HALVE PRIJS',

    // Validation
    'validation_required': 'Dit veld is verplicht',
    'validation_email_invalid': 'Voer een geldig e-mailadres in',
    'validation_password_min': 'Wachtwoord moet minimaal 6 tekens bevatten',

    // Auth errors
    'auth_error_invalid_credential': 'Onjuist e-mailadres of wachtwoord',
    'auth_error_user_not_found': 'Geen account gevonden voor dit e-mailadres',
    'auth_error_email_in_use': 'Dit e-mailadres is al in gebruik',
    'auth_error_weak_password': 'Wachtwoord te zwak (min. 6 tekens)',
    'auth_error_network': 'Geen internetverbinding',
    'auth_error_cancelled': 'Inloggen geannuleerd',
    'auth_error_unknown': 'Er ging iets mis, probeer het opnieuw',
    'auth_error_wrong_password': 'Onjuist wachtwoord',
    'auth_error_requires_recent_login': 'Log opnieuw in en probeer het opnieuw',
  },
};
