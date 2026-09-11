# Run formatter and linter together (use before committing)
local: format lint

# Auto-format all Dart source files in lib/
format:
	dart format lib/

# Check for analysis issues and verify formatting is clean (used in CI)
lint:
	flutter analyze
	dart format --set-exit-if-changed lib/

# Configure Firebase for the project (requires Firebase CLI and setup)
firebase:
	dart pub global activate flutterfire_cli
	export PATH="$PATH":"$HOME/.pub-cache/bin"
	flutterfire configure

# Drop in placeholder Firebase config so the app compiles and analyzes without
# a real Firebase project (used by CI). It cannot talk to Firebase at runtime.
firebase-placeholders:
	cp firebase.json.example firebase.json
	cp lib/firebase_options.dart.example lib/firebase_options.dart
	cp android/app/google-services.json.example android/app/google-services.json
	cp ios/Runner/GoogleService-Info.plist.example ios/Runner/GoogleService-Info.plist

# ── Android ───────────────────────────────────────────────────────────────────

# Build a release APK signed with the release keystore (output: build/app/outputs/apk/release/app-release.apk)
android-release:
	flutter build apk --release

# Build a release App Bundle for Play Store upload (output: build/app/outputs/bundle/release/app-release.aab)
android-bundle:
	flutter build appbundle --release

# Build and install a release APK on a connected Android device
android-install:
	flutter install --release

# ── iOS ───────────────────────────────────────────────────────────────────────

# Open the iOS Simulator app
ios-simulator:
	open -a Simulator

# Build a release iOS app (requires valid provisioning profile and Apple Developer account)
ios-release:
	flutter build ios --release

# Build a release IPA for App Store / TestFlight upload (output: build/ios/ipa/)
ios-bundle:
	flutter build ipa --release

# Build and install a release app on a connected iOS device
ios-install:
	flutter run --release
