import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state.dart';
import '../services/auth_service.dart';
import '../theme/app_colors.dart';
import '../widgets/kk_logo.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _authService = AuthService();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isLoading = false;
  String? _error;

  String? _emailError;
  String? _passwordError;

  late final TapGestureRecognizer _termsRecognizer;
  late final TapGestureRecognizer _privacyRecognizer;

  @override
  void initState() {
    super.initState();
    _termsRecognizer = TapGestureRecognizer()
      ..onTap = () {
        final lang = AppState.of(context).locale.languageCode;
        final url = lang == 'en'
            ? 'https://kortingklok.nl/en/terms/'
            : 'https://kortingklok.nl/terms/';
        launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      };
    _privacyRecognizer = TapGestureRecognizer()
      ..onTap = () {
        final lang = AppState.of(context).locale.languageCode;
        final url = lang == 'en'
            ? 'https://kortingklok.nl/en/privacy/'
            : 'https://kortingklok.nl/privacy/';
        launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      };
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _termsRecognizer.dispose();
    _privacyRecognizer.dispose();
    super.dispose();
  }

  bool _validate(AppLocalizations l) {
    String? em;
    String? pw;

    final email = _emailController.text.trim();
    if (email.isEmpty) {
      em = l.validationRequired;
    } else if (!RegExp(r'^[^@]+@[^@]+\.[^@]+$').hasMatch(email)) {
      em = l.validationEmailInvalid;
    }

    if (_passwordController.text.isEmpty) {
      pw = l.validationRequired;
    } else if (_passwordController.text.length < 6) {
      pw = l.validationPasswordMin;
    }

    setState(() {
      _emailError = em;
      _passwordError = pw;
    });

    return em == null && pw == null;
  }

  String _mapFirebaseError(Object e, AppLocalizations l) {
    if (e is FirebaseAuthException) {
      switch (e.code) {
        case 'invalid-credential':
        case 'wrong-password':
          return l.authErrorInvalidCredential;
        case 'user-not-found':
          return l.authErrorUserNotFound;
        case 'network-request-failed':
          return l.authErrorNetwork;
        default:
          return l.authErrorUnknown;
      }
    }
    final msg = e.toString();
    if (msg.contains('cancelled') || msg.contains('canceled')) {
      return l.authErrorCancelled;
    }
    return l.authErrorUnknown;
  }

  Future<void> _signInWithEmail(AppLocalizations l) async {
    if (!_validate(l)) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await _authService.signInWithEmailPassword(
        _emailController.text,
        _passwordController.text,
      );
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(context, '/home', (_) => false);
      }
    } catch (e) {
      if (mounted) setState(() => _error = _mapFirebaseError(e, l));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _signInWithGoogle(AppLocalizations l) async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await _authService.signInWithGoogle();
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(context, '/home', (_) => false);
      }
    } catch (e) {
      if (mounted) setState(() => _error = _mapFirebaseError(e, l));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _signInWithApple(AppLocalizations l) async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await _authService.signInWithApple();
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(context, '/home', (_) => false);
      }
    } catch (e) {
      if (mounted) setState(() => _error = _mapFirebaseError(e, l));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const SizedBox(height: 10),
                const KKLogo(size: 80),
                const SizedBox(height: 14),
                Text(
                  l.loginTitle,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                    color: isDark ? AppColors.darkText : AppColors.darkBlue,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  l.loginSubtitle,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.lightSecondary,
                  ),
                ),
                const SizedBox(height: 22),
                _buildLabel(l.loginEmailLabel, isDark),
                const SizedBox(height: 5),
                TextField(
                  controller: _emailController,
                  decoration: InputDecoration(
                    hintText: l.loginEmailHint,
                    errorText: _emailError,
                  ),
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  enabled: !_isLoading,
                  onChanged: (_) {
                    if (_emailError != null) {
                      setState(() => _emailError = null);
                    }
                  },
                ),
                const SizedBox(height: 14),
                _buildLabel(l.loginPasswordLabel, isDark),
                const SizedBox(height: 5),
                TextField(
                  controller: _passwordController,
                  decoration: InputDecoration(
                    hintText: l.loginPasswordHint,
                    errorText: _passwordError,
                  ),
                  obscureText: true,
                  textInputAction: TextInputAction.done,
                  enabled: !_isLoading,
                  onSubmitted: (_) => _signInWithEmail(l),
                  onChanged: (_) {
                    if (_passwordError != null) {
                      setState(() => _passwordError = null);
                    }
                  },
                ),
                const SizedBox(height: 6),
                Align(
                  alignment: Alignment.centerRight,
                  child: GestureDetector(
                    onTap: _isLoading
                        ? null
                        : () =>
                              Navigator.pushNamed(context, '/forgot-password'),
                    child: Text(
                      l.loginForgotPassword,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primaryOrange,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                if (_error != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 9,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.red.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: Colors.red.withValues(alpha: 0.3),
                      ),
                    ),
                    child: Text(
                      _error!,
                      style: const TextStyle(fontSize: 13, color: Colors.red),
                    ),
                  ),
                  const SizedBox(height: 10),
                ],
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : () => _signInWithEmail(l),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : Text(l.loginButton),
                  ),
                ),
                const SizedBox(height: 18),
                _SocialDivider(text: l.loginOrContinue, isDark: isDark),
                const SizedBox(height: 14),
                _SocialButton(
                  icon: Icons.g_mobiledata,
                  label: l.loginGoogle,
                  isDark: isDark,
                  isLoading: _isLoading,
                  onPressed: () => _signInWithGoogle(l),
                ),
                const SizedBox(height: 8),
                _SocialButton(
                  icon: Icons.apple,
                  label: l.loginApple,
                  isDark: isDark,
                  isApple: true,
                  isLoading: _isLoading,
                  onPressed: () => _signInWithApple(l),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      '${l.loginNoAccount} ',
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.lightSecondary,
                      ),
                    ),
                    GestureDetector(
                      onTap: _isLoading
                          ? null
                          : () => Navigator.pushReplacementNamed(
                              context,
                              '/register',
                            ),
                      child: Text(
                        l.loginSignUpLink,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppColors.primaryOrange,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Text.rich(
                  TextSpan(
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.lightSecondary,
                    ),
                    children: [
                      TextSpan(text: '${l.registerTermsPrefix} '),
                      TextSpan(
                        text: l.registerTermsLink,
                        style: const TextStyle(
                          color: AppColors.primaryOrange,
                          decoration: TextDecoration.underline,
                          decorationColor: AppColors.primaryOrange,
                        ),
                        recognizer: _termsRecognizer,
                      ),
                      TextSpan(text: l.registerTermsAnd),
                      TextSpan(
                        text: l.registerPrivacyLink,
                        style: const TextStyle(
                          color: AppColors.primaryOrange,
                          decoration: TextDecoration.underline,
                          decorationColor: AppColors.primaryOrange,
                        ),
                        recognizer: _privacyRecognizer,
                      ),
                      const TextSpan(text: '.'),
                    ],
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLabel(String text, bool isDark) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: isDark ? AppColors.darkText : AppColors.lightText,
        ),
      ),
    );
  }
}

