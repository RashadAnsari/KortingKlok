# Run formatter and linter together (use before committing)
local: format lint

# Auto-format all Dart source files in lib/
format:
	dart format lib/

# Check for analysis issues and verify formatting is clean (used in CI)
lint:
	flutter analyze
	dart format --set-exit-if-changed lib/

# Open the iOS Simulator app
simulator:
	open -a Simulator

# ── Android ───────────────────────────────────────────────────────────────────

# Build a debug APK for local testing (output: build/app/outputs/apk/debug/app-debug.apk)
android-debug:
	flutter build apk --debug

# Build a release APK signed with the release keystore (output: build/app/outputs/apk/release/app-release.apk)
android-release:
	flutter build apk --release

# Build a release App Bundle for Play Store upload (output: build/app/outputs/bundle/release/app-release.aab)
android-bundle:
	flutter build appbundle --release

# ── iOS ───────────────────────────────────────────────────────────────────────

# Build a debug iOS app without code signing (for simulator use)
ios-debug:
	flutter build ios --debug --no-codesign

# Build a release iOS app (requires valid provisioning profile and Apple Developer account)
ios-release:
	flutter build ios --release
