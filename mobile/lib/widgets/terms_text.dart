import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state.dart';
import '../theme/app_colors.dart';

class TermsAndPrivacyText extends StatefulWidget {
  const TermsAndPrivacyText({super.key});

  @override
  State<TermsAndPrivacyText> createState() => _TermsAndPrivacyTextState();
}

class _TermsAndPrivacyTextState extends State<TermsAndPrivacyText> {
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
    _termsRecognizer.dispose();
    _privacyRecognizer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Text.rich(
      TextSpan(
        style: const TextStyle(fontSize: 11, color: AppColors.lightSecondary),
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
    );
  }
}
