/// Build-time configuration for the app.
///
/// Every value can be overridden per build without touching the source:
///
///   flutter run \
///     --dart-define=API_HOST=https://api.ansarihamedani.me \
///     --dart-define=WEBSITE_URL=https://ansarihamedani.me \
///     --dart-define=SUPPORT_EMAIL=hello@ansarihamedani.me
class AppConfig {
  /// Base URL of the KortingKlok backend, without a trailing slash.
  static const String apiHost = String.fromEnvironment(
    'API_HOST',
    defaultValue: 'http://localhost:8000',
  );

  /// Public website that serves the terms and privacy pages.
  /// When empty, the app shows that text without outbound links.
  static const String websiteUrl = String.fromEnvironment('WEBSITE_URL');

  /// Address behind the "contact support" entry.
  /// When empty, the entry is hidden.
  static const String supportEmail = String.fromEnvironment('SUPPORT_EMAIL');

  static bool get hasWebsite => websiteUrl.isNotEmpty;

  static bool get hasSupportEmail => supportEmail.isNotEmpty;

  /// URL of a page on the website in the given language. Dutch is served from
  /// the root, English from `/en`. Pass an empty [path] for the home page.
  static String pageUrl(String path, String languageCode) {
    final root = languageCode == 'en' ? '$websiteUrl/en' : websiteUrl;
    return path.isEmpty ? '$root/' : '$root/$path/';
  }
}
