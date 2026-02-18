import 'dart:async';

import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../models/api_product.dart';
import '../models/category.dart';
import '../models/supermarket.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../widgets/api_product_card.dart';
import '../widgets/empty_state.dart';
import '../widgets/error_view.dart';
import 'api_product_detail_screen.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _api = ApiService();
  final _searchController = TextEditingController();
  Timer? _debounce;

  List<Supermarket> _supermarkets = [];
  int _selectedIndex = 0;

  List<Category> _categories = [];
  List<Category> _categoryBreadcrumb = [];
  List<ApiProduct> _searchResults = [];
  bool _viewingCategoryProducts = false;

  bool _loadingSupermarkets = true;
  bool _loadingContent = false;
  String? _error;

  bool get _isSearching => _searchController.text.trim().isNotEmpty;
  Supermarket? get _currentSupermarket =>
      _supermarkets.isEmpty ? null : _supermarkets[_selectedIndex];

  @override
  void initState() {
    super.initState();
    _loadSupermarkets();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  Future<void> _loadSupermarkets() async {
    setState(() {
      _loadingSupermarkets = true;
      _error = null;
    });
    try {
      final data = await _api.get('/products/supermarkets') as List<dynamic>;
      final supermarkets = data
          .map((e) => Supermarket.fromJson(e as Map<String, dynamic>))
          .toList();
      if (mounted) {
        setState(() {
          _supermarkets = supermarkets;
          _loadingSupermarkets = false;
        });
        if (supermarkets.isNotEmpty) {
          _loadCategories(supermarkets[0].id);
        }
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loadingSupermarkets = false;
          _error = 'error';
        });
      }
    }
  }

  Future<void> _loadCategories(int supermarketId, {int? parentId}) async {
    setState(() {
      _loadingContent = true;
      _categories = [];
      _error = null;
      _viewingCategoryProducts = false;
    });
    try {
      final params = <String, String?>{'supermarket': supermarketId.toString()};
      if (parentId != null) {
        params['parent'] = parentId.toString();
      }
      final data =
          await _api.get('/products/categories', params: params)
              as List<dynamic>;
      if (mounted) {
        setState(() {
          _categories = data
              .map((e) => Category.fromJson(e as Map<String, dynamic>))
              .toList();
          _loadingContent = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loadingContent = false;
          _error = 'error';
        });
      }
    }
  }

  Future<void> _onCategoryTapped(Category cat) async {
    setState(() {
      _loadingContent = true;
      _error = null;
    });
    try {
      final data =
          await _api.get(
                '/products/categories',
                params: {
                  'supermarket': _currentSupermarket?.id.toString(),
                  'parent': cat.id.toString(),
                },
              )
              as List<dynamic>;
      if (!mounted) return;
      final subcats = data
          .map((e) => Category.fromJson(e as Map<String, dynamic>))
          .toList();
      if (subcats.isNotEmpty) {
        setState(() {
          _categoryBreadcrumb = [..._categoryBreadcrumb, cat];
          _categories = subcats;
          _loadingContent = false;
        });
      } else {
        await _loadCategoryProducts(cat);
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loadingContent = false;
          _error = 'error';
        });
      }
    }
  }

  Future<void> _loadCategoryProducts(Category cat) async {
    try {
      final data =
          await _api.get(
                '/products/search',
                params: {
                  'supermarket': _currentSupermarket?.id.toString(),
                  'category': cat.id.toString(),
                },
              )
              as Map<String, dynamic>;
      if (mounted) {
        final results = (data['results'] as List<dynamic>)
            .map((e) => ApiProduct.fromJson(e as Map<String, dynamic>))
            .toList();
        setState(() {
          _categoryBreadcrumb = [..._categoryBreadcrumb, cat];
          _searchResults = results;
          _viewingCategoryProducts = true;
          _loadingContent = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loadingContent = false;
          _error = 'error';
        });
      }
    }
  }

  void _onCategoryBack() {
    final newBreadcrumb = [..._categoryBreadcrumb]..removeLast();
    if (_viewingCategoryProducts) {
      setState(() {
        _viewingCategoryProducts = false;
        _searchResults = [];
        _categoryBreadcrumb = newBreadcrumb;
      });
    } else {
      setState(() => _categoryBreadcrumb = newBreadcrumb);
      final parentId = newBreadcrumb.isEmpty ? null : newBreadcrumb.last.id;
      _loadCategories(_currentSupermarket!.id, parentId: parentId);
    }
  }

  Future<void> _search(String query) async {
    if (query.trim().isEmpty) {
      setState(() {
        _searchResults = [];
        _categoryBreadcrumb = [];
        _viewingCategoryProducts = false;
      });
      if (_currentSupermarket != null) {
        _loadCategories(_currentSupermarket!.id);
      }
      return;
    }
    setState(() {
      _loadingContent = true;
      _error = null;
    });
    try {
      final data =
          await _api.get(
                '/products/search',
                params: {
                  'q': query.trim(),
                  'supermarket': _currentSupermarket?.id.toString(),
                },
              )
              as Map<String, dynamic>;
      if (mounted) {
        final results = (data['results'] as List<dynamic>)
            .map((e) => ApiProduct.fromJson(e as Map<String, dynamic>))
            .toList();
        setState(() {
          _searchResults = results;
          _loadingContent = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loadingContent = false;
          _error = 'error';
        });
      }
    }
  }

  void _onSearchChanged(String value) {
    setState(() {});
    if (_debounce?.isActive ?? false) _debounce!.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), () => _search(value));
  }

  void _openProductDetail(ApiProduct product) {
    Navigator.pushNamed(
      context,
      '/api-product-detail',
      arguments: ApiProductDetailArgs(
        product: product,
        supermarketName: _currentSupermarket?.name ?? '',
        supermarketLogoUrl: _currentSupermarket?.logoUrl,
      ),
    ).then((result) {
      if (result is bool && result != product.isTracked && mounted) {
        setState(() {
          final i = _searchResults.indexWhere((p) => p.id == product.id);
          if (i != -1) {
            final old = _searchResults[i];
            _searchResults[i] = ApiProduct(
              id: old.id,
              name: old.name,
              supermarketId: old.supermarketId,
              category: old.category,
              basePrice: old.basePrice,
              currentPrice: old.currentPrice,
              hasDiscount: old.hasDiscount,
              discountText: old.discountText,
              imageUrl: old.imageUrl,
              websiteUrl: old.websiteUrl,
              isTracked: result,
            );
          }
        });
      }
    });
  }

  void _onStoreSelected(int index) {
    if (index == _selectedIndex) return;
    setState(() {
      _selectedIndex = index;
      _searchResults = [];
      _categoryBreadcrumb = [];
      _viewingCategoryProducts = false;
    });
    if (_searchController.text.trim().isNotEmpty) {
      _search(_searchController.text);
    } else {
      _loadCategories(_supermarkets[index].id);
    }
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

    final storeName = _currentSupermarket?.name ?? '';

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: l.searchPlaceholder(storeName),
              prefixIcon: const Icon(Icons.search, size: 20),
              suffixIcon: _isSearching
                  ? IconButton(
                      icon: const Icon(Icons.clear, size: 20),
                      onPressed: () {
                        _searchController.clear();
                        _onSearchChanged('');
                      },
                    )
                  : null,
            ),
            onChanged: _onSearchChanged,
          ),
        ),
        const SizedBox(height: 16),
        if (_supermarkets.isNotEmpty)
          _StoreTabs(
            supermarkets: _supermarkets,
            selectedIndex: _selectedIndex,
            onSelected: _onStoreSelected,
            isDark: isDark,
          ),
        Expanded(
          child: GestureDetector(
            onHorizontalDragEnd:
                _categoryBreadcrumb.isNotEmpty && !_loadingContent
                ? (details) {
                    if ((details.primaryVelocity ?? 0) > 200) {
                      _onCategoryBack();
                    }
                  }
                : null,
            child: _loadingContent
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                ? ErrorView(
                    onRetry: () {
                      if (_isSearching) {
                        _search(_searchController.text);
                      } else if (_currentSupermarket != null) {
                        _loadCategories(_currentSupermarket!.id);
                      }
                    },
                  )
                : _isSearching
                ? _SearchResultsList(
                    products: _searchResults,
                    onProductTapped: _openProductDetail,
                    isDark: isDark,
                    l: l,
                  )
                : _viewingCategoryProducts
                ? _CategoryProductsView(
                    products: _searchResults,
                    categoryName: _categoryBreadcrumb.last.name,
                    onBack: _onCategoryBack,
                    onProductTapped: _openProductDetail,
                    isDark: isDark,
                    l: l,
                  )
                : _CategoryList(
                    categories: _categories,
                    breadcrumb: _categoryBreadcrumb,
                    storeName: storeName,
                    onBack: _categoryBreadcrumb.isEmpty
                        ? null
                        : _onCategoryBack,
                    onCategoryTapped: _onCategoryTapped,
                    isDark: isDark,
                    l: l,
                  ),
          ),
        ),
      ],
    );
  }
}

