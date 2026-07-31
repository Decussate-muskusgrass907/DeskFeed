import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/websocket_service.dart';
import '../services/notification_service.dart';
import '../widgets/activity_card.dart';
import '../widgets/email_alert_card.dart';
import 'stream_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _tab = 0;

  @override
  void initState() {
    super.initState();
    _connect();
    _regFcm();
  }

  Future<void> _connect() async {
    final a = context.read<AuthService>();
    final w = context.read<WebSocketService>();
    if (a.token != null && a.deviceId != null) {
      await w.connect(a.token!, a.deviceId!);
    }
  }

  Future<void> _regFcm() async {
    final t = await NotificationService.getFcmToken();
    if (t != null) {
      await context.read<AuthService>().registerFcmToken(t);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ws = context.watch<WebSocketService>();
    final auth = context.watch<AuthService>();
    return Scaffold(
      appBar: AppBar(
        title: Text(auth.deviceName ?? 'DeskFeed'),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 8),
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: ws.isConnected ? Colors.green : Colors.red,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => auth.logout(),
          ),
        ],
      ),
      body: IndexedStack(
        index: _tab,
        children: [
          _buildActivity(ws),
          _buildEmail(ws),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const StreamScreen()),
        ),
        icon: const Icon(Icons.videocam),
        label: const Text('Live View'),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.list_alt_rounded),
            label: 'Activity',
          ),
          NavigationDestination(
            icon: Icon(Icons.email_rounded),
            label: 'Emails',
          ),
        ],
      ),
    );
  }

  Widget _buildActivity(WebSocketService ws) {
    if (ws.activityCount == 0) {
      return _empty(Icons.hourglass_empty, 'Waiting...');
    }
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 80),
      itemCount: ws.recentActivities.length,
      itemBuilder: (_, i) => ActivityCard(activity: ws.recentActivities[i]),
    );
  }

  Widget _buildEmail(WebSocketService ws) {
    if (ws.recentEmails.isEmpty) {
      return _empty(Icons.email_outlined, 'No alerts');
    }
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 80),
      itemCount: ws.recentEmails.length,
      itemBuilder: (_, i) => EmailAlertCard(alert: ws.recentEmails[i]),
    );
  }

  Widget _empty(IconData icon, String text) {
    final t = Theme.of(context);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 64, color: t.colorScheme.onSurfaceVariant),
          const SizedBox(height: 16),
          Text(text, style: t.textTheme.bodyLarge),
        ],
      ),
    );
  }
}
