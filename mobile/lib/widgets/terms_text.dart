import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
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
    _termsRecognizer = _openPage('terms');
    _privacyRecognizer = _openPage('privacy');
  }

  TapGestureRecognizer _openPage(String path) {
    return TapGestureRecognizer()
      ..onTap = () {
        final lang = AppState.of(context).locale.languageCode;
        final url = AppConfig.pageUrl(path, lang);
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
          _link(l.registerTermsLink, _termsRecognizer),
          TextSpan(text: l.registerTermsAnd),
          _link(l.registerPrivacyLink, _privacyRecognizer),
          const TextSpan(text: '.'),
        ],
      ),
      textAlign: TextAlign.center,
    );
  }

  /// Renders as a tappable link when a website is configured, and as plain
  /// text otherwise, so a build without WEBSITE_URL has no dead links.
  TextSpan _link(String text, TapGestureRecognizer recognizer) {
    if (!AppConfig.hasWebsite) return TextSpan(text: text);
    return TextSpan(
      text: text,
      style: const TextStyle(
        color: AppColors.primaryOrange,
        decoration: TextDecoration.underline,
        decorationColor: AppColors.primaryOrange,
      ),
      recognizer: recognizer,
    );
  }
}