class _StoreTabs extends StatelessWidget {
  final List<Supermarket> supermarkets;
  final int selectedIndex;
  final ValueChanged<int> onSelected;
  final bool isDark;

  const _StoreTabs({
    required this.supermarkets,
    required this.selectedIndex,
    required this.onSelected,
    required this.isDark,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
            width: 2,
          ),
        ),
      ),
      child: Row(
        children: List.generate(supermarkets.length, (i) {
          final isActive = selectedIndex == i;
          return Expanded(
            child: GestureDetector(
              onTap: () => onSelected(i),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(
                      color: isActive
                          ? AppColors.primaryOrange
                          : Colors.transparent,
                      width: 3,
                    ),
                  ),
                ),
                child: Text(
                  supermarkets[i].name,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: isActive
                        ? AppColors.primaryOrange
                        : (isDark
                              ? AppColors.darkSecondary
                              : AppColors.midGray),
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}

class _CategoryList extends StatelessWidget {
  final List<Category> categories;
  final List<Category> breadcrumb;
  final String storeName;
  final VoidCallback? onBack;
  final ValueChanged<Category> onCategoryTapped;
  final bool isDark;
  final AppLocalizations l;

  const _CategoryList({
    required this.categories,
    required this.breadcrumb,
    required this.storeName,
    required this.onBack,
    required this.onCategoryTapped,
    required this.isDark,
    required this.l,
  });

  @override
  Widget build(BuildContext context) {
    if (categories.isEmpty) {
      return EmptyState(
        icon: Icons.category_outlined,
        message: l.searchNoCategories,
      );
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (onBack != null)
          _BackHeader(
            title: breadcrumb.last.name,
            onBack: onBack!,
            isDark: isDark,
          )
        else
          Text(
            l.searchCategoriesTitle(storeName),
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w600,
              color: isDark ? AppColors.darkText : AppColors.darkBlue,
            ),
          ),
        const SizedBox(height: 14),
        ...categories.map(
          (cat) => _CategoryItem(
            name: cat.name,
            isDark: isDark,
            onTap: () => onCategoryTapped(cat),
          ),
        ),
      ],
    );
  }
}

class _BackHeader extends StatelessWidget {
  final String title;
  final VoidCallback onBack;
  final bool isDark;

  const _BackHeader({
    required this.title,
    required this.onBack,
    required this.isDark,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onBack,
      child: Row(
        children: [
          Icon(Icons.arrow_back_ios, size: 16, color: AppColors.primaryOrange),
          const SizedBox(width: 4),
          Text(
            title,
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w600,
              color: isDark ? AppColors.darkText : AppColors.darkBlue,
            ),
          ),
        ],
      ),
    );
  }
}

