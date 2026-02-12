import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../models/product.dart';

class StoreFilterChip extends StatelessWidget {
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  const StoreFilterChip({
    super.key,
    required this.label,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: isActive
              ? AppColors.primaryOrange
              : Theme.of(context).colorScheme.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isActive
                ? AppColors.primaryOrange
                : Theme.of(context).dividerColor,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: isActive
                ? Colors.white
                : Theme.of(
                    context,
                  ).colorScheme.onSurface.withValues(alpha: 0.7),
          ),
        ),
      ),
    );
  }
}

class StoreBadge extends StatelessWidget {
  final Store store;

  const StoreBadge({super.key, required this.store});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    String label;

    switch (store) {
      case Store.ah:
        bg = AppColors.ahBlue;
        fg = Colors.white;
        label = 'Albert Heijn';
      case Store.jumbo:
        bg = AppColors.jumboYellow;
        fg = Colors.black;
        label = 'Jumbo';
      case Store.lidl:
        bg = AppColors.lidlBlue;
        fg = AppColors.lidlYellow;
        label = 'Lidl';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(15),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: fg),
      ),
    );
  }
}

class StoreIcon extends StatelessWidget {
  final Store store;
  final double size;

  const StoreIcon({super.key, required this.store, this.size = 26});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    String text;

    switch (store) {
      case Store.ah:
        bg = AppColors.ahBlue;
        fg = Colors.white;
        text = 'AH';
      case Store.jumbo:
        bg = AppColors.jumboYellow;
        fg = Colors.black;
        text = 'JB';
      case Store.lidl:
        bg = AppColors.lidlBlue;
        fg = AppColors.lidlYellow;
        text = 'Lidl';
    }

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: bg,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.2),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Center(
        child: Text(
          text,
          style: TextStyle(
            color: fg,
            fontSize: size * 0.32,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}
