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

  String get forgotTitle => _t('forgot_title');
  String get forgotSubtitle => _t('forgot_subtitle');
  String get forgotButton => _t('forgot_button');
  String get forgotBackLogin => _t('forgot_back_login');
  String get forgotSuccessTitle => _t('forgot_success_title');
  String forgotSuccessDesc(String email) =>
      _tWithParam('forgot_success_desc', 'email', email);

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

  String get registerTitle => _t('register_title');
  String get registerSubtitle => _t('register_subtitle');
  String get registerDisplayName => _t('register_display_name');
  String get registerDisplayNameHint => _t('register_display_name_hint');
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

  String get homeTitle => _t('home_title');
  String get homeAllStores => _t('home_all_stores');
  String get homeEmptyTitle => _t('home_empty_title');
  String get homeEmptySubtitle => _t('home_empty_subtitle');

  String searchPlaceholder(String store) =>
      _tWithParam('search_placeholder', 'store', store);
  String searchCategoriesTitle(String store) =>
      _tWithParam('search_categories_title', 'store', store);
  String get searchNoCategories => _t('search_no_categories');
  String get searchNoResults => _t('search_no_results');
  String get errorGeneric => _t('error_generic');
  String get retryButton => _t('retry_button');

  String get detailBack => _t('detail_back');
  String get detailOnSaleAt => _t('detail_on_sale_at');
  String detailViewAt(String store) =>
      _tWithParam('detail_view_at', 'store', store);

  String get profileAccount => _t('profile_account');
  String get profileChangeName => _t('profile_change_name');
  String get profileChangePassword => _t('profile_change_password');
  String get profilePreferences => _t('profile_preferences');
  String get profileLanguage => _t('profile_language');
  String get profileTheme => _t('profile_theme');
  String get profileOther => _t('profile_other');
  String get profileHelp => _t('profile_help');
  String get profilePrivacy => _t('profile_privacy');
  String get profileAbout => _t('profile_about');
  String get profileLogout => _t('profile_logout');
  String get profileChangeEmail => _t('profile_change_email');
  String get profileNewEmailLabel => _t('profile_new_email_label');
  String get profileNewEmailHint => _t('profile_new_email_hint');
  String get profileCurrentPasswordLabel =>
      _t('profile_current_password_label');
  String get profileNewPasswordLabel => _t('profile_new_password_label');
  String get profileSave => _t('profile_save');
  String get profileNameUpdated => _t('profile_name_updated');
  String get profilePasswordUpdated => _t('profile_password_updated');
  String get profileEmailVerifySent => _t('profile_email_verify_sent');

  String get themeLight => _t('theme_light');
  String get themeDark => _t('theme_dark');
  String get themeSystem => _t('theme_system');

  String get langEnglish => _t('lang_english');
  String get langDutch => _t('lang_dutch');

  String get navHome => _t('nav_home');
  String get navSearch => _t('nav_search');
  String get navProfile => _t('nav_profile');

  String get validationRequired => _t('validation_required');
  String get validationEmailInvalid => _t('validation_email_invalid');
  String get validationPasswordMin => _t('validation_password_min');

  String get authErrorInvalidCredential => _t('auth_error_invalid_credential');
  String get authErrorUserNotFound => _t('auth_error_user_not_found');
  String get authErrorEmailInUse => _t('auth_error_email_in_use');
  String get authErrorWeakPassword => _t('auth_error_weak_password');
  String get authErrorNetwork => _t('auth_error_network');
  String get authErrorCancelled => _t('auth_error_cancelled');
  String get authErrorUnknown => _t('auth_error_unknown');
  String get authErrorWrongPassword => _t('auth_error_wrong_password');
  String get authErrorRequiresRecentLogin =>
      _t('auth_error_requires_recent_login');
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
