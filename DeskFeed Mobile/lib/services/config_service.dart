import 'package:shared_preferences/shared_preferences.dart';

class ConfigService {
  static const _keyUrl = 'server_url';
  static const _defaultUrl = 'http://localhost:3000';

  static String _url = _defaultUrl;
  static bool _loaded = false;

  static String get httpUrl => _url;
  static String get wsUrl => '${_url.replaceAll(RegExp(r'/+$'), '')}/viewer-ws'
      .replaceFirst('http://', 'ws://')
      .replaceFirst('https://', 'wss://');

  static Future<void> load() async {
    if (_loaded) return;
    final prefs = await SharedPreferences.getInstance();
    _url = prefs.getString(_keyUrl) ?? _defaultUrl;
    _loaded = true;
  }

  static Future<void> setUrl(String url) async {
    _url = url.replaceAll(RegExp(r'/+$'), '');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyUrl, _url);
  }
}
