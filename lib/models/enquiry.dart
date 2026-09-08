/// Model representing a wholesale enquiry / proposal between an artisan and a buyer.
class Enquiry {
  final int id;
  final int buyerId;
  final int productId;
  final String? buyerCompany;
  final String? productName;
  final String message;
  final String status; // pending | contacted | accepted | rejected
  final String? artisanResponse;
  final DateTime? createdAt;
  final DateTime? respondedAt;

  Enquiry({
    required this.id,
    required this.buyerId,
    required this.productId,
    this.buyerCompany,
    this.productName,
    required this.message,
    required this.status,
    this.artisanResponse,
    this.createdAt,
    this.respondedAt,
  });

  factory Enquiry.fromJson(Map<String, dynamic> json) {
    return Enquiry(
      id: json['id'] as int,
      buyerId: json['buyer_id'] as int,
      productId: json['product_id'] as int,
      buyerCompany: json['buyer_company'] as String?,
      productName: json['product_name'] as String?,
      message: json['message'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      artisanResponse: json['artisan_response'] as String?,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      respondedAt: json['responded_at'] != null ? DateTime.tryParse(json['responded_at'].toString()) : null,
    );
  }
}
