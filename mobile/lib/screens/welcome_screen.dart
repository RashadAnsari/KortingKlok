import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../widgets/kk_logo.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            children: [
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(height: 20),
                      const KKLogo(size: 80),
                      const SizedBox(height: 14),
                      Text(
                        l.welcomeTitle,
                        style: TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.w700,
                          color: isDark
                              ? AppColors.darkText
                              : AppColors.darkBlue,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        l.welcomeTagline,
                        style: TextStyle(
                          fontSize: 14,
                          color: isDark
                              ? AppColors.darkSecondary
                              : AppColors.midGray,
                        ),
                      ),
                      const SizedBox(height: 24),
                      Center(
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 340),
                          child: Column(
                            children: [
                              _FeatureItem(
                                icon: Icons.smartphone,
                                title: l.welcomeFeature1Title,
                                description: l.welcomeFeature1Desc,
                              ),
                              const SizedBox(height: 18),
                              _FeatureItem(
                                icon: Icons.notifications_active,
                                title: l.welcomeFeature2Title,
                                description: l.welcomeFeature2Desc,
                              ),
                              const SizedBox(height: 18),
                              _FeatureItem(
                                icon: Icons.savings,
                                title: l.welcomeFeature3Title,
                                description: l.welcomeFeature3Desc,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pushNamed(context, '/register'),
                  child: Text(l.welcomeGetStarted),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '${l.welcomeHaveAccount} ',
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.lightSecondary,
                    ),
                  ),
                  GestureDetector(
                    onTap: () => Navigator.pushNamed(context, '/login'),
                    child: Text(
                      l.welcomeLogInLink,
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
    );
  }
}

class _FeatureItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;

  const _FeatureItem({
    required this.icon,
    required this.title,
    required this.description,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 26, color: AppColors.primaryOrange),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: isDark ? AppColors.darkText : AppColors.darkBlue,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                description,
                style: const TextStyle(
                  fontSize: 13,
                  color: AppColors.lightSecondary,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
