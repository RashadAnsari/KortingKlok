import 'dart:convert';
import 'dart:io';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:http/http.dart' as http;

const _apiHostOverride = String.fromEnvironment('API_HOST');

String get _baseUrl {
  if (_apiHostOverride.isNotEmpty) return '$_apiHostOverride/api/v1';
  final host = Platform.isAndroid ? '10.0.2.2' : '127.0.0.1';
  return 'http://$host:8000/api/v1';
}

class ApiService {
  Future<Map<String, String>> _headers() async {
    final token = await FirebaseAuth.instance.currentUser!.getIdToken();
    return {'Authorization': 'Bearer $token'};
  }

  Future<dynamic> get(String path, {Map<String, String?>? params}) async {
    final queryParams = <String, String>{};
    if (params != null) {
      for (final e in params.entries) {
        if (e.value != null && e.value!.isNotEmpty) {
          queryParams[e.key] = e.value!;
        }
      }
    }

    final uri = Uri.parse(
      '$_baseUrl$path',
    ).replace(queryParameters: queryParams.isNotEmpty ? queryParams : null);

    final response = await http.get(uri, headers: await _headers());

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw ApiException(response.statusCode, path);
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? body}) async {
    final uri = Uri.parse('$_baseUrl$path');
    final headers = {...await _headers(), 'Content-Type': 'application/json'};
    final response = await http.post(
      uri,
      headers: headers,
      body: body != null ? jsonEncode(body) : null,
    );
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return response.body.isNotEmpty ? jsonDecode(response.body) : null;
    }
    throw ApiException(response.statusCode, path);
  }

  Future<void> delete(String path) async {
    final uri = Uri.parse('$_baseUrl$path');
    final response = await http.delete(uri, headers: await _headers());
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    throw ApiException(response.statusCode, path);
  }
}

class ApiException implements Exception {
  final int statusCode;
  final String path;

  const ApiException(this.statusCode, this.path);

  @override
  String toString() => 'ApiException($statusCode) on $path';
}
