import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../models/product.dart';
import 'store_chip.dart';

class ProductCard extends StatelessWidget {
  final Product product;
  final String ctaText;
  final VoidCallback onTap;

  const ProductCard({
    super.key,
    required this.product,
    required this.ctaText,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(10),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.09),
            blurRadius: 7,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Product image with store icon
          Stack(
            children: [
              Container(
                width: double.infinity,
                height: 105,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: isDark
                        ? [AppColors.darkBorder, AppColors.darkSurface]
                        : [const Color(0xFFF5F5F5), const Color(0xFFE0E0E0)],
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Center(
                  child: Text(
                    product.emoji,
                    style: const TextStyle(fontSize: 36),
                  ),
                ),
              ),
              Positioned(
                top: 8,
                left: 8,
                child: StoreIcon(store: product.store),
              ),
            ],
          ),
          const SizedBox(height: 10),
          // Product name
          Text(
            product.name,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: Theme.of(context).colorScheme.onSurface,
            ),
          ),
          const SizedBox(height: 3),
          // Category
          Text(
            product.category,
            style: const TextStyle(
              fontSize: 11,
              color: AppColors.lightSecondary,
            ),
          ),
          const SizedBox(height: 8),
          // Price row
          Row(
            children: [
              Text(
                '\u20ac${product.oldPrice.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.lightSecondary,
                  decoration: TextDecoration.lineThrough,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                '\u20ac${product.newPrice.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: AppColors.primaryOrange,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Badges
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: isDark
                      ? AppColors.badgeBgDark
                      : AppColors.badgeBgLight,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  product.badgeText,
                  style: const TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w600,
                    color: AppColors.primaryOrange,
                  ),
                ),
              ),
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppColors.primaryOrange,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  '-${product.discountPercent}%',
                  style: const TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          // CTA button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(onPressed: onTap, child: Text(ctaText)),
          ),
        ],
      ),
    );
  }
}
