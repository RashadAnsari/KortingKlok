import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class EmptyState extends StatelessWidget {
  final IconData icon;
  final String message;

  const EmptyState({super.key, required this.icon, required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 56,
            color: AppColors.lightSecondary.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            message,
            style: const TextStyle(
              fontSize: 15,
              color: AppColors.lightSecondary,
            ),
          ),
        ],
      ),
    );
  }
}
