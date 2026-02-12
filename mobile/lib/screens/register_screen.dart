import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state.dart';
import '../theme/app_colors.dart';
import '../widgets/kk_logo.dart';

class RegisterScreen extends StatelessWidget {
  const RegisterScreen({super.key});

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
                // First + Last name row
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildLabel(l.registerFirstName, isDark),
                          const SizedBox(height: 5),
                          TextField(
                            decoration: InputDecoration(
                              hintText: l.registerFirstNameHint,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildLabel(l.registerLastName, isDark),
                          const SizedBox(height: 5),
                          TextField(
                            decoration: InputDecoration(
                              hintText: l.registerLastNameHint,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                // Email field
                _buildLabel(l.registerEmailLabel, isDark),
                const SizedBox(height: 5),
                TextField(
                  decoration: InputDecoration(hintText: l.registerEmailHint),
                  keyboardType: TextInputType.emailAddress,
                ),
                const SizedBox(height: 14),
                // Password field
                _buildLabel(l.registerPasswordLabel, isDark),
                const SizedBox(height: 5),
                TextField(
                  decoration: InputDecoration(hintText: l.registerPasswordHint),
                  obscureText: true,
                ),
                const SizedBox(height: 16),
                // Sign up button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      AppStateScope.of(context).login();
                      Navigator.pushNamedAndRemoveUntil(
                        context,
                        '/home',
                        (_) => false,
                      );
                    },
                    child: Text(l.registerButton),
                  ),
                ),
                const SizedBox(height: 18),
                // Social divider
                _SocialDivider(text: l.registerOrContinue, isDark: isDark),
                const SizedBox(height: 14),
                // Google button
                _SocialButton(
                  icon: Icons.g_mobiledata,
                  label: l.registerGoogle,
                  isDark: isDark,
                ),
                const SizedBox(height: 8),
                // Apple button
                _SocialButton(
                  icon: Icons.apple,
                  label: l.registerApple,
                  isDark: isDark,
                  isApple: true,
                ),
                const SizedBox(height: 16),
                // Login link
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
                      onTap: () =>
                          Navigator.pushReplacementNamed(context, '/login'),
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
              ],
            ),
          ),
        ),
      ),
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

  const _SocialButton({
    required this.icon,
    required this.label,
    required this.isDark,
    this.isApple = false,
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
        onPressed: () {},
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
