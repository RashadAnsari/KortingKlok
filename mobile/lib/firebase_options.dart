// GENERATED FILE — do not edit manually.
//
// Run the following commands to regenerate this file for your Firebase project:
//
//   dart pub global activate flutterfire_cli
//   flutterfire configure
//
// See https://firebase.flutter.dev/docs/cli for setup instructions.

import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      throw UnsupportedError(
        'DefaultFirebaseOptions have not been configured for web. '
        'Run flutterfire configure to generate options.',
      );
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyCan-2nAXTEFnvzoov-EkZWpZbBkD9dE0s',
    appId: '1:227043916405:android:47acaf829c399aaadcd63c',
    messagingSenderId: '227043916405',
    projectId: 'kortingklok',
    storageBucket: 'kortingklok.firebasestorage.app',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyAV1SkuFPKRcs_Z-byHHbpQnUOoWWIKk9Q',
    appId: '1:227043916405:ios:d1ce291d8fd07f91dcd63c',
    messagingSenderId: '227043916405',
    projectId: 'kortingklok',
    storageBucket: 'kortingklok.firebasestorage.app',
    androidClientId:
        '227043916405-8940e9231c8qf700kbrbchubp658h7t7.apps.googleusercontent.com',
    iosClientId:
        '227043916405-8n5scju48od686ah0m3ngs6r5vdc6bsk.apps.googleusercontent.com',
    iosBundleId: 'nl.kortingklok.app',
  );
}