class _SocialDivider extends StatelessWidget {
  final String text;
  final bool isDark;

  const _SocialDivider({required this.text, required this.isDark});

  @override
  Widget build(BuildContext context) {
    final dividerColor = isDark ? AppColors.darkBorder : AppColors.lightBorder;
    return Row(
      children: [
        Expanded(child: Divider(color: dividerColor)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.lightSecondary,
            ),
          ),
        ),
        Expanded(child: Divider(color: dividerColor)),
      ],
    );
  }
}

class _SocialButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isDark;
  final bool isApple;
  final bool isLoading;
  final VoidCallback onPressed;

  const _SocialButton({
    required this.icon,
    required this.label,
    required this.isDark,
    required this.onPressed,
    this.isApple = false,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    Color border;

    if (isApple) {
      bg = isDark ? Colors.white : Colors.black;
      fg = isDark ? Colors.black : Colors.white;
      border = isDark ? Colors.white : Colors.black;
    } else {
      bg = isDark ? AppColors.darkSurface : Colors.white;
      fg = isDark ? AppColors.darkText : AppColors.lightText;
      border = isDark ? AppColors.darkBorder : AppColors.lightBorder;
    }

    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: isLoading ? null : onPressed,
        icon: Icon(icon, size: 20, color: fg),
        label: Text(
          label,
          style: TextStyle(
            color: fg,
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
        style: OutlinedButton.styleFrom(
          backgroundColor: bg,
          side: BorderSide(color: border),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(vertical: 11),
        ),
      ),
    );
  }
}
