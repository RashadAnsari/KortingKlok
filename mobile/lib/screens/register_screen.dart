import 'dart:io';
import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/auth_service.dart';
import '../theme/app_colors.dart';
import '../utils/firebase_error_mapper.dart';
import '../utils/validators.dart';
import '../widgets/kk_logo.dart';
import '../widgets/social_button.dart';
import '../widgets/terms_text.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _authService = AuthService();
  final _displayNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isLoading = false;
  String? _error;

  String? _displayNameError;
  String? _emailError;
  String? _passwordError;

  @override
  void dispose() {
    _displayNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  bool _validate(AppLocalizations l) {
    String? dn;
    String? em;
    String? pw;

    if (_displayNameController.text.trim().isEmpty) dn = l.validationRequired;

    final email = _emailController.text.trim();
    if (email.isEmpty) {
      em = l.validationRequired;
    } else if (!isValidEmail(email)) {
      em = l.validationEmailInvalid;
    }

    if (_passwordController.text.isEmpty) {
      pw = l.validationRequired;
    } else if (_passwordController.text.length < 6) {
      pw = l.validationPasswordMin;
    }

    setState(() {
      _displayNameError = dn;
      _emailError = em;
      _passwordError = pw;
    });

    return dn == null && em == null && pw == null;
  }

  Future<void> _registerWithEmail(AppLocalizations l) async {
    if (!_validate(l)) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await _authService.registerWithEmailPassword(
        _emailController.text.trim(),
        _passwordController.text,
        _displayNameController.text.trim(),
      );
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(context, '/home', (_) => false);
      }
    } catch (e) {
      if (mounted) setState(() => _error = mapFirebaseError(e, l));
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
      if (mounted) setState(() => _error = mapFirebaseError(e, l));
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
      if (mounted) setState(() => _error = mapFirebaseError(e, l));
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
                  l.registerTitle,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                    color: isDark ? AppColors.darkText : AppColors.darkBlue,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  l.registerSubtitle,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.lightSecondary,
                  ),
                ),
                const SizedBox(height: 22),
                _buildField(
                  label: _buildLabel(l.registerDisplayName, isDark),
                  child: TextField(
                    controller: _displayNameController,
                    decoration: InputDecoration(
                      hintText: l.registerDisplayNameHint,
                      errorText: _displayNameError,
                    ),
                    textInputAction: TextInputAction.next,
                    enabled: !_isLoading,
                    onChanged: (_) {
                      if (_displayNameError != null) {
                        setState(() => _displayNameError = null);
                      }
                    },
                  ),
                ),
                const SizedBox(height: 14),
                _buildField(
                  label: _buildLabel(l.registerEmailLabel, isDark),
                  child: TextField(
                    controller: _emailController,
                    decoration: InputDecoration(
                      hintText: l.registerEmailHint,
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
                ),
                const SizedBox(height: 14),
                _buildField(
                  label: _buildLabel(l.registerPasswordLabel, isDark),
                  child: TextField(
                    controller: _passwordController,
                    decoration: InputDecoration(
                      hintText: l.registerPasswordHint,
                      errorText: _passwordError,
                    ),
                    obscureText: true,
                    textInputAction: TextInputAction.done,
                    enabled: !_isLoading,
                    onChanged: (_) {
                      if (_passwordError != null) {
                        setState(() => _passwordError = null);
                      }
                    },
                    onSubmitted: (_) => _registerWithEmail(l),
                  ),
                ),
                const SizedBox(height: 16),
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
                    onPressed: _isLoading ? null : () => _registerWithEmail(l),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : Text(l.registerButton),
                  ),
                ),
                const SizedBox(height: 18),
                SocialDivider(text: l.registerOrContinue),
                const SizedBox(height: 14),
                SocialButton(
                  icon: Icons.g_mobiledata,
                  label: l.registerGoogle,
                  isLoading: _isLoading,
                  onPressed: () => _signInWithGoogle(l),
                ),
                if (!Platform.isAndroid) ...[
                  const SizedBox(height: 8),
                  SocialButton(
                    icon: Icons.apple,
                    label: l.registerApple,
                    isApple: true,
                    isLoading: _isLoading,
                    onPressed: () => _signInWithApple(l),
                  ),
                ],
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      '${l.registerHaveAccount} ',
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
                              '/login',
                            ),
                      child: Text(
                        l.registerLogInLink,
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
                const TermsAndPrivacyText(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildField({required Widget label, required Widget child}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [label, const SizedBox(height: 5), child],
    );
  }

  Widget _buildLabel(String text, bool isDark) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        color: isDark ? AppColors.darkText : AppColors.lightText,
      ),
    );
  }
}
