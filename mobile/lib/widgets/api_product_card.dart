import 'package:flutter/material.dart';

import '../models/api_product.dart';
import '../theme/app_colors.dart';

class ApiProductCard extends StatelessWidget {
  final ApiProduct product;
  final VoidCallback? onTap;

  const ApiProductCard({super.key, required this.product, this.onTap});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return GestureDetector(
      onTap: onTap,
      child: Container(
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
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: SizedBox(
                width: double.infinity,
                height: 105,
                child: product.imageUrl != null
                    ? Image.network(
                        product.imageUrl!,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => _Placeholder(isDark: isDark),
                      )
                    : _Placeholder(isDark: isDark),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              product.name,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Theme.of(context).colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 8),
            if (product.currentPrice != null)
              Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  if (product.basePrice != null &&
                      product.basePrice != product.currentPrice) ...[
                    Text(
                      '€${product.basePrice}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.lightSecondary,
                        decoration: TextDecoration.lineThrough,
                      ),
                    ),
                    const SizedBox(width: 6),
                  ],
                  Text(
                    '€${product.currentPrice}',
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primaryOrange,
                    ),
                  ),
                ],
              ),
            if (product.discountText != null) ...[
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppColors.primaryOrange,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  product.discountText!,
                  style: const TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _Placeholder extends StatelessWidget {
  final bool isDark;

  const _Placeholder({required this.isDark});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isDark
              ? [AppColors.darkBorder, AppColors.darkSurface]
              : [const Color(0xFFF5F5F5), const Color(0xFFE0E0E0)],
        ),
      ),
      child: const Center(
        child: Icon(
          Icons.shopping_basket_outlined,
          size: 36,
          color: AppColors.lightSecondary,
        ),
      ),
    );
  }
}
