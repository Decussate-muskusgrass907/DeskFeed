class ActivityLog {
  final String? appName;
  final String? browserUrl;
  final String? folderPath;
  final String? windowTitle;
  final String timestamp;
  final String deviceName;
  final String deviceId;

  ActivityLog({
    this.appName,
    this.browserUrl,
    this.folderPath,
    this.windowTitle,
    required this.timestamp,
    this.deviceName = '',
    this.deviceId = '',
  });

  factory ActivityLog.fromJson(Map<String, dynamic> json) {
    return ActivityLog(
      appName: json['appName'] as String?,
      browserUrl: json['browserUrl'] as String?,
      folderPath: json['folderPath'] as String?,
      windowTitle: json['windowTitle'] as String?,
      timestamp: json['timestamp'] as String? ?? DateTime.now().toIso8601String(),
      deviceName: json['deviceName'] as String? ?? '',
      deviceId: json['deviceId'] as String? ?? '',
    );
  }

  DateTime get dateTime => DateTime.tryParse(timestamp) ?? DateTime.now();

  String get formattedTime {
    final dt = dateTime;
    return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}:${dt.second.toString().padLeft(2, '0')}';
  }
}
