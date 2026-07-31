import 'package:flutter/material.dart';
import '../models/activity_log.dart';

class ActivityCard extends StatelessWidget {
  final ActivityLog activity;

  const ActivityCard({super.key, required this.activity});

  IconData _getAppIcon(String? appName) {
    if (appName == null) return Icons.android;
    final name = appName.toLowerCase();
    if (name.contains('chrome') || name.contains('edge') || name.contains('firefox')) {
      return Icons.language;
    }
    if (name.contains('explorer')) return Icons.folder;
    if (name.contains('code') || name.contains('terminal')) return Icons.code;
    if (name.contains('outlook') || name.contains('mail')) return Icons.mail;
    if (name.contains('word') || name.contains('excel') || name.contains('powerpoint')) {
      return Icons.description;
    }
    return Icons.android;
  }

  Color _getAppColor(String? appName) {
    if (appName == null) return Colors.grey;
    final name = appName.toLowerCase();
    if (name.contains('chrome')) return Colors.green;
    if (name.contains('edge')) return Colors.blue;
    if (name.contains('firefox')) return Colors.orange;
    if (name.contains('explorer')) return Colors.amber;
    if (name.contains('outlook')) return Colors.blue;
    if (name.contains('code')) return Colors.indigo;
    return Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: _getAppColor(activity.appName).withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                _getAppIcon(activity.appName),
                color: _getAppColor(activity.appName),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    activity.appName ?? 'Unknown',
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  if (activity.windowTitle != null && activity.windowTitle!.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      activity.windowTitle!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                  if (activity.browserUrl != null) ...[
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Icon(Icons.link, size: 12, color: Colors.green),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            activity.browserUrl!,
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: Colors.green.shade300,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                  if (activity.folderPath != null) ...[
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Icon(Icons.folder, size: 12, color: Colors.amber),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            activity.folderPath!,
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: Colors.amber.shade300,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            Text(
              activity.formattedTime,
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
