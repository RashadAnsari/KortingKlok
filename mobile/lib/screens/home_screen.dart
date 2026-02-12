import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../models/product.dart';
import '../widgets/product_card.dart';
import '../widgets/store_chip.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _selectedFilter = 'all';

  List<Product> get _filteredProducts {
    if (_selectedFilter == 'all') return mockProducts;
    final store = {
      'ah': Store.ah,
      'jumbo': Store.jumbo,
      'lidl': Store.lidl,
    }[_selectedFilter];
    return mockProducts.where((p) => p.store == store).toList();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          l.homeTitle,
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: isDark ? AppColors.darkText : AppColors.darkBlue,
          ),
        ),
        const SizedBox(height: 14),
        // Filter chips
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              StoreFilterChip(
                label: l.homeAllStores,
                isActive: _selectedFilter == 'all',
                onTap: () => setState(() => _selectedFilter = 'all'),
              ),
              const SizedBox(width: 8),
              StoreFilterChip(
                label: 'Albert Heijn',
                isActive: _selectedFilter == 'ah',
                onTap: () => setState(() => _selectedFilter = 'ah'),
              ),
              const SizedBox(width: 8),
              StoreFilterChip(
                label: 'Jumbo',
                isActive: _selectedFilter == 'jumbo',
                onTap: () => setState(() => _selectedFilter = 'jumbo'),
              ),
              const SizedBox(width: 8),
              StoreFilterChip(
                label: 'Lidl',
                isActive: _selectedFilter == 'lidl',
                onTap: () => setState(() => _selectedFilter = 'lidl'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        // Product cards
        ..._filteredProducts.map(
          (product) => Padding(
            padding: const EdgeInsets.only(bottom: 14),
            child: ProductCard(
              product: product,
              ctaText: l.homeViewOffer,
              onTap: () => Navigator.pushNamed(
                context,
                '/product-detail',
                arguments: product,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
