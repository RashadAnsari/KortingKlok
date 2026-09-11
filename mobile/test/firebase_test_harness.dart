import 'package:firebase_auth_platform_interface/firebase_auth_platform_interface.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_core_platform_interface/test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

/// Initialises Firebase with fakes so widget tests can pump the real app
/// without a Firebase project. Signed out is the only state it reproduces;
/// tests that need a signed-in user should fake at a higher level.
Future<void> setUpFakeFirebase() async {
  TestWidgetsFlutterBinding.ensureInitialized();
  setupFirebaseCoreMocks();
  FirebaseAuthPlatform.instance = _FakeFirebaseAuth();
  await Firebase.initializeApp();
}

class _FakeFirebaseAuth extends FirebaseAuthPlatform
    with MockPlatformInterfaceMixin {
  @override
  UserPlatform? get currentUser => null;

  @override
  String? get languageCode => 'nl';

  @override
  FirebaseAuthPlatform delegateFor({required FirebaseApp app}) => this;

  @override
  FirebaseAuthPlatform setInitialValues({
    PigeonUserDetails? currentUser,
    String? languageCode,
  }) => this;

  @override
  Stream<UserPlatform?> authStateChanges() => Stream.value(null);

  @override
  Stream<UserPlatform?> idTokenChanges() => Stream.value(null);

  @override
  Stream<UserPlatform?> userChanges() => Stream.value(null);

  @override
  Future<void> setLanguageCode(String? languageCode) async {}
}
