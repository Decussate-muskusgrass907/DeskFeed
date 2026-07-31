import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/auth_service.dart';
import 'services/websocket_service.dart';
import 'services/notification_service.dart';
import 'services/config_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/stream_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ConfigService.load();
  try {
    await NotificationService.initialize();
  } catch (e) {
    debugPrint('NotificationService init failed: $e');
  }
  runApp(const DeskFeedApp());
}

class DeskFeedApp extends StatelessWidget {
  const DeskFeedApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
        ChangeNotifierProvider(create: (_) => WebSocketService()),
      ],
      child: MaterialApp(
        title: 'DeskFeed Mobile',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorSchemeSeed: Colors.indigo,
          brightness: Brightness.dark,
          useMaterial3: true,
        ),
        home: const AuthGate(),
      ),
    );
  }
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    if (auth.isAuthenticated) {
      return const DashboardScreen();
    }
    return const LoginScreen();
  }
}
