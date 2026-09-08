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
  ApiService._() {
    // Seed a couple of enquiries so Market Linkage has something to
    // show even before the artisan has published anything.
    _enquiries.addAll([
      BuyerEnquiry(
        id: 'seed-1',
        buyerName: 'Rina Textiles, Jaipur',
        channel: 'B2B Marketplace',
        message: 'Interested in a bulk order — can you do 50 pieces?',
        productDescription: 'Handwoven jute basket',
        productPrice: 620,
        receivedAt: DateTime.now().subtract(const Duration(hours: 5)),
      ),
      BuyerEnquiry(
        id: 'seed-2',
        buyerName: 'Direct Buyer · Ananya S.',
        channel: 'Direct Buyer',
        message: 'क्या थोक ऑर्डर के लिए छूट मिल सकती है?',
        productDescription: 'Blue pottery vase',
        productPrice: 850,
        receivedAt: DateTime.now().subtract(const Duration(days: 1)),
      ),
    ]);
  }
  static final ApiService instance = ApiService._();

  final List<Product> _catalog = [];
  List<Product> get catalog => List.unmodifiable(_catalog);

  final List<BuyerEnquiry> _enquiries = [];
  List<BuyerEnquiry> get enquiries => List.unmodifiable(_enquiries);

  // In-progress Add Product draft, kept so the artisan can resume if
  // they leave mid-flow (e.g. via the Home button) instead of losing
  // their photo/voice note/price. Session-only — not persisted across
  // app restarts.
  ProductDraft? _savedDraft;
  ProductDraft? get savedDraft => _savedDraft;
  void saveDraft(ProductDraft draft) => _savedDraft = draft;
  void clearDraft() => _savedDraft = null;

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
    _maybeGenerateEnquiry(product);
    // TODO(person3): also POST to {apiBaseUrl}/products per
    // API_CONTRACT.md section 2 once useMockApi is false, so the
    // catalog persists server-side instead of only in memory.
  }

  void updateProduct(Product updated) {
    final index = _catalog.indexWhere((p) => p.id == updated.id);
    if (index != -1) _catalog[index] = updated;
    // TODO(person3): PATCH {apiBaseUrl}/products/{id} once live.
  }

  void deleteProduct(String id) {
    _catalog.removeWhere((p) => p.id == id);
    // TODO(person3): DELETE {apiBaseUrl}/products/{id} once live.
  }

  // Mock buyer interest generator — gives the Market Linkage screen
  // something believable to show as the catalog grows. Swap for real
  // enquiry data once Person 3's backend exposes it.
  static const _buyerNames = [
    'Northern Crafts Co-op',
    'Sunrise Home Decor',
    'Meera Handicrafts Export',
    'Direct Buyer · Kabir M.',
    'Direct Buyer · Priya N.',
  ];
  static const _channels = ['B2B Marketplace', 'Government e-Marketplace', 'Direct Buyer'];
  static const _messages = [
    'Loved this piece! Is customization available?',
    'Please share more photos and delivery timeline.',
    'Interested in a bulk order — can you do 50 pieces?',
    'क्या थोक ऑर्डर के लिए छूट मिल सकती है?',
    'यह कितने दिनों में डिलीवर हो सकता है?',
  ];

  void _maybeGenerateEnquiry(Product product) {
    final rand = Random();
    _enquiries.insert(
      0,
      BuyerEnquiry(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        buyerName: _buyerNames[rand.nextInt(_buyerNames.length)],
        channel: _channels[rand.nextInt(_channels.length)],
        message: _messages[rand.nextInt(_messages.length)],
        productDescription: product.descriptionEn,
        productPrice: product.price,
        receivedAt: DateTime.now(),
      ),
    );
  }
}
