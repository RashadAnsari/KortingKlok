import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/auth_service.dart';
import '../theme/app_colors.dart';
import '../widgets/kk_logo.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _authService = AuthService();
  final _emailController = TextEditingController();

  bool _isLoading = false;
  bool _sent = false;
  String? _emailError;
  String? _error;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  bool _validateEmail(AppLocalizations l) {
    final email = _emailController.text.trim();
    String? err;
    if (email.isEmpty) {
      err = l.validationRequired;
    } else if (!RegExp(r'^[^@]+@[^@]+\.[^@]+$').hasMatch(email)) {
      err = l.validationEmailInvalid;
    }
    setState(() => _emailError = err);
    return err == null;
  }

  Future<void> _sendReset(AppLocalizations l) async {
    if (!_validateEmail(l)) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await _authService.sendPasswordResetEmail(_emailController.text.trim());
      if (mounted) setState(() => _sent = true);
    } catch (e) {
      if (!mounted) return;
      if (e is FirebaseAuthException && e.code == 'network-request-failed') {
        setState(() => _error = l.authErrorNetwork);
      } else {
        // For all other errors (e.g. user-not-found) still show success
        // so we don't reveal whether an account exists.
        setState(() => _sent = true);
      }
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
            child: _sent ? _buildSuccess(l, isDark) : _buildForm(l, isDark),
          ),
        ),
      ),
    );
  }

  Widget _buildForm(AppLocalizations l, bool isDark) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        const SizedBox(height: 10),
        const KKLogo(size: 80),
        const SizedBox(height: 14),
        Text(
          l.forgotTitle,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: isDark ? AppColors.darkText : AppColors.darkBlue,
          ),
        ),
        const SizedBox(height: 5),
        Text(
          l.forgotSubtitle,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 13, color: AppColors.lightSecondary),
        ),
        const SizedBox(height: 28),
        // Email field
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildLabel(l.loginEmailLabel, isDark),
            const SizedBox(height: 5),
            TextField(
              controller: _emailController,
              decoration: InputDecoration(
                hintText: l.loginEmailHint,
                errorText: _emailError,
              ),
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.done,
              enabled: !_isLoading,
              onChanged: (_) {
                if (_emailError != null) setState(() => _emailError = null);
              },
              onSubmitted: (_) => _sendReset(l),
            ),
          ],
        ),
        const SizedBox(height: 16),
        // Network error banner
        if (_error != null) ...[
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
            decoration: BoxDecoration(
              color: Colors.red.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
            ),
            child: Text(
              _error!,
              style: const TextStyle(fontSize: 13, color: Colors.red),
            ),
          ),
          const SizedBox(height: 10),
        ],
        // Send button
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _isLoading ? null : () => _sendReset(l),
            child: _isLoading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : Text(l.forgotButton),
          ),
        ),
        const SizedBox(height: 20),
        // Back to login
        GestureDetector(
          onTap: _isLoading ? null : () => Navigator.pop(context),
          child: Text(
            l.forgotBackLogin,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppColors.primaryOrange,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSuccess(AppLocalizations l, bool isDark) {
    final email = _emailController.text.trim();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        const SizedBox(height: 40),
        const KKLogo(size: 80),
        const SizedBox(height: 32),
        Container(
          width: 72,
          height: 72,
          decoration: BoxDecoration(
            color: Colors.green.withValues(alpha: 0.12),
            shape: BoxShape.circle,
          ),
          child: const Icon(
            Icons.mark_email_read_outlined,
            size: 36,
            color: Colors.green,
          ),
        ),
        const SizedBox(height: 20),
        Text(
          l.forgotSuccessTitle,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: isDark ? AppColors.darkText : AppColors.darkBlue,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          l.forgotSuccessDesc(email),
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 14,
            color: AppColors.lightSecondary,
            height: 1.5,
          ),
        ),
        const SizedBox(height: 32),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () => Navigator.pop(context),
            child: Text(l.forgotBackLogin),
          ),
        ),
      ],
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
