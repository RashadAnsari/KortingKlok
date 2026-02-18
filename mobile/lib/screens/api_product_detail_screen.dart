import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../l10n/app_localizations.dart';
import '../models/api_product.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';

class ApiProductDetailArgs {
  final ApiProduct product;
  final String? supermarketName;
  final String? supermarketLogoUrl;

  const ApiProductDetailArgs({
    required this.product,
    this.supermarketName,
    this.supermarketLogoUrl,
  });
}

class ApiProductDetailScreen extends StatefulWidget {
  const ApiProductDetailScreen({super.key});

  @override
  State<ApiProductDetailScreen> createState() => _ApiProductDetailScreenState();
}

class _ApiProductDetailScreenState extends State<ApiProductDetailScreen> {
  final _api = ApiService();
  final _shareButtonKey = GlobalKey();
  bool _initialized = false;
  late ApiProductDetailArgs _args;
  bool? _isTracked;
  bool _trackingLoading = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      _initialized = true;
      _args =
          ModalRoute.of(context)!.settings.arguments as ApiProductDetailArgs;
      _loadTrackingStatus();
    }
  }

  void _loadTrackingStatus() {
    setState(() => _isTracked = _args.product.isTracked);
  }

  Future<void> _toggleTracking() async {
    if (_isTracked == null || _trackingLoading) return;
    setState(() => _trackingLoading = true);
    try {
      if (_isTracked!) {
        await _api.delete('/products/${_args.product.id}/track');
      } else {
        await _api.post('/products/${_args.product.id}/track');
      }
      if (mounted) {
        setState(() {
          _isTracked = !_isTracked!;
          _trackingLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _trackingLoading = false);
        final l = AppLocalizations.of(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(
                  Icons.error_outline_rounded,
                  color: Colors.white,
                  size: 20,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    l.errorGeneric,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
            behavior: SnackBarBehavior.floating,
            backgroundColor: const Color(0xFF323232),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            action: SnackBarAction(
              label: l.retryButton,
              textColor: AppColors.primaryOrange,
              onPressed: _toggleTracking,
            ),
            duration: const Duration(seconds: 5),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_initialized) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final product = _args.product;
    final supermarketName = _args.supermarketName;
    final supermarketLogoUrl = _args.supermarketLogoUrl;
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) Navigator.pop(context, _isTracked);
      },
      child: Scaffold(
        appBar: AppBar(
          leadingWidth: 100,
          leading: GestureDetector(
            onTap: () => Navigator.pop(context, _isTracked),
            child: Row(
              children: [
                const SizedBox(width: 4),
                Icon(
                  Icons.arrow_back_ios,
                  size: 16,
                  color: isDark ? AppColors.primaryOrange : AppColors.darkBlue,
                ),
                const SizedBox(width: 2),
                Text(
                  l.detailBack,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: isDark
                        ? AppColors.primaryOrange
                        : AppColors.darkBlue,
                  ),
                ),
              ],
            ),
          ),
          actions: [
            IconButton(
              key: _shareButtonKey,
              icon: Icon(
                Icons.ios_share,
                color: isDark ? AppColors.darkSecondary : AppColors.midGray,
              ),
              onPressed: product.websiteUrl != null
                  ? () {
                      final box =
                          _shareButtonKey.currentContext?.findRenderObject()
                              as RenderBox?;
                      Share.shareUri(
                        Uri.parse(product.websiteUrl!),
                        sharePositionOrigin: box == null
                            ? null
                            : box.localToGlobal(Offset.zero) & box.size,
                      );
                    }
                  : null,
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
              SizedBox(
                width: double.infinity,
                height: 200,
                child: product.imageUrl != null
                    ? Image.network(
                        product.imageUrl!,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) =>
                            _ImagePlaceholder(isDark: isDark),
                      )
                    : _ImagePlaceholder(isDark: isDark),
              ),
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
                    if (product.category != null) ...[
                      const SizedBox(height: 6),
                      Text(
                        product.category!.name,
                        style: TextStyle(
                          fontSize: 14,
                          color: isDark
                              ? AppColors.darkSecondary
                              : AppColors.lightSecondary,
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),
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
                                fontSize: 17,
                                color: AppColors.lightSecondary,
                                decoration: TextDecoration.lineThrough,
                              ),
                            ),
                            const SizedBox(width: 10),
                          ],
                          Text(
                            '€${product.currentPrice}',
                            style: const TextStyle(
                              fontSize: 26,
                              fontWeight: FontWeight.w700,
                              color: AppColors.primaryOrange,
                            ),
                          ),
                        ],
                      ),
                    if (product.discountText != null) ...[
                      const SizedBox(height: 12),
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
                          product.discountText!,
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 20),
                    if (supermarketName != null)
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
                                    : AppColors.midGray,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                _StoreLogo(
                                  name: supermarketName,
                                  logoUrl: supermarketLogoUrl,
                                  size: 40,
                                ),
                                const SizedBox(width: 12),
                                Text(
                                  supermarketName,
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
                    if (_isTracked != null) ...[
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _trackingLoading ? null : _toggleTracking,
                          icon: _trackingLoading
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : Icon(
                                  _isTracked!
                                      ? Icons.bookmark_remove_outlined
                                      : Icons.bookmark_add_outlined,
                                ),
                          label: Text(
                            _isTracked! ? l.detailUntrack : l.detailTrack,
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: _isTracked!
                                ? AppColors.lightSecondary
                                : AppColors.primaryOrange,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                    ],
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton(
                        onPressed: product.websiteUrl != null
                            ? () => launchUrl(
                                Uri.parse(product.websiteUrl!),
                                mode: LaunchMode.externalApplication,
                              )
                            : null,
                        child: Text(l.detailViewAt(supermarketName ?? '')),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ImagePlaceholder extends StatelessWidget {
  final bool isDark;

  const _ImagePlaceholder({required this.isDark});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isDark
              ? [AppColors.darkBorder, AppColors.darkSurface]
              : [AppColors.lightSurface, AppColors.lightBorder],
        ),
      ),
      child: const Center(
        child: Icon(
          Icons.shopping_basket_outlined,
          size: 56,
          color: AppColors.lightSecondary,
        ),
      ),
    );
  }
}

class _StoreLogo extends StatelessWidget {
  final String name;
  final String? logoUrl;
  final double size;

  const _StoreLogo({required this.name, this.logoUrl, this.size = 36});

  @override
  Widget build(BuildContext context) {
    if (logoUrl != null) {
      return SvgPicture.network(
        logoUrl!,
        width: size,
        height: size,
        fit: BoxFit.contain,
        placeholderBuilder: (_) => _fallback(),
      );
    }
    return _fallback();
  }

  Widget _fallback() {
    final lower = name.toLowerCase();
    final Color bg;
    final Color fg;
    final String label;

    if (lower.contains('albert') || lower == 'ah') {
      bg = AppColors.ahBlue;
      fg = Colors.white;
      label = 'AH';
    } else if (lower.contains('jumbo')) {
      bg = AppColors.jumboYellow;
      fg = Colors.black;
      label = 'JB';
    } else if (lower.contains('lidl')) {
      bg = AppColors.lidlBlue;
      fg = AppColors.lidlYellow;
      label = 'Lidl';
    } else {
      bg = AppColors.primaryOrange;
      fg = Colors.white;
      label = name.isNotEmpty ? name[0].toUpperCase() : '?';
    }

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(color: bg, shape: BoxShape.circle),
      child: Center(
        child: Text(
          label,
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
