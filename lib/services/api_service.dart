import 'dart:math';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../models/product.dart';

/// Single point of contact with the backend (Person 3's FastAPI +
/// Person 2's AI pipeline). See API_CONTRACT.md at the project root
/// for the exact request/response shapes expected here.
///
/// While AppConfig.useMockApi is true, everything runs against fake
/// data with a simulated delay — the whole app is demoable without
/// the real backend, and Person 2/3 can build and test their parts
/// independently against the same contract. Flip that one flag once
/// the real server is live; no screen code needs to change.
class ApiService {
  ApiService._();
  static final ApiService instance = ApiService._();

  final List<Product> _catalog = [];
  List<Product> get catalog => List.unmodifiable(_catalog);

  Future<Product> processNewProduct(ProductDraft draft) {
    return AppConfig.useMockApi ? _mockProcessNewProduct(draft) : _realProcessNewProduct(draft);
  }

  Future<Product> _mockProcessNewProduct(ProductDraft draft) async {
    await Future.delayed(const Duration(seconds: 3)); // simulate AI pipeline

    final materialCost = draft.rawMaterialCost;
    final labour = materialCost * 0.6;
    final marketAdjustment = 120 + Random().nextInt(80);
    final suggestedPrice = materialCost + labour + marketAdjustment;

    return Product(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      image: draft.photo,
      descriptionHi: 'हाथ से बनी पारंपरिक कलाकृति, स्थानीय सामग्री से तैयार।',
      descriptionEn: 'Handcrafted traditional piece, made with local materials.',
      price: suggestedPrice.roundToDouble(),
      priceReason: 'Cost ₹${materialCost.round()} + labour + market rate for similar items',
    );
  }

  /// Real implementation — wire this up once Person 3's endpoint from
  /// API_CONTRACT.md section 1 is live. Sends the photo + voice note
  /// as multipart form data and expects back the JSON shape documented
  /// there (image_url, description_hi, description_en, price, price_reason).
  Future<Product> _realProcessNewProduct(ProductDraft draft) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/products/process');
    final request = http.MultipartRequest('POST', uri)
      ..fields['raw_material_cost'] = draft.rawMaterialCost.toString();

    if (draft.photo != null) {
      request.files.add(await http.MultipartFile.fromPath('photo', draft.photo!.path));
    }
    if (draft.audioPath != null) {
      request.files.add(await http.MultipartFile.fromPath('audio', draft.audioPath!));
    }

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);

    if (response.statusCode != 200) {
      throw Exception('AI processing failed: ${response.statusCode} ${response.body}');
    }

    // TODO(person1): once Person 2/3 confirm the live response shape,
    // parse response.body (JSON) into a Product here, e.g.:
    //   final json = jsonDecode(response.body);
    //   return Product(id: json['id'] ?? ..., imageUrl: json['image_url'], ...);
    throw UnimplementedError('Parse the real AI response once /products/process is live.');
  }

  void publish(Product product) {
    _catalog.add(product);
    // TODO(person3): also POST to {apiBaseUrl}/products per
    // API_CONTRACT.md section 2 once useMockApi is false, so the
    // catalog persists server-side instead of only in memory.
  }
}
