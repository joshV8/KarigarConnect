/// Model representing an in-app notification for the artisan.
class NotificationItem {
  final int id;
  final String type;
  final String title;
  final String message;
  final int? relatedProductId;
  final int? relatedEnquiryId;
  final bool isRead;
  final DateTime? createdAt;

  NotificationItem({
    required this.id,
    required this.type,
    required this.title,
    required this.message,
    this.relatedProductId,
    this.relatedEnquiryId,
    required this.isRead,
    this.createdAt,
  });

  factory NotificationItem.fromJson(Map<String, dynamic> json) {
    return NotificationItem(
      id: json['id'] as int,
      type: json['type'] as String? ?? 'system',
      title: json['title'] as String? ?? 'Notification',
      message: json['message'] as String? ?? '',
      relatedProductId: json['related_product_id'] as int?,
      relatedEnquiryId: json['related_enquiry_id'] as int?,
      isRead: json['is_read'] as bool? ?? false,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
    );
  }
}
