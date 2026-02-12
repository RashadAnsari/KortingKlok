import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  int _selectedTabIndex = 0;

  static const _stores = ['Albert Heijn', 'Jumbo', 'Lidl'];
  static const _storeShorts = ['AH', 'Jumbo', 'Lidl'];

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final currentStore = _stores[_selectedTabIndex];

    final categories = [
      l.searchCatDeals,
      l.searchCatFresh,
      l.searchCatDairy,
      l.searchCatMeat,
      l.searchCatDrinks,
    ];

    return Column(
      children: [
        // Search bar
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: TextField(
            decoration: InputDecoration(
              hintText: l.searchPlaceholder(currentStore),
              prefixIcon: const Icon(Icons.search, size: 20),
            ),
          ),
        ),
        const SizedBox(height: 16),
        // Store tabs
        Container(
          decoration: BoxDecoration(
            border: Border(
              bottom: BorderSide(
                color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                width: 2,
              ),
            ),
          ),
          child: Row(
            children: List.generate(_storeShorts.length, (i) {
              final isActive = _selectedTabIndex == i;
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _selectedTabIndex = i),
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
                      _storeShorts[i],
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: isActive
                            ? AppColors.primaryOrange
                            : (isDark
                                  ? AppColors.darkSecondary
                                  : const Color(0xFF666666)),
                      ),
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
        // Categories
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(
                l.searchCategoriesTitle(currentStore),
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w600,
                  color: isDark ? AppColors.darkText : AppColors.darkBlue,
                ),
              ),
              const SizedBox(height: 14),
              ...categories.map((cat) => _CategoryItem(name: cat)),
            ],
          ),
        ),
      ],
    );
  }
}

class _CategoryItem extends StatelessWidget {
  final String name;

  const _CategoryItem({required this.name});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
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
    );
  }
}
