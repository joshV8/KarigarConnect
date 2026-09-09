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

class NegotiationAnalysis {
  final bool isSustainable;
  final String evaluationSummary;
  final List<String> proposedCounterOffers;

  NegotiationAnalysis({
    required this.isSustainable,
    required this.evaluationSummary,
    required this.proposedCounterOffers,
  });

  factory NegotiationAnalysis.fromJson(Map<String, dynamic> json) {
    return NegotiationAnalysis(
      isSustainable: json['is_sustainable'] as bool? ?? false,
      evaluationSummary: json['evaluation_summary'] as String? ?? '',
      proposedCounterOffers: (json['proposed_counter_offers'] as List?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}

class FeasibilityBreakdown {
  final int requiredUnits;
  final int inventoryAvailable;
  final int unitsToProduce;
  final double productionRatePerDay;
  final double estimatedDays;
  final double rawMaterialAdjustedRate;
  final bool canFulfill;

  FeasibilityBreakdown({
    required this.requiredUnits,
    required this.inventoryAvailable,
    required this.unitsToProduce,
    required this.productionRatePerDay,
    required this.estimatedDays,
    required this.rawMaterialAdjustedRate,
    required this.canFulfill,
  });

  factory FeasibilityBreakdown.fromJson(Map<String, dynamic> json) {
    return FeasibilityBreakdown(
      requiredUnits: (json['required_units'] as num?)?.toInt() ?? 0,
      inventoryAvailable: (json['inventory_available'] as num?)?.toInt() ?? 0,
      unitsToProduce: (json['units_to_produce'] as num?)?.toInt() ?? 0,
      productionRatePerDay: (json['production_rate_per_day'] as num?)?.toDouble() ?? 0.0,
      estimatedDays: (json['estimated_days'] as num?)?.toDouble() ?? 0.0,
      rawMaterialAdjustedRate: (json['raw_material_adjusted_rate'] as num?)?.toDouble() ?? 0.0,
      canFulfill: json['can_fulfill'] as bool? ?? false,
    );
  }
}

class FeasibilityReport {
  final bool canFulfillOnTime;
  final String statusEmoji;
  final String statusLabel;
  final String summary;
  final FeasibilityBreakdown breakdown;
  final String recommendedResponse;
  final String? splitDeliverySuggestion;

  FeasibilityReport({
    required this.canFulfillOnTime,
    required this.statusEmoji,
    required this.statusLabel,
    required this.summary,
    required this.breakdown,
    required this.recommendedResponse,
    this.splitDeliverySuggestion,
  });

  factory FeasibilityReport.fromJson(Map<String, dynamic> json) {
    return FeasibilityReport(
      canFulfillOnTime: json['can_fulfill_on_time'] as bool? ?? false,
      statusEmoji: json['status_emoji'] as String? ?? '❓',
      statusLabel: json['status_label'] as String? ?? 'Unknown',
      summary: json['summary'] as String? ?? '',
      breakdown: FeasibilityBreakdown.fromJson(json['breakdown'] as Map<String, dynamic>? ?? {}),
      recommendedResponse: json['recommended_response'] as String? ?? '',
      splitDeliverySuggestion: json['split_delivery_suggestion'] as String?,
    );
  }
}
