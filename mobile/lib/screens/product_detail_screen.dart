import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../models/product.dart';
import '../widgets/store_chip.dart';

class ProductDetailScreen extends StatelessWidget {
  const ProductDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final product = ModalRoute.of(context)!.settings.arguments as Product;
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          l.detailBack,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: isDark ? AppColors.primaryOrange : AppColors.darkBlue,
          ),
        ),
        titleSpacing: 0,
        actions: [
          IconButton(
            icon: Icon(
              Icons.ios_share,
              color: isDark ? AppColors.darkSecondary : const Color(0xFF666666),
            ),
            onPressed: () {},
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(
            height: 1,
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
        ),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Large product image
            Container(
              width: double.infinity,
              height: 200,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: isDark
                      ? [AppColors.darkBorder, AppColors.darkSurface]
                      : [const Color(0xFFF5F5F5), const Color(0xFFE0E0E0)],
                ),
              ),
              child: Center(
                child: Text(
                  product.emoji,
                  style: const TextStyle(fontSize: 70),
                ),
              ),
            ),
            // Product info
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: isDark ? AppColors.darkText : AppColors.darkBlue,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    product.category,
                    style: const TextStyle(
                      fontSize: 14,
                      color: AppColors.lightSecondary,
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Prices
                  Row(
                    children: [
                      Text(
                        '\u20ac${product.oldPrice.toStringAsFixed(2)}',
                        style: const TextStyle(
                          fontSize: 17,
                          color: AppColors.lightSecondary,
                          decoration: TextDecoration.lineThrough,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        '\u20ac${product.newPrice.toStringAsFixed(2)}',
                        style: const TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.w700,
                          color: AppColors.primaryOrange,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Badges
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: isDark
                              ? AppColors.badgeBgDark
                              : AppColors.badgeBgLight,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Text(
                          product.badgeText,
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: AppColors.primaryOrange,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.primaryOrange,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Text(
                          '-${product.discountPercent}%',
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  // Store info box
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: isDark
                          ? AppColors.darkSurface
                          : AppColors.lightSurface,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          l.detailOnSaleAt,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: isDark
                                ? AppColors.darkSecondary
                                : const Color(0xFF666666),
                          ),
                        ),
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            StoreIcon(store: product.store, size: 22),
                            const SizedBox(width: 8),
                            Text(
                              product.storeLabel,
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: isDark
                                    ? AppColors.primaryOrange
                                    : AppColors.darkBlue,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  // CTA
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {},
                      child: Text(l.detailViewAt(product.storeLabel)),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: 0,
        onTap: (_) {},
        items: [
          BottomNavigationBarItem(
            icon: const Icon(Icons.home),
            label: l.navHome,
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.search),
            label: l.navSearch,
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.person),
            label: l.navProfile,
          ),
        ],
      ),
    );
  }
}
