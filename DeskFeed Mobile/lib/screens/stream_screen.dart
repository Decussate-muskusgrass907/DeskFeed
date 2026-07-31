import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/websocket_service.dart';

class StreamScreen extends StatefulWidget {
  const StreamScreen({super.key});

  @override
  State<StreamScreen> createState() => _StreamScreenState();
}

class _StreamScreenState extends State<StreamScreen> {
  bool _isStreaming = false;
  ui.Image? _currentFrame;

  @override
  void initState() {
    super.initState();
    context.read<WebSocketService>().frameStream.listen((f) {
      if (mounted) setState(() => _currentFrame = f);
    });
  }

  @override
  void dispose() {
    if (_isStreaming) {
      context.read<WebSocketService>().stopStream();
    }
    super.dispose();
  }

  void _toggleStream() {
    final ws = context.read<WebSocketService>();
    if (_isStreaming) {
      ws.stopStream();
    } else {
      ws.requestStream();
    }
    setState(() => _isStreaming = !_isStreaming);
  }

  @override
  Widget build(BuildContext context) {
    final ws = context.watch<WebSocketService>();
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Live View'),
        actions: [
          if (ws.audioActive)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.mic, size: 16, color: Colors.green),
                  const SizedBox(width: 4),
                  Text('Audio', style: TextStyle(color: Colors.green, fontSize: 12)),
                ],
              ),
            ),
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Icon(
              _isStreaming
                  ? Icons.fiber_manual_record
                  : Icons.radio_button_off,
              color: _isStreaming ? Colors.red : Colors.grey,
              size: 20,
            ),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Expanded(
              child: RepaintBoundary(
                child: Container(
                  margin: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.black,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color:
                          _isStreaming ? Colors.red : Colors.grey.shade700,
                      width: 2,
                    ),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: _currentFrame != null
                        ? RawImage(
                            image: _currentFrame,
                            fit: BoxFit.contain,
                            filterQuality: FilterQuality.medium,
                          )
                        : Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.videocam_off,
                                  size: 64,
                                  color: theme.colorScheme.onSurfaceVariant,
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  _isStreaming
                                      ? 'Connecting...'
                                      : 'Tap Start',
                                  style: theme.textTheme.bodyLarge,
                                ),
                              ],
                            ),
                          ),
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: FilledButton.icon(
                onPressed: _toggleStream,
                icon:
                    Icon(_isStreaming ? Icons.stop : Icons.play_arrow),
                label: Text(_isStreaming ? 'Stop' : 'Start'),
                style: FilledButton.styleFrom(
                  minimumSize: const Size(180, 48),
                  backgroundColor: _isStreaming
                      ? Colors.red
                      : theme.colorScheme.primary,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
