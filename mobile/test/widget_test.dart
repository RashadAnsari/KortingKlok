import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:korting_klok/main.dart';
import 'package:korting_klok/providers/app_state.dart';

void main() {
  testWidgets('App starts on welcome screen in Dutch', (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(const AppStateScope(child: KortingKlokApp()));
    await tester.pumpAndSettle();

    expect(find.text('KortingKlok'), findsWidgets);
    // Default language is Dutch on auth screens
    expect(find.text('Aan de slag'), findsOneWidget);
  });
}
