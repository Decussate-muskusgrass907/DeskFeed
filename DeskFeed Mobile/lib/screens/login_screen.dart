import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/config_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _deviceIdController = TextEditingController();
  final _pinController = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _deviceIdController.dispose();
    _pinController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    final auth = context.read<AuthService>();
    final deviceId = _deviceIdController.text.trim();
    final pin = _pinController.text.trim();

    if (deviceId.isEmpty || pin.isEmpty) {
      setState(() => _error = 'Please fill in all fields');
      return;
    }

    final error = await auth.login(deviceId, pin);
    if (error != null) {
      setState(() => _error = error);
    }
  }

  void _showSettings() {
    final controller = TextEditingController(text: ConfigService.httpUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Server URL'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Server URL',
            hintText: 'http://your-ip:3000',
            border: OutlineInputBorder(),
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () async {
              await ConfigService.setUrl(controller.text.trim());
              if (ctx.mounted) Navigator.pop(ctx);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: _showSettings,
            tooltip: 'Configure Server URL',
          ),
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.security, size: 80, color: theme.colorScheme.primary),
              const SizedBox(height: 16),
              Text(
                'DeskFeed Mobile',
                style: theme.textTheme.headlineLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Enter your pairing details',
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 32),
              TextField(
                controller: _deviceIdController,
                decoration: const InputDecoration(
                  labelText: 'Device ID',
                  prefixIcon: Icon(Icons.computer),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _pinController,
                decoration: const InputDecoration(
                  labelText: 'Pairing PIN',
                  prefixIcon: Icon(Icons.pin),
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                maxLength: 6,
                obscureText: true,
              ),
              if (_error != null) ...[
                const SizedBox(height: 8),
                Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
              ],
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: FilledButton(
                  onPressed: auth.isLoading ? null : _login,
                  child: auth.isLoading
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Connect'),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                ConfigService.httpUrl,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.6),
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