class _CategoryItem extends StatelessWidget {
  final String name;
  final bool isDark;
  final VoidCallback onTap;

  const _CategoryItem({
    required this.name,
    required this.isDark,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: isDark ? AppColors.darkSurface : AppColors.lightSurface,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                name,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: isDark ? AppColors.darkText : AppColors.lightText,
                ),
              ),
              Icon(
                Icons.arrow_forward_ios,
                size: 14,
                color: isDark
                    ? AppColors.darkSecondary
                    : AppColors.lightSecondary,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CategoryProductsView extends StatelessWidget {
  final List<ApiProduct> products;
  final String categoryName;
  final VoidCallback onBack;
  final ValueChanged<ApiProduct>? onProductTapped;
  final bool isDark;
  final AppLocalizations l;

  const _CategoryProductsView({
    required this.products,
    required this.categoryName,
    required this.onBack,
    this.onProductTapped,
    required this.isDark,
    required this.l,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: _BackHeader(
            title: categoryName,
            onBack: onBack,
            isDark: isDark,
          ),
        ),
        Expanded(
          child: products.isEmpty
              ? EmptyState(
                  icon: Icons.shopping_basket_outlined,
                  message: l.searchNoResults,
                )
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                  itemCount: products.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 14),
                  itemBuilder: (_, i) => ApiProductCard(
                    product: products[i],
                    onTap: () => onProductTapped?.call(products[i]),
                  ),
                ),
        ),
      ],
    );
  }
}

class _SearchResultsList extends StatelessWidget {
  final List<ApiProduct> products;
  final ValueChanged<ApiProduct>? onProductTapped;
  final bool isDark;
  final AppLocalizations l;

  const _SearchResultsList({
    required this.products,
    this.onProductTapped,
    required this.isDark,
    required this.l,
  });

  @override
  Widget build(BuildContext context) {
    if (products.isEmpty) {
      return EmptyState(
        icon: Icons.search_off_rounded,
        message: l.searchNoResults,
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: products.length,
      separatorBuilder: (_, _) => const SizedBox(height: 14),
      itemBuilder: (_, i) => ApiProductCard(
        product: products[i],
        onTap: () => onProductTapped?.call(products[i]),
      ),
    );
  }
}
