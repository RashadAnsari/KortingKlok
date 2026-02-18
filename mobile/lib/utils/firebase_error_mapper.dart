import 'package:firebase_auth/firebase_auth.dart';
import '../l10n/app_localizations.dart';

String mapFirebaseError(Object e, AppLocalizations l, {bool isReauth = false}) {
  if (e is FirebaseAuthException) {
    switch (e.code) {
      case 'invalid-credential':
      case 'wrong-password':
        return isReauth
            ? l.authErrorWrongPassword
            : l.authErrorInvalidCredential;
      case 'user-not-found':
        return l.authErrorUserNotFound;
      case 'email-already-in-use':
        return l.authErrorEmailInUse;
      case 'weak-password':
        return l.authErrorWeakPassword;
      case 'network-request-failed':
        return l.authErrorNetwork;
      case 'requires-recent-login':
        return l.authErrorRequiresRecentLogin;
      default:
        return l.authErrorUnknown;
    }
  }
  final msg = e.toString();
  if (msg.contains('cancelled') || msg.contains('canceled')) {
    return l.authErrorCancelled;
  }
  return l.authErrorUnknown;
}
