# KortingKlok app

Flutter app for iOS and Android. Browse supermarket deals, search by store and
category, follow products, and receive a push notification when a followed
product changes price.

## Requirements

- [Flutter](https://docs.flutter.dev/install/quick) on the stable channel
- Xcode for iOS, Android Studio for Android
  ([iOS setup](https://docs.flutter.dev/platform-integration/ios/setup),
  [Android setup](https://docs.flutter.dev/platform-integration/android/setup))
- A Firebase project with Authentication and Cloud Messaging enabled
- A running [backend](../backend/README.md)

## Firebase setup

The app needs its own Firebase project. The generated configuration is
gitignored, so nobody ships someone else's project keys by accident.

```bash
make firebase
```

That activates the FlutterFire CLI and runs `flutterfire configure`, which
writes `firebase.json`, `lib/firebase_options.dart`,
`android/app/google-services.json`, and `ios/Runner/GoogleService-Info.plist`.

Two values are not generated and need editing by hand:

- `ios/Runner/Info.plist` contains a `CFBundleURLSchemes` placeholder. Replace
  it with the `REVERSED_CLIENT_ID` from your `GoogleService-Info.plist`, or
  Google sign-in will not return to the app.
- `ios/Runner.xcodeproj` has an empty `DEVELOPMENT_TEAM`. Set your Apple team in
  Xcode before building to a device, and export `DEVELOPMENT_TEAM` in your shell
  so CocoaPods signs the pods with the same team.

To compile without a Firebase project at all, for a quick look at the code or
in CI, drop in placeholders instead. The app builds but cannot sign in:

```bash
make firebase-placeholders
```

## Running

```bash
flutter pub get
flutter run --dart-define=API_HOST=http://localhost:8000
```

Everything environment-specific lives in [lib/config.dart](lib/config.dart) and
is set at build time:

| Define | Default | Purpose |
| --- | --- | --- |
| `API_HOST` | `http://localhost:8000` | Backend base URL, no trailing slash |
| `WEBSITE_URL` | empty | Site serving the terms and privacy pages. Empty hides those links |
| `SUPPORT_EMAIL` | empty | Address behind "contact support". Empty hides the entry |

On an Android emulator the host machine is `http://10.0.2.2:8000`.

## Quality

```bash
make format   # dart format lib/
make lint     # flutter analyze and a formatting check
flutter test
make local    # format and lint (what the pre-commit hook runs)
```

## Release builds

Android release builds are signed with the debug key unless you provide
`android/key.properties`, which is gitignored:

```properties
storePassword=...
keyPassword=...
keyAlias=...
storeFile=/absolute/path/to/keystore.jks
```

```bash
make android-release   # APK
make android-bundle    # AAB
make ios-release       # iOS app
make ios-bundle        # IPA
```

Change `applicationId` in `android/app/build.gradle.kts` and the bundle
identifier in Xcode before distributing your own build.

## Layout

```
lib/
  config.dart     build-time configuration
  main.dart       app entry, Firebase init, routing
  models/         API response models
  providers/      app state: session, locale, theme
  screens/        one file per screen
  services/       API client, auth, notifications
  theme/          colors and theming
  widgets/        shared widgets
  l10n/           Dutch and English strings
```
