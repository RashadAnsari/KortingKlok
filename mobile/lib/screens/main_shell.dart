import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../widgets/kk_logo.dart';
import 'home_screen.dart';
import 'search_screen.dart';
import 'profile_screen.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    SearchScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: Row(
          children: [
            const KKLogo(size: 28),
            const SizedBox(width: 8),
            Text(
              'KortingKlok',
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: isDark ? AppColors.primaryOrange : AppColors.darkBlue,
              ),
            ),
          ],
        ),
        actions: [
          GestureDetector(
            onTap: () => setState(() => _currentIndex = 2),
            child: Container(
              width: 30,
              height: 30,
              margin: const EdgeInsets.only(right: 16),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkBorder : AppColors.lightGray,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.person,
                size: 16,
                color: isDark ? AppColors.darkText : AppColors.lightText,
              ),
            ),
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
      body: IndexedStack(index: _currentIndex, children: _screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
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
