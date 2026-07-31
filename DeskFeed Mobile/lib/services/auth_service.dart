import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'config_service.dart';

class AuthService extends ChangeNotifier {
  String? _token;
  String? _deviceId;
  String? _deviceName;
  bool _isLoading = false;

  String get _baseUrl => ConfigService.httpUrl;

  String? get token => _token;
  String? get deviceId => _deviceId;
  String? get deviceName => _deviceName;
  bool get isAuthenticated => _token != null;
  bool get isLoading => _isLoading;

  AuthService() {
    _loadSavedAuth();
  }

  Future<void> _loadSavedAuth() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('auth_token');
    _deviceId = prefs.getString('device_id');
    _deviceName = prefs.getString('device_name');
    notifyListeners();
  }

  Future<String?> login(String deviceId, String pin) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/api/auth/viewer-login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'deviceId': deviceId,
          'pairingPin': pin,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['token'];
        _deviceId = deviceId;
        _deviceName = data['deviceName'];

        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', _token!);
        await prefs.setString('device_id', _deviceId!);
        await prefs.setString('device_name', _deviceName ?? '');

        _isLoading = false;
        notifyListeners();
        return null;
      } else {
        _isLoading = false;
        notifyListeners();
        return 'Invalid device ID or PIN';
      }
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return 'Connection error: $e';
    }
  }

  Future<void> registerFcmToken(String fcmToken) async {
    if (_token == null || _deviceId == null) return;

    try {
      await http.post(
        Uri.parse('$_baseUrl/api/auth/register-fcm'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
        body: jsonEncode({
          'deviceId': _deviceId,
          'fcmToken': fcmToken,
        }),
      );
    } catch (e) {
      debugPrint('FCM token registration failed: $e');
    }
  }

  Future<void> logout() async {
    _token = null;
    _deviceId = null;
    _deviceName = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('device_id');
    await prefs.remove('device_name');
    notifyListeners();
  }
}
