import 'dart:io';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_service.dart';

class NotificationService {
  static const _keyDeviceId = 'device_id';
  static const _keyDeviceRegistered = 'device_registered';
  static const _channel = MethodChannel('nl.kortingklok.app/notifications');

  final _messaging = FirebaseMessaging.instance;
  final _api = ApiService();

  /// Request notification permission. Returns true if authorized or provisional.
  Future<bool> requestPermission() async {
    final settings = await _messaging.requestPermission();
    return settings.authorizationStatus == AuthorizationStatus.authorized ||
        settings.authorizationStatus == AuthorizationStatus.provisional;
  }

  /// Clear all delivered notifications from the notification tray.
  Future<void> clearNotifications() async {
    try {
      await _channel.invokeMethod('clearNotifications');
    } catch (_) {}
  }

  /// Get or create a stable device ID persisted in SharedPreferences.
  Future<String> getDeviceId() async {
    final prefs = await SharedPreferences.getInstance();
    var deviceId = prefs.getString(_keyDeviceId);
    if (deviceId == null) {
      deviceId =
          DateTime.now().microsecondsSinceEpoch.toRadixString(36) +
          Object().hashCode.toRadixString(36);
      await prefs.setString(_keyDeviceId, deviceId);
    }
    return deviceId;
  }

  /// Register this device only if it hasn't been registered yet.
  Future<void> registerDeviceIfNeeded(String language) async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool(_keyDeviceRegistered) == true) return;
    await registerDevice(language);
  }

  /// Register this device with the backend for push notifications.
  Future<void> registerDevice(String language) async {
    final token = await _messaging.getToken();
    if (token == null) return;

    final deviceId = await getDeviceId();
    final deviceType = Platform.isIOS ? 'ios' : 'android';

    await _api.post(
      '/users/devices',
      body: {
        'fcm_token': token,
        'device_id': deviceId,
        'device_type': deviceType,
        'language': language,
      },
    );

    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyDeviceRegistered, true);
  }

  /// Unregister this device from the backend (on logout).
  Future<void> unregisterDevice() async {
    final deviceId = await getDeviceId();
    await _api.post('/users/logout', body: {'device_id': deviceId});
  }

  /// Clear the registration flag and device ID (on logout).
  Future<void> clearRegistration() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyDeviceRegistered);
    await prefs.remove(_keyDeviceId);
  }
}
