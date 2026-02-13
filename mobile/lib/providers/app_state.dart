import 'dart:async';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/auth_service.dart';
import '../services/notification_service.dart';

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

  final _authService = AuthService();
  final _notificationService = NotificationService();

  // Firebase auth state
  User? _firebaseUser;
  StreamSubscription<User?>? _authSub;

  // User preferences (null = not yet set)
  Locale? _userLocale;
  ThemeMode? _userThemeMode;

  bool _prefsLoaded = false;

  bool get isAuthenticated => _firebaseUser != null;
  String? get userName => _firebaseUser?.displayName;
  String? get userEmail => _firebaseUser?.email;

  /// Effective locale: user preference, or Dutch if not set.
  Locale get locale => _userLocale ?? const Locale('nl');

  /// Effective theme: user preference, or system if not set.
  ThemeMode get themeMode => _userThemeMode ?? ThemeMode.system;

  Locale? get userLocale => _userLocale;
  ThemeMode? get userThemeMode => _userThemeMode;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
    _authSub = FirebaseAuth.instance.userChanges().listen((user) {
      setState(() => _firebaseUser = user);
    });
  }

  @override
  void dispose() {
    _authSub?.cancel();
    super.dispose();
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
      _prefsLoaded = true;
    });
    // Sync Firebase email language with the loaded preference (or NL default).
    FirebaseAuth.instance.setLanguageCode(_userLocale?.languageCode ?? 'nl');
  }

  Future<void> setLocale(Locale locale) async {
    setState(() => _userLocale = locale);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyLocale, locale.languageCode);
    // Keep Firebase email language in sync with the user's choice.
    FirebaseAuth.instance.setLanguageCode(locale.languageCode);
    // Re-register device with the new language for push notifications.
    try {
      await _notificationService.registerDevice(locale.languageCode);
    } catch (_) {}
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    setState(() => _userThemeMode = mode);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_keyThemeMode, mode.index);
  }

  /// Sign out from Firebase. Preferences (locale, theme) are kept.
  Future<void> logout() async {
    try {
      await _notificationService.unregisterDevice();
    } catch (_) {
      // Best-effort: don't block logout if device unregistration fails.
    }
    await _notificationService.clearRegistration();
    await _authService.signOut();
    // _firebaseUser is set to null automatically by the authStateChanges stream.
  }

  @override
  Widget build(BuildContext context) {
    if (!_prefsLoaded) return const SizedBox.shrink();
    return AppState(
      locale: locale,
      themeMode: themeMode,
      userLocale: _userLocale,
      userThemeMode: _userThemeMode,
      isAuthenticated: isAuthenticated,
      userName: userName,
      userEmail: userEmail,
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
  final String? userName;
  final String? userEmail;

  const AppState({
    super.key,
    required this.locale,
    required this.themeMode,
    required this.userLocale,
    required this.userThemeMode,
    required this.isAuthenticated,
    required this.userName,
    required this.userEmail,
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
        userThemeMode != oldWidget.userThemeMode ||
        userName != oldWidget.userName ||
        userEmail != oldWidget.userEmail;
  }
}
