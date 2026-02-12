import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppStateScope extends StatefulWidget {
  final Widget child;

  const AppStateScope({super.key, required this.child});

  @override
  State<AppStateScope> createState() => AppStateScopeState();

  static AppStateScopeState of(BuildContext context) {
    return context.findAncestorStateOfType<AppStateScopeState>()!;
  }
}

class AppStateScopeState extends State<AppStateScope> {
  static const _keyLocale = 'user_locale';
  static const _keyThemeMode = 'user_theme_mode';

  // User preferences (null = not yet set by user)
  Locale? _userLocale;
  ThemeMode? _userThemeMode;

  bool _isAuthenticated = false;
  bool _loaded = false;

  bool get isAuthenticated => _isAuthenticated;

  /// Effective locale: auth screens always Dutch, after auth use user pref or Dutch default.
  Locale get locale {
    if (!_isAuthenticated) return const Locale('nl');
    return _userLocale ?? const Locale('nl');
  }

  /// Effective theme: auth screens always system, after auth use user pref or system default.
  ThemeMode get themeMode {
    if (!_isAuthenticated) return ThemeMode.system;
    return _userThemeMode ?? ThemeMode.system;
  }

  /// The raw user preference (for showing current selection in Profile dropdown).
  Locale? get userLocale => _userLocale;
  ThemeMode? get userThemeMode => _userThemeMode;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    final localeCode = prefs.getString(_keyLocale);
    final themeModeIndex = prefs.getInt(_keyThemeMode);

    setState(() {
      _userLocale = localeCode != null ? Locale(localeCode) : null;
      _userThemeMode = themeModeIndex != null
          ? ThemeMode.values[themeModeIndex]
          : null;
      _loaded = true;
    });
  }

  Future<void> setLocale(Locale locale) async {
    setState(() => _userLocale = locale);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyLocale, locale.languageCode);
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    setState(() => _userThemeMode = mode);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_keyThemeMode, mode.index);
  }

  /// Call after successful login/register to enter authenticated state.
  void login() {
    setState(() => _isAuthenticated = true);
  }

  /// Clear all user preferences and return to unauthenticated state.
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyLocale);
    await prefs.remove(_keyThemeMode);
    setState(() {
      _userLocale = null;
      _userThemeMode = null;
      _isAuthenticated = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_loaded) {
      return const SizedBox.shrink();
    }
    return AppState(
      locale: locale,
      themeMode: themeMode,
      userLocale: _userLocale,
      userThemeMode: _userThemeMode,
      isAuthenticated: _isAuthenticated,
      child: widget.child,
    );
  }
}

class AppState extends InheritedWidget {
  final Locale locale;
  final ThemeMode themeMode;
  final Locale? userLocale;
  final ThemeMode? userThemeMode;
  final bool isAuthenticated;

  const AppState({
    super.key,
    required this.locale,
    required this.themeMode,
    required this.userLocale,
    required this.userThemeMode,
    required this.isAuthenticated,
    required super.child,
  });

  static AppState of(BuildContext context) {
    return context.dependOnInheritedWidgetOfExactType<AppState>()!;
  }

  @override
  bool updateShouldNotify(AppState oldWidget) {
    return locale != oldWidget.locale ||
        themeMode != oldWidget.themeMode ||
        isAuthenticated != oldWidget.isAuthenticated ||
        userLocale != oldWidget.userLocale ||
        userThemeMode != oldWidget.userThemeMode;
  }
}
