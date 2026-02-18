import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state.dart';
import '../services/auth_service.dart';
import '../theme/app_colors.dart';
import '../utils/firebase_error_mapper.dart';
import '../utils/validators.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _authService = AuthService();

  String _localeLabel(Locale? locale, AppLocalizations l) {
    return locale?.languageCode == 'en' ? l.langEnglish : l.langDutch;
  }

  String _themeModeLabel(ThemeMode mode, AppLocalizations l) {
    switch (mode) {
      case ThemeMode.light:
        return l.themeLight;
      case ThemeMode.dark:
        return l.themeDark;
      case ThemeMode.system:
        return l.themeSystem;
    }
  }

  Future<void> _openUrl(String url) async {
    final uri = Uri.parse(url);
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  void _showChangeNameSheet(
    BuildContext context,
    AppLocalizations l,
    bool isDark,
  ) {
    final ctrl = TextEditingController(
      text: AppState.of(context).userName ?? '',
    );
    bool loading = false;
    String? error;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: isDark ? AppColors.darkSurface : Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => StatefulBuilder(
        builder: (ctx, setS) => Padding(
          padding: EdgeInsets.fromLTRB(
            20,
            24,
            20,
            MediaQuery.of(ctx).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _SheetTitle(text: l.profileChangeName, isDark: isDark),
              const SizedBox(height: 16),
              _SheetLabel(text: l.registerDisplayName, isDark: isDark),
              const SizedBox(height: 5),
              TextField(
                controller: ctrl,
                decoration: InputDecoration(
                  hintText: l.registerDisplayNameHint,
                ),
                enabled: !loading,
                textInputAction: TextInputAction.done,
              ),
              if (error != null) ...[
                const SizedBox(height: 8),
                Text(
                  error!,
                  style: const TextStyle(color: Colors.red, fontSize: 13),
                ),
              ],
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: loading
                      ? null
                      : () async {
                          final name = ctrl.text.trim();
                          if (name.isEmpty) return;
                          setS(() {
                            loading = true;
                            error = null;
                          });
                          try {
                            await _authService.updateDisplayName(name);
                            if (ctx.mounted) Navigator.pop(ctx);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text(l.profileNameUpdated)),
                              );
                            }
                          } catch (e) {
                            setS(() {
                              loading = false;
                              error = mapFirebaseError(e, l, isReauth: true);
                            });
                          }
                        },
                  child: loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(l.profileSave),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showChangeEmailSheet(
    BuildContext context,
    AppLocalizations l,
    bool isDark,
  ) {
    final emailCtrl = TextEditingController();
    final passwordCtrl = TextEditingController();
    bool loading = false;
    String? error;
    bool obscure = true;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: isDark ? AppColors.darkSurface : Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => StatefulBuilder(
        builder: (ctx, setS) => Padding(
          padding: EdgeInsets.fromLTRB(
            20,
            24,
            20,
            MediaQuery.of(ctx).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _SheetTitle(text: l.profileChangeEmail, isDark: isDark),
              const SizedBox(height: 16),
              _SheetLabel(text: l.profileNewEmailLabel, isDark: isDark),
              const SizedBox(height: 5),
              TextField(
                controller: emailCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(hintText: l.profileNewEmailHint),
                enabled: !loading,
                textInputAction: TextInputAction.next,
              ),
              const SizedBox(height: 12),
              _SheetLabel(text: l.profileCurrentPasswordLabel, isDark: isDark),
              const SizedBox(height: 5),
              TextField(
                controller: passwordCtrl,
                obscureText: obscure,
                decoration: InputDecoration(
                  hintText: l.loginPasswordHint,
                  suffixIcon: IconButton(
                    icon: Icon(
                      obscure ? Icons.visibility_off : Icons.visibility,
                      size: 20,
                      color: AppColors.lightSecondary,
                    ),
                    onPressed: () => setS(() => obscure = !obscure),
                  ),
                ),
                enabled: !loading,
                textInputAction: TextInputAction.done,
              ),
              if (error != null) ...[
                const SizedBox(height: 8),
                Text(
                  error!,
                  style: const TextStyle(color: Colors.red, fontSize: 13),
                ),
              ],
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: loading
                      ? null
                      : () async {
                          final email = emailCtrl.text.trim();
                          if (email.isEmpty || passwordCtrl.text.isEmpty) {
                            return;
                          }
                          if (!isValidEmail(email)) {
                            setS(() => error = l.validationEmailInvalid);
                            return;
                          }
                          setS(() {
                            loading = true;
                            error = null;
                          });
                          try {
                            await _authService.changeEmail(
                              passwordCtrl.text,
                              email,
                            );
                            if (ctx.mounted) Navigator.pop(ctx);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(l.profileEmailVerifySent),
                                  duration: const Duration(seconds: 5),
                                ),
                              );
                            }
                          } catch (e) {
                            setS(() {
                              loading = false;
                              error = mapFirebaseError(e, l, isReauth: true);
                            });
                          }
                        },
                  child: loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(l.profileSave),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showChangePasswordSheet(
    BuildContext context,
    AppLocalizations l,
    bool isDark,
  ) {
    final currentCtrl = TextEditingController();
    final newCtrl = TextEditingController();
    bool loading = false;
    String? error;
    bool obscureCurrent = true;
    bool obscureNew = true;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: isDark ? AppColors.darkSurface : Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => StatefulBuilder(
        builder: (ctx, setS) => Padding(
          padding: EdgeInsets.fromLTRB(
            20,
            24,
            20,
            MediaQuery.of(ctx).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _SheetTitle(text: l.profileChangePassword, isDark: isDark),
              const SizedBox(height: 16),
              _SheetLabel(text: l.profileCurrentPasswordLabel, isDark: isDark),
              const SizedBox(height: 5),
              TextField(
                controller: currentCtrl,
                obscureText: obscureCurrent,
                decoration: InputDecoration(
                  hintText: l.loginPasswordHint,
                  suffixIcon: IconButton(
                    icon: Icon(
                      obscureCurrent ? Icons.visibility_off : Icons.visibility,
                      size: 20,
                      color: AppColors.lightSecondary,
                    ),
                    onPressed: () =>
                        setS(() => obscureCurrent = !obscureCurrent),
                  ),
                ),
                enabled: !loading,
                textInputAction: TextInputAction.next,
              ),
              const SizedBox(height: 12),
              _SheetLabel(text: l.profileNewPasswordLabel, isDark: isDark),
              const SizedBox(height: 5),
              TextField(
                controller: newCtrl,
                obscureText: obscureNew,
                decoration: InputDecoration(
                  hintText: l.loginPasswordHint,
                  suffixIcon: IconButton(
                    icon: Icon(
                      obscureNew ? Icons.visibility_off : Icons.visibility,
                      size: 20,
                      color: AppColors.lightSecondary,
                    ),
                    onPressed: () => setS(() => obscureNew = !obscureNew),
                  ),
                ),
                enabled: !loading,
                textInputAction: TextInputAction.done,
              ),
              if (error != null) ...[
                const SizedBox(height: 8),
                Text(
                  error!,
                  style: const TextStyle(color: Colors.red, fontSize: 13),
                ),
              ],
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: loading
                      ? null
                      : () async {
                          if (currentCtrl.text.isEmpty ||
                              newCtrl.text.isEmpty) {
                            return;
                          }
                          if (newCtrl.text.length < 6) {
                            setS(() => error = l.validationPasswordMin);
                            return;
                          }
                          setS(() {
                            loading = true;
                            error = null;
                          });
                          try {
                            await _authService.changePassword(
                              currentCtrl.text,
                              newCtrl.text,
                            );
                            if (ctx.mounted) Navigator.pop(ctx);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(l.profilePasswordUpdated),
                                ),
                              );
                            }
                          } catch (e) {
                            setS(() {
                              loading = false;
                              error = mapFirebaseError(e, l, isReauth: true);
                            });
                          }
                        },
                  child: loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(l.profileSave),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showLanguageSheet(
    BuildContext context,
    AppLocalizations l,
    bool isDark,
    AppStateScopeState appState,
  ) {
    final current = appState.userLocale?.languageCode ?? 'nl';

    showModalBottomSheet(
      context: context,
      backgroundColor: isDark ? AppColors.darkSurface : Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
            child: _SheetTitle(text: l.profileLanguage, isDark: isDark),
          ),
          Divider(
            height: 1,
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
          _SheetOption(
            label: l.langDutch,
            selected: current == 'nl',
            isDark: isDark,
            onTap: () {
              appState.setLocale(const Locale('nl'));
              Navigator.pop(context);
            },
          ),
          _SheetOption(
            label: l.langEnglish,
            selected: current == 'en',
            isDark: isDark,
            onTap: () {
              appState.setLocale(const Locale('en'));
              Navigator.pop(context);
            },
          ),
          const SizedBox(height: 12),
        ],
      ),
    );
  }

  void _showThemeSheet(
    BuildContext context,
    AppLocalizations l,
    bool isDark,
    AppStateScopeState appState,
    ThemeMode current,
  ) {
    showModalBottomSheet(
      context: context,
      backgroundColor: isDark ? AppColors.darkSurface : Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
            child: _SheetTitle(text: l.profileTheme, isDark: isDark),
          ),
          Divider(
            height: 1,
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
          _SheetOption(
            label: l.themeSystem,
            selected: current == ThemeMode.system,
            isDark: isDark,
            onTap: () {
              appState.setThemeMode(ThemeMode.system);
              Navigator.pop(context);
            },
          ),
          _SheetOption(
            label: l.themeLight,
            selected: current == ThemeMode.light,
            isDark: isDark,
            onTap: () {
              appState.setThemeMode(ThemeMode.light);
              Navigator.pop(context);
            },
          ),
          _SheetOption(
            label: l.themeDark,
            selected: current == ThemeMode.dark,
            isDark: isDark,
            onTap: () {
              appState.setThemeMode(ThemeMode.dark);
              Navigator.pop(context);
            },
          ),
          const SizedBox(height: 12),
        ],
      ),
    );
  }

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
                  AppState.of(context).userName ?? '',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                    color: isDark ? AppColors.darkText : AppColors.darkBlue,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  AppState.of(context).userEmail ?? '',
                  style: TextStyle(
                    fontSize: 14,
                    color: isDark ? AppColors.darkSecondary : AppColors.midGray,
                  ),
                ),
              ],
            ),
          ),

          _SettingsSection(
            title: l.profileAccount,
            isDark: isDark,
            children: [
              _SettingRow(
                label: l.profileChangeName,
                isDark: isDark,
                trailing: _Chevron(),
                onTap: () => _showChangeNameSheet(context, l, isDark),
              ),
              _SettingRow(
                label: l.profileChangeEmail,
                isDark: isDark,
                trailing: _Chevron(),
                onTap: () => _showChangeEmailSheet(context, l, isDark),
              ),
              _SettingRow(
                label: l.profileChangePassword,
                isDark: isDark,
                trailing: _Chevron(),
                onTap: () => _showChangePasswordSheet(context, l, isDark),
              ),
            ],
          ),

          _SettingsSection(
            title: l.profilePreferences,
            isDark: isDark,
            children: [
              _SettingRow(
                label: l.profileLanguage,
                isDark: isDark,
                trailing: _ValueChevron(value: _localeLabel(currentLocale, l)),
                onTap: () => _showLanguageSheet(context, l, isDark, appState),
              ),
              _SettingRow(
                label: l.profileTheme,
                isDark: isDark,
                trailing: _ValueChevron(
                  value: _themeModeLabel(currentTheme, l),
                ),
                onTap: () =>
                    _showThemeSheet(context, l, isDark, appState, currentTheme),
              ),
            ],
          ),

          _SettingsSection(
            title: l.profileOther,
            isDark: isDark,
            children: [
              _SettingRow(
                label: l.profileHelp,
                isDark: isDark,
                trailing: _Chevron(),
                onTap: () {
                  _openUrl('mailto:hallo@kortingklok.nl');
                },
              ),
              _SettingRow(
                label: l.profilePrivacy,
                isDark: isDark,
                trailing: _Chevron(),
                onTap: () {
                  final lang = AppState.of(context).locale.languageCode;
                  final url = lang == 'en'
                      ? 'https://kortingklok.nl/en/privacy'
                      : 'https://kortingklok.nl/privacy';
                  _openUrl(url);
                },
              ),
              _SettingRow(
                label: l.profileAbout,
                isDark: isDark,
                trailing: _Chevron(),
                onTap: () {
                  final lang = AppState.of(context).locale.languageCode;
                  final url = lang == 'en'
                      ? 'https://kortingklok.nl/en'
                      : 'https://kortingklok.nl';
                  _openUrl(url);
                },
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
}

class _SheetTitle extends StatelessWidget {
  final String text;
  final bool isDark;

  const _SheetTitle({required this.text, required this.isDark});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 17,
        fontWeight: FontWeight.w700,
        color: isDark ? AppColors.darkText : AppColors.darkBlue,
      ),
    );
  }
}

