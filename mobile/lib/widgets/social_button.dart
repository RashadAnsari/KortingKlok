import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class SocialDivider extends StatelessWidget {
  final String text;

  const SocialDivider({super.key, required this.text});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
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

class SocialButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isApple;
  final bool isLoading;
  final VoidCallback onPressed;

  const SocialButton({
    super.key,
    required this.icon,
    required this.label,
    required this.onPressed,
    this.isApple = false,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final Color bg;
    final Color fg;
    final Color border;

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
