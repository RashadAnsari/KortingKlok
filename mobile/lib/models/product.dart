enum Store { ah, jumbo, lidl }

class Product {
  final String name;
  final String category;
  final double oldPrice;
  final double newPrice;
  final String badgeText;
  final int discountPercent;
  final Store store;
  final String emoji;

  const Product({
    required this.name,
    required this.category,
    required this.oldPrice,
    required this.newPrice,
    required this.badgeText,
    required this.discountPercent,
    required this.store,
    required this.emoji,
  });

  String get storeLabel {
    switch (store) {
      case Store.ah:
        return 'Albert Heijn';
      case Store.jumbo:
        return 'Jumbo';
      case Store.lidl:
        return 'Lidl';
    }
  }

  String get storeShort {
    switch (store) {
      case Store.ah:
        return 'AH';
      case Store.jumbo:
        return 'JB';
      case Store.lidl:
        return 'Lidl';
    }
  }
}

final List<Product> mockProducts = [
  const Product(
    name: "Ben & Jerry's Cookie Dough",
    category: 'Ijs & Desserts',
    oldPrice: 4.99,
    newPrice: 3.49,
    badgeText: '1+1 GRATIS',
    discountPercent: 30,
    store: Store.ah,
    emoji: '\ud83c\udf66',
  ),
  const Product(
    name: 'Coca-Cola 6-pack',
    category: 'Frisdrank',
    oldPrice: 4.49,
    newPrice: 2.99,
    badgeText: '2e HALVE PRIJS',
    discountPercent: 33,
    store: Store.jumbo,
    emoji: '\ud83e\udd64',
  ),
  const Product(
    name: 'Pringles Original',
    category: 'Chips & Snacks',
    oldPrice: 2.79,
    newPrice: 1.49,
    badgeText: '1+1 GRATIS',
    discountPercent: 47,
    store: Store.lidl,
    emoji: '\ud83c\udf5f',
  ),
  const Product(
    name: 'Douwe Egberts Koffie',
    category: 'Koffie & Thee',
    oldPrice: 7.99,
    newPrice: 5.49,
    badgeText: '2e HALVE PRIJS',
    discountPercent: 31,
    store: Store.ah,
    emoji: '\u2615',
  ),
];
