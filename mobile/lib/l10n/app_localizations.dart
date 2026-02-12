import 'package:flutter/widgets.dart';
import 'translations.dart';

class AppLocalizations {
  final Locale locale;

  AppLocalizations(this.locale);

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  String _t(String key) {
    final lang = locale.languageCode;
    return translations[lang]?[key] ?? translations['en']?[key] ?? key;
  }

  String _tWithParam(String key, String param, String value) {
    return _t(key).replaceAll('{$param}', value);
  }

  // Welcome
  String get welcomeTitle => _t('welcome_title');
  String get welcomeTagline => _t('welcome_tagline');
  String get welcomeFeature1Title => _t('welcome_feature1_title');
  String get welcomeFeature1Desc => _t('welcome_feature1_desc');
  String get welcomeFeature2Title => _t('welcome_feature2_title');
  String get welcomeFeature2Desc => _t('welcome_feature2_desc');
  String get welcomeFeature3Title => _t('welcome_feature3_title');
  String get welcomeFeature3Desc => _t('welcome_feature3_desc');
  String get welcomeGetStarted => _t('welcome_get_started');
  String get welcomeHaveAccount => _t('welcome_have_account');
  String get welcomeLogInLink => _t('welcome_log_in_link');

  // Login
  String get loginTitle => _t('login_title');
  String get loginSubtitle => _t('login_subtitle');
  String get loginEmailLabel => _t('login_email_label');
  String get loginEmailHint => _t('login_email_hint');
  String get loginPasswordLabel => _t('login_password_label');
  String get loginPasswordHint => _t('login_password_hint');
  String get loginForgotPassword => _t('login_forgot_password');
  String get loginButton => _t('login_button');
  String get loginOrContinue => _t('login_or_continue');
  String get loginGoogle => _t('login_google');
  String get loginApple => _t('login_apple');
  String get loginNoAccount => _t('login_no_account');
  String get loginSignUpLink => _t('login_sign_up_link');

  // Register
  String get registerTitle => _t('register_title');
  String get registerSubtitle => _t('register_subtitle');
  String get registerFirstName => _t('register_first_name');
  String get registerFirstNameHint => _t('register_first_name_hint');
  String get registerLastName => _t('register_last_name');
  String get registerLastNameHint => _t('register_last_name_hint');
  String get registerEmailLabel => _t('register_email_label');
  String get registerEmailHint => _t('register_email_hint');
  String get registerPasswordLabel => _t('register_password_label');
  String get registerPasswordHint => _t('register_password_hint');
  String get registerButton => _t('register_button');
  String get registerOrContinue => _t('register_or_continue');
  String get registerGoogle => _t('register_google');
  String get registerApple => _t('register_apple');
  String get registerHaveAccount => _t('register_have_account');
  String get registerLogInLink => _t('register_log_in_link');

  // Home
  String get homeTitle => _t('home_title');
  String get homeAllStores => _t('home_all_stores');
  String get homeViewOffer => _t('home_view_offer');

  // Search
  String searchPlaceholder(String store) =>
      _tWithParam('search_placeholder', 'store', store);
  String searchCategoriesTitle(String store) =>
      _tWithParam('search_categories_title', 'store', store);
  String get searchCatDeals => _t('search_cat_deals');
  String get searchCatFresh => _t('search_cat_fresh');
  String get searchCatDairy => _t('search_cat_dairy');
  String get searchCatMeat => _t('search_cat_meat');
  String get searchCatDrinks => _t('search_cat_drinks');

  // Product detail
  String get detailBack => _t('detail_back');
  String get detailOnSaleAt => _t('detail_on_sale_at');
  String detailViewAt(String store) =>
      _tWithParam('detail_view_at', 'store', store);

  // Profile
  String get profileAccount => _t('profile_account');
  String get profileChangeName => _t('profile_change_name');
  String get profileChangePassword => _t('profile_change_password');
  String get profilePreferences => _t('profile_preferences');
  String get profileLanguage => _t('profile_language');
  String get profileTheme => _t('profile_theme');
  String get profileNotificationsSection => _t('profile_notifications_section');
  String get profilePushNotifications => _t('profile_push_notifications');
  String get profileOther => _t('profile_other');
  String get profileHelp => _t('profile_help');
  String get profilePrivacy => _t('profile_privacy');
  String get profileAbout => _t('profile_about');
  String get profileLogout => _t('profile_logout');

  // Theme
  String get themeLight => _t('theme_light');
  String get themeDark => _t('theme_dark');
  String get themeSystem => _t('theme_system');

  // Language
  String get langEnglish => _t('lang_english');
  String get langDutch => _t('lang_dutch');

  // Nav
  String get navHome => _t('nav_home');
  String get navSearch => _t('nav_search');
  String get navProfile => _t('nav_profile');

  // Badges
  String get badgeBuy1Get1 => _t('badge_buy1get1');
  String get badgeHalfPrice => _t('badge_half_price');
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) => ['en', 'nl'].contains(locale.languageCode);

  @override
  Future<AppLocalizations> load(Locale locale) async =>
      AppLocalizations(locale);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}
