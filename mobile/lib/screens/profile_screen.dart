import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../providers/app_state.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _pushEnabled = true;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final appState = AppStateScope.of(context);
    final currentLocale = appState.userLocale ?? const Locale('nl');
    final currentTheme = appState.userThemeMode ?? ThemeMode.system;

    return SingleChildScrollView(
      child: Column(
        children: [
          // Profile header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 28),
            decoration: BoxDecoration(
              border: Border(
                bottom: BorderSide(
                  color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                ),
              ),
            ),
            child: Column(
              children: [
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    color: isDark ? AppColors.darkBorder : AppColors.lightGray,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.person,
                    size: 36,
                    color: isDark
                        ? AppColors.darkText
                        : AppColors.lightSecondary,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  'Jan de Vries',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                    color: isDark ? AppColors.darkText : AppColors.darkBlue,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'jan@example.com',
                  style: TextStyle(
                    fontSize: 14,
                    color: isDark
                        ? AppColors.darkSecondary
                        : const Color(0xFF666666),
                  ),
                ),
              ],
            ),
          ),

          // Account section
          _SettingsSection(
            title: l.profileAccount,
            isDark: isDark,
            children: [
              _SettingRow(
                label: l.profileChangeName,
                isDark: isDark,
                trailing: Icon(
                  Icons.arrow_forward_ios,
                  size: 14,
                  color: AppColors.lightSecondary,
                ),
                onTap: () {},
              ),
              _SettingRow(
                label: l.profileChangePassword,
                isDark: isDark,
                trailing: Icon(
                  Icons.arrow_forward_ios,
                  size: 14,
                  color: AppColors.lightSecondary,
                ),
                onTap: () {},
              ),
            ],
          ),

          // Preferences section
          _SettingsSection(
            title: l.profilePreferences,
            isDark: isDark,
            children: [
              _SettingRow(
                label: l.profileLanguage,
                isDark: isDark,
                trailing: _buildDropdown<String>(
                  value: currentLocale.languageCode,
                  items: [
                    DropdownMenuItem(value: 'en', child: Text(l.langEnglish)),
                    DropdownMenuItem(value: 'nl', child: Text(l.langDutch)),
                  ],
                  onChanged: (val) {
                    if (val != null) {
                      appState.setLocale(Locale(val));
                    }
                  },
                  isDark: isDark,
                ),
              ),
              _SettingRow(
                label: l.profileTheme,
                isDark: isDark,
                trailing: _buildDropdown<ThemeMode>(
                  value: currentTheme,
                  items: [
                    DropdownMenuItem(
                      value: ThemeMode.light,
                      child: Text(l.themeLight),
                    ),
                    DropdownMenuItem(
                      value: ThemeMode.dark,
                      child: Text(l.themeDark),
                    ),
                    DropdownMenuItem(
                      value: ThemeMode.system,
                      child: Text(l.themeSystem),
                    ),
                  ],
                  onChanged: (val) {
                    if (val != null) {
                      appState.setThemeMode(val);
                    }
                  },
                  isDark: isDark,
                ),
              ),
            ],
          ),

          // Notifications section
          _SettingsSection(
            title: l.profileNotificationsSection,
            isDark: isDark,
            children: [
              _SettingRow(
                label: l.profilePushNotifications,
                isDark: isDark,
                trailing: Switch(
                  value: _pushEnabled,
                  onChanged: (val) => setState(() => _pushEnabled = val),
                  activeTrackColor: AppColors.primaryOrange,
                ),
              ),
            ],
          ),

          // Other section
          _SettingsSection(
            title: l.profileOther,
            isDark: isDark,
            children: [
              _SettingRow(
                label: l.profileHelp,
                isDark: isDark,
                trailing: Icon(
                  Icons.arrow_forward_ios,
                  size: 14,
                  color: AppColors.lightSecondary,
                ),
                onTap: () {},
              ),
              _SettingRow(
                label: l.profilePrivacy,
                isDark: isDark,
                trailing: Icon(
                  Icons.arrow_forward_ios,
                  size: 14,
                  color: AppColors.lightSecondary,
                ),
                onTap: () {},
              ),
              _SettingRow(
                label: l.profileAbout,
                isDark: isDark,
                trailing: Icon(
                  Icons.arrow_forward_ios,
                  size: 14,
                  color: AppColors.lightSecondary,
                ),
                onTap: () {},
              ),
              _SettingRow(
                label: l.profileLogout,
                isDark: isDark,
                isDestructive: true,
                onTap: () async {
                  await AppStateScope.of(context).logout();
                  if (context.mounted) {
                    Navigator.pushNamedAndRemoveUntil(
                      context,
                      '/welcome',
                      (_) => false,
                    );
                  }
                },
              ),
            ],
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildDropdown<T>({
    required T value,
    required List<DropdownMenuItem<T>> items,
    required ValueChanged<T?> onChanged,
    required bool isDark,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkSurface : AppColors.lightSurface,
        borderRadius: BorderRadius.circular(7),
        border: Border.all(
          color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
        ),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          value: value,
          items: items,
          onChanged: onChanged,
          isDense: true,
          style: TextStyle(
            fontSize: 13,
            color: isDark ? AppColors.darkText : AppColors.lightText,
          ),
          dropdownColor: isDark ? AppColors.darkSurface : Colors.white,
          icon: Icon(
            Icons.arrow_drop_down,
            color: isDark ? AppColors.darkText : AppColors.lightText,
          ),
        ),
      ),
    );
  }
}

class _SettingsSection extends StatelessWidget {
  final String title;
  final bool isDark;
  final List<Widget> children;

  const _SettingsSection({
    required this.title,
    required this.isDark,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
            child: Text(
              title,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.5,
                color: AppColors.lightSecondary,
              ),
            ),
          ),
          ...children,
          const SizedBox(height: 4),
        ],
      ),
    );
  }
}

class _SettingRow extends StatelessWidget {
  final String label;
  final bool isDark;
  final Widget? trailing;
  final VoidCallback? onTap;
  final bool isDestructive;

  const _SettingRow({
    required this.label,
    required this.isDark,
    this.trailing,
    this.onTap,
    this.isDestructive = false,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 14,
                fontWeight: isDestructive ? FontWeight.w600 : FontWeight.normal,
                color: isDestructive
                    ? AppColors.primaryOrange
                    : (isDark ? AppColors.darkText : AppColors.lightText),
              ),
            ),
            trailing ?? const SizedBox.shrink(),
          ],
        ),
      ),
    );
  }
}