class _SheetLabel extends StatelessWidget {
  final String text;
  final bool isDark;

  const _SheetLabel({required this.text, required this.isDark});

  @override
  Widget build(BuildContext context) {
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

class _SheetOption extends StatelessWidget {
  final String label;
  final bool selected;
  final bool isDark;
  final VoidCallback onTap;

  const _SheetOption({
    required this.label,
    required this.selected,
    required this.isDark,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 15,
                fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
                color: selected
                    ? AppColors.primaryOrange
                    : (isDark ? AppColors.darkText : AppColors.lightText),
              ),
            ),
            if (selected)
              const Icon(Icons.check, color: AppColors.primaryOrange, size: 18),
          ],
        ),
      ),
    );
  }
}

class _Chevron extends StatelessWidget {
  const _Chevron();

  @override
  Widget build(BuildContext context) {
    return const Icon(
      Icons.arrow_forward_ios,
      size: 14,
      color: AppColors.lightSecondary,
    );
  }
}

class _ValueChevron extends StatelessWidget {
  final String value;

  const _ValueChevron({required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: const TextStyle(fontSize: 13, color: AppColors.lightSecondary),
        ),
        const SizedBox(width: 6),
        const Icon(
          Icons.arrow_forward_ios,
          size: 14,
          color: AppColors.lightSecondary,
        ),
      ],
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
