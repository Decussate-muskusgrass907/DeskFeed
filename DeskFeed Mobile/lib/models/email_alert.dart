class EmailAlert {
  final String subject;
  final String sender;
  final String timestamp;
  final String deviceName;

  EmailAlert({
    required this.subject,
    required this.sender,
    required this.timestamp,
    this.deviceName = '',
  });

  factory EmailAlert.fromJson(Map<String, dynamic> json) {
    return EmailAlert(
      subject: json['subject'] as String? ?? '',
      sender: json['sender'] as String? ?? '',
      timestamp: json['timestamp'] as String? ?? DateTime.now().toIso8601String(),
      deviceName: json['deviceName'] as String? ?? '',
    );
  }
}
