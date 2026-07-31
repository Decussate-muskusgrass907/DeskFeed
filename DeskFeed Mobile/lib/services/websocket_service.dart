import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/io.dart';
import 'package:flutter_sound/flutter_sound.dart';
import '../models/activity_log.dart';
import '../models/email_alert.dart';
import 'config_service.dart';

class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  List<ActivityLog> _recentActivities = [];
  List<EmailAlert> _recentEmails = [];
  bool _isConnected = false;
  bool _audioActive = false;
  StreamSubscription? _subscription;
  final StreamController<ui.Image?> _frameController =
      StreamController<ui.Image?>.broadcast();
  FlutterSoundPlayer? _audioPlayer;

  static const int _maxActivities = 50;
  static const int _maxEmails = 30;
  DateTime _lastFrameTime = DateTime.now();
  static const Duration _frameThrottle = Duration(milliseconds: 66);

  String get _wsUrl => ConfigService.wsUrl;

  List<ActivityLog> get recentActivities =>
      List.unmodifiable(_recentActivities);
  List<EmailAlert> get recentEmails => List.unmodifiable(_recentEmails);
  bool get isConnected => _isConnected;
  bool get audioActive => _audioActive;
  Stream<ui.Image?> get frameStream => _frameController.stream;
  int get activityCount => _recentActivities.length;

  Future<void> connect(String token, String deviceId) async {
    try {
      final ws = await WebSocket.connect(
        '$_wsUrl',
        headers: {'Authorization': 'Bearer $token'},
      );
      _channel = IOWebSocketChannel(ws);
      _isConnected = true;
      notifyListeners();

      _audioPlayer = FlutterSoundPlayer();
      await _audioPlayer!.openPlayer();

      _subscription = _channel!.stream.listen(
        (message) => _handleMessage(jsonDecode(message as String)),
        onError: (_) {
          _isConnected = false;
          notifyListeners();
        },
        onDone: () {
          _isConnected = false;
          notifyListeners();
        },
      );
    } catch (_) {
      _isConnected = false;
      notifyListeners();
    }
  }

  void _handleMessage(Map<String, dynamic> data) {
    switch (data['type'] as String?) {
      case 'activity:update':
        _recentActivities.insert(0, ActivityLog.fromJson(data));
        if (_recentActivities.length > _maxActivities) {
          _recentActivities = _recentActivities.sublist(0, _maxActivities);
        }
        notifyListeners();
        break;

      case 'email:alert':
        _recentEmails.insert(0, EmailAlert.fromJson(data));
        if (_recentEmails.length > _maxEmails) {
          _recentEmails = _recentEmails.sublist(0, _maxEmails);
        }
        notifyListeners();
        break;

      case 'stream:video':
        final now = DateTime.now();
        if (now.difference(_lastFrameTime) < _frameThrottle) return;
        _lastFrameTime = now;
        _decodeFrame(data['data'] as String?);
        break;

      case 'stream:audio':
        _playAudio(data['data'] as String?);
        break;
    }
  }

  Future<void> _decodeFrame(String? b64) async {
    if (b64 == null || b64.isEmpty) return;
    try {
      final bytes = base64Decode(b64);
      final codec = await ui.instantiateImageCodec(bytes, targetWidth: 640);
      final frame = await codec.getNextFrame();
      _frameController.add(frame.image);
    } catch (_) {}
  }

  Future<void> _playAudio(String? b64) async {
    if (b64 == null || b64.isEmpty || _audioPlayer == null) return;
    try {
      final bytes = base64Decode(b64);
      if (!_audioActive) {
        _audioActive = true;
        notifyListeners();
        await _audioPlayer!.startPlayerFromStream(
          codec: Codec.pcm16,
          numChannels: 1,
          sampleRate: 16000,
          interleaved: false,
          bufferSize: 2048,
        );
      }
      _audioPlayer!.uint8ListSink?.add(bytes);
    } catch (_) {}
  }

  void requestStream() {
    _channel?.sink.add(jsonEncode({'type': 'stream:request'}));
  }

  void stopStream() {
    _audioActive = false;
    notifyListeners();
    _audioPlayer?.stopPlayer();
    _channel?.sink.add(jsonEncode({'type': 'stream:stop'}));
  }

  @override
  void dispose() {
    _audioPlayer?.closePlayer();
    _subscription?.cancel();
    _channel?.sink.close();
    _frameController.close();
    super.dispose();
  }
}
