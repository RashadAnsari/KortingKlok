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

  Future<bool> requestPermission() async {
    final settings = await _messaging.requestPermission();
    return settings.authorizationStatus == AuthorizationStatus.authorized ||
        settings.authorizationStatus == AuthorizationStatus.provisional;
  }

  Future<void> clearNotifications() async {
    try {
      await _channel.invokeMethod('clearNotifications');
    } catch (_) {}
  }

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

  Future<void> registerDeviceIfNeeded(String language) async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool(_keyDeviceRegistered) == true) return;
    await registerDevice(language);
  }

  Future<void> registerDevice(String language) async {
    try {
      String? fcmToken;
      for (var i = 0; i < 15; i++) {
        try {
          if (Platform.isIOS) await _messaging.getAPNSToken();
          fcmToken = await _messaging.getToken();
          if (fcmToken != null) break;
        } catch (_) {}
        await Future.delayed(const Duration(seconds: 2));
      }
      if (fcmToken == null) return;

      final deviceId = await getDeviceId();
      final deviceType = Platform.isIOS ? 'ios' : 'android';

      await _api.post(
        '/users/devices',
        body: {
          'fcm_token': fcmToken,
          'device_id': deviceId,
          'device_type': deviceType,
          'language': language,
        },
      );

      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_keyDeviceRegistered, true);
    } catch (_) {}
  }

  Future<void> unregisterDevice() async {
    try {
      final deviceId = await getDeviceId();
      await _api.post('/users/logout', body: {'device_id': deviceId});
    } catch (_) {}
  }

  Future<void> clearRegistration() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyDeviceRegistered);
    await prefs.remove(_keyDeviceId);
  }
}
