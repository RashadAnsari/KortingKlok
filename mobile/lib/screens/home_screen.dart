import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../models/api_product.dart';
import '../models/supermarket.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../widgets/api_product_card.dart';
import '../widgets/error_view.dart';
import '../widgets/store_chip.dart';
import 'api_product_detail_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = ApiService();

  List<Supermarket> _supermarkets = [];
  List<ApiProduct> _products = [];
  int? _selectedSupermarketIndex;
  bool _loadingSupermarkets = true;
  bool _loadingProducts = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSupermarkets();
  }

  Future<void> _loadSupermarkets() async {
    setState(() {
      _loadingSupermarkets = true;
      _error = null;
    });
    try {
      final data = await _api.get('/products/supermarkets');
      final list = (data as List).map((e) => Supermarket.fromJson(e)).toList();
      if (mounted) {
        setState(() {
          _supermarkets = list;
          _loadingSupermarkets = false;
        });
        _loadProducts();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loadingSupermarkets = false;
          _error = 'supermarkets';
        });
      }
    }
  }

  Future<void> _loadProducts() async {
    setState(() {
      _loadingProducts = true;
      _error = null;
    });
    try {
      final params = <String, String?>{};
      if (_selectedSupermarketIndex != null) {
        params['supermarket'] = _supermarkets[_selectedSupermarketIndex!].id
            .toString();
      }
      final data = await _api.get('/products/deals', params: params);
      final results = (data['results'] as List)
          .map((e) => ApiProduct.fromJson(e))
          .toList();
      if (mounted) {
        setState(() {
          _products = results;
          _loadingProducts = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loadingProducts = false;
          _error = 'products';
        });
      }
    }
  }

  void _selectFilter(int? index) {
    if (index == _selectedSupermarketIndex) return;
    setState(() => _selectedSupermarketIndex = index);
    _loadProducts();
  }

  void _openProductDetail(ApiProduct product) {
    final supermarket = _supermarkets
        .where((s) => s.id == product.supermarketId)
        .firstOrNull;
    Navigator.pushNamed(
      context,
      '/api-product-detail',
      arguments: ApiProductDetailArgs(
        product: product,
        supermarketName: supermarket?.name ?? '',
        supermarketLogoUrl: supermarket?.logoUrl,
      ),
    ).then((result) {
      if (result is bool && result != product.isTracked && mounted) {
        if (!result) {
          setState(() {
            _products.removeWhere((p) => p.id == product.id);
          });
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    if (_loadingSupermarkets) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null && _supermarkets.isEmpty) {
      return ErrorView(onRetry: _loadSupermarkets);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: Text(
            l.homeTitle,
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: isDark ? AppColors.darkText : AppColors.darkBlue,
            ),
          ),
        ),
        const SizedBox(height: 14),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                StoreFilterChip(
                  label: l.homeAllStores,
                  isActive: _selectedSupermarketIndex == null,
                  onTap: () => _selectFilter(null),
                ),
                ..._supermarkets.asMap().entries.map(
                  (e) => Padding(
                    padding: const EdgeInsets.only(left: 8),
                    child: StoreFilterChip(
                      label: e.value.name,
                      isActive: _selectedSupermarketIndex == e.key,
                      onTap: () => _selectFilter(e.key),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: _loadingProducts
              ? const Center(child: CircularProgressIndicator())
              : _error != null
              ? ErrorView(onRetry: _loadProducts)
              : _products.isEmpty
              ? const _EmptyView()
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _products.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 14),
                  itemBuilder: (_, i) => ApiProductCard(
                    product: _products[i],
                    onTap: () => _openProductDetail(_products[i]),
                  ),
                ),
        ),
      ],
    );
  }
}

class _EmptyView extends StatelessWidget {
  const _EmptyView();

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: isDark
                    ? AppColors.primaryOrange.withValues(alpha: 0.15)
                    : AppColors.primaryOrange.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.bookmark_outline_rounded,
                size: 28,
                color: AppColors.primaryOrange,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              l.homeEmptyTitle,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: isDark ? AppColors.darkText : AppColors.darkBlue,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              l.homeEmptySubtitle,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.lightSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
