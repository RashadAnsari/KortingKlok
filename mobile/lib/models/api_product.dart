import 'category.dart';

class ApiProduct {
  final int id;
  final String name;
  final int supermarketId;
  final Category? category;
  final String? basePrice;
  final String? currentPrice;
  final bool hasDiscount;
  final String? discountText;
  final String? imageUrl;
  final String? websiteUrl;
  final bool isTracked;

  const ApiProduct({
    required this.id,
    required this.name,
    required this.supermarketId,
    this.category,
    this.basePrice,
    this.currentPrice,
    required this.hasDiscount,
    this.discountText,
    this.imageUrl,
    this.websiteUrl,
    this.isTracked = false,
  });

  factory ApiProduct.fromJson(Map<String, dynamic> json) => ApiProduct(
    id: json['id'] as int,
    name: json['name'] as String,
    supermarketId: json['supermarket'] as int,
    category: json['category'] != null
        ? Category.fromJson(json['category'] as Map<String, dynamic>)
        : null,
    basePrice: json['base_price'] as String?,
    currentPrice: json['current_price'] as String?,
    hasDiscount: json['has_discount'] as bool,
    discountText: json['discount_text'] as String?,
    imageUrl: json['image_url'] as String?,
    websiteUrl: json['website_url'] as String?,
    isTracked: json['is_tracked'] as bool? ?? false,
  );
}
