class Category {
  final int id;
  final String name;
  final int? parent;

  const Category({required this.id, required this.name, this.parent});

  factory Category.fromJson(Map<String, dynamic> json) => Category(
    id: json['id'] as int,
    name: json['name'] as String,
    parent: json['parent'] as int?,
  );
}
