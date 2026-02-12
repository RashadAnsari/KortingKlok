import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class KKLogo extends StatelessWidget {
  final double size;

  const KKLogo({super.key, this.size = 80});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final asset = isDark
        ? 'assets/images/logo-dark.svg'
        : 'assets/images/logo.svg';

    return SvgPicture.asset(asset, width: size, height: size);
  }
}
