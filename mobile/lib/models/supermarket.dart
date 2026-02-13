class Supermarket {
  final int id;
  final String name;
  final String slug;
  final String? logoUrl;
  final String? websiteUrl;

  const Supermarket({
    required this.id,
    required this.name,
    required this.slug,
    this.logoUrl,
    this.websiteUrl,
  });

  factory Supermarket.fromJson(Map<String, dynamic> json) => Supermarket(
    id: json['id'] as int,
    name: json['name'] as String,
    slug: json['slug'] as String,
    logoUrl: json['logo_url'] as String?,
    websiteUrl: json['website_url'] as String?,
  );
}
