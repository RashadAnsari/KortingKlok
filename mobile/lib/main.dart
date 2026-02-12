import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'l10n/app_localizations.dart';
import 'providers/app_state.dart';
import 'theme/app_theme.dart';
import 'screens/welcome_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/main_shell.dart';
import 'screens/product_detail_screen.dart';

void main() {
  runApp(const AppStateScope(child: KortingKlokApp()));
}

class KortingKlokApp extends StatelessWidget {
  const KortingKlokApp({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = AppState.of(context);

    return MaterialApp(
      title: 'KortingKlok',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: appState.themeMode,
      locale: appState.locale,
      supportedLocales: const [Locale('nl'), Locale('en')],
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      initialRoute: '/welcome',
      routes: {
        '/welcome': (_) => const WelcomeScreen(),
        '/login': (_) => const LoginScreen(),
        '/register': (_) => const RegisterScreen(),
        '/home': (_) => const MainShell(),
        '/product-detail': (_) => const ProductDetailScreen(),
      },
    );
  }
}
