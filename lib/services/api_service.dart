import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import '../config.dart';
import '../models/product.dart';
import '../models/buyer.dart';
import '../models/enquiry.dart';
import '../models/catalog_model.dart';
import '../models/notification_item.dart';

class BuyerEnquiry {
  final String id;
  final String buyerName;
  final String channel;
  final String message;
  final String productDescription;
  final double productPrice;
  final DateTime receivedAt;

  const BuyerEnquiry({
    required this.id,
    required this.buyerName,
    required this.channel,
    required this.message,
    required this.productDescription,
    required this.productPrice,
    required this.receivedAt,
  });
}

/// Single point of contact with the backend (FastAPI backend + AI pipeline).
class ApiService {
  ApiService._() {
    _mockEnquiries.addAll([
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

  final List<BuyerEnquiry> _mockEnquiries = [];
  List<BuyerEnquiry> get enquiries => List.unmodifiable(_mockEnquiries);

  // In-progress Add Product draft, kept so the artisan can resume if
  // they leave mid-flow (e.g. via the Home button) instead of losing
  // their photo/voice note/price. Session-only.
  ProductDraft? _savedDraft;
  ProductDraft? get savedDraft => _savedDraft;
  void saveDraft(ProductDraft draft) => _savedDraft = draft;
  void clearDraft() => _savedDraft = null;

  void setAuthToken(String token) {
    AppConfig.authToken = token;
  }

  Map<String, String> get _headers => {
        'Authorization': 'Bearer ${AppConfig.authToken}',
        'Content-Type': 'application/json',
      };

  // =========================================================================
  // Product Creation & AI Pipeline
  // =========================================================================

  Future<Product> processNewProduct(ProductDraft draft) {
    return AppConfig.useMockApi ? _mockProcessNewProduct(draft) : _realProcessNewProduct(draft);
  }

  Future<Product> _mockProcessNewProduct(ProductDraft draft) async {
    await Future.delayed(const Duration(seconds: 3));

    final materialCost = draft.rawMaterialCost;
    final labour = materialCost * 0.6;
    final marketAdjustment = 120 + Random().nextInt(80);
    final suggestedPrice = materialCost + labour + marketAdjustment;

    return Product(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      image: draft.photo,
      imageBytes: draft.photoBytes,
      descriptionHi: 'हाथ से बनी पारंपरिक कलाकृति, प्राकृतिक रंगों और स्थानीय शिल्प कौशल से तैयार।',
      descriptionEn: 'Handcrafted traditional piece made with natural colors and local artisan skill.',
      voiceTranscription: 'यह हस्तनिर्मित पारंपरिक वस्तु प्राकृतिक सामग्री से तैयार की गई है।',
      translatedVoiceText: 'This handmade traditional piece was crafted using natural materials.',
      price: suggestedPrice.roundToDouble(),
      priceReason: 'Cost ₹${materialCost.round()} + labour + market rate for similar items',
    );
  }

  Future<Product> _realProcessNewProduct(ProductDraft draft) async {
    const baseUrl = AppConfig.apiBaseUrl;

    // 1. Create Product
    final createUri = Uri.parse('$baseUrl/products');
    final createBody = jsonEncode({
      'name': 'Artisan Craft',
      'raw_material_cost': draft.rawMaterialCost,
      'labour_cost': (draft.rawMaterialCost * 0.4).roundToDouble(),
      'packaging_cost': 20.0,
      'category': 'Handicraft',
      'material': 'Traditional Materials',
    });

    final createResp = await http.post(createUri, headers: _headers, body: createBody);
    if (createResp.statusCode != 201 && createResp.statusCode != 200) {
      throw Exception('Failed to create product record: ${createResp.statusCode} ${createResp.body}');
    }
    final createdData = jsonDecode(createResp.body) as Map<String, dynamic>;
    final int productId = createdData['id'] as int;

    // 2. Upload image if available
    String? uploadedImageUrl;
    try {
      if (draft.photoBytes != null || draft.photo != null) {
        final uploadUri = Uri.parse('$baseUrl/products/$productId/images');
        final uploadReq = http.MultipartRequest('POST', uploadUri)
          ..headers['Authorization'] = 'Bearer ${AppConfig.authToken}';

        if (draft.photoBytes != null) {
          final filename = draft.photoName ?? 'photo.jpg';
          uploadReq.files.add(
            http.MultipartFile.fromBytes('file', draft.photoBytes!, filename: filename),
          );
        } else if (draft.photo != null && !kIsWeb) {
          uploadReq.files.add(
            await http.MultipartFile.fromPath('file', draft.photo!.path),
          );
        }

        final streamed = await uploadReq.send();
        final uploadResp = await http.Response.fromStream(streamed);
        if (uploadResp.statusCode == 201 || uploadResp.statusCode == 200) {
          final imgData = jsonDecode(uploadResp.body) as Map<String, dynamic>;
          uploadedImageUrl = imgData['original_url'] as String?;
        }
      }
    } catch (_) {}

    // 3. Upload voice recording if available
    String? uploadedAudioUrl;
    try {
      if (draft.audioBytes != null || (draft.audioPath != null && !kIsWeb)) {
        final audioUri = Uri.parse('$baseUrl/products/$productId/audio');
        final audioReq = http.MultipartRequest('POST', audioUri)
          ..headers['Authorization'] = 'Bearer ${AppConfig.authToken}'
          ..fields['language'] = draft.language
          ..fields['duration'] = (draft.audioDuration ?? 5.0).toString();

        if (draft.audioBytes != null) {
          final filename = draft.audioName ?? 'voice_note.m4a';
          audioReq.files.add(
            http.MultipartFile.fromBytes('file', draft.audioBytes!, filename: filename),
          );
        } else if (draft.audioPath != null && !kIsWeb) {
          audioReq.files.add(
            await http.MultipartFile.fromPath('file', draft.audioPath!),
          );
        }

        final streamedAudio = await audioReq.send();
        final audioResp = await http.Response.fromStream(streamedAudio);
        if (audioResp.statusCode == 201 || audioResp.statusCode == 200) {
          final audioData = jsonDecode(audioResp.body) as Map<String, dynamic>;
          uploadedAudioUrl = audioData['audio_url'] as String?;
        }
      }
    } catch (_) {}

    // 4. Process AI enhancements & pricing
    final processUri = Uri.parse('$baseUrl/products/$productId/process');
    final processBody = jsonEncode({
      'voice_text': draft.audioPath != null ? 'Handcrafted traditional artisan craft' : null,
      'language': draft.language,
    });

    final processResp = await http.post(processUri, headers: _headers, body: processBody);
    if (processResp.statusCode != 200) {
      throw Exception('AI processing failed: ${processResp.statusCode} ${processResp.body}');
    }

    final processData = jsonDecode(processResp.body) as Map<String, dynamic>;
    final productObj = processData['product'] as Map<String, dynamic>? ?? createdData;
    final pricingObj = processData['pricing'] as Map<String, dynamic>?;

    final String descEn = productObj['description_en'] ?? productObj['name'] ?? 'Handcrafted traditional piece';
    final String descHi = productObj['description_hi'] ?? 'हाथ से बनी पारंपरिक कलाकृति';
    final String? voiceTrans = productObj['voice_transcription'];
    final String? transVoice = productObj['translated_voice_text'];

    final double price = pricingObj != null
        ? (pricingObj['recommended_price'] as num).toDouble()
        : (draft.rawMaterialCost * 1.75);
    final String priceReason = pricingObj != null
        ? (pricingObj['reason'] as String? ?? 'Cost + labour + market rate')
        : 'Cost ₹${draft.rawMaterialCost.toInt()} + labour + margin';

    if (uploadedImageUrl == null) {
      final images = productObj['images'] as List?;
      if (images != null && images.isNotEmpty) {
        uploadedImageUrl = images.last['original_url'] as String?;
      }
    }

    final resultProduct = Product(
      id: productId.toString(),
      image: draft.photo,
      imageBytes: draft.photoBytes,
      imageUrl: uploadedImageUrl,
      descriptionHi: descHi,
      descriptionEn: descEn,
      voiceTranscription: voiceTrans,
      translatedVoiceText: transVoice,
      audioUrl: uploadedAudioUrl,
      price: price,
      priceReason: priceReason,
    );

    return resultProduct;
  }

  // =========================================================================
  // Product Catalog CRUD
  // =========================================================================

  Future<List<Product>> fetchCatalog({String? artisanId}) async {
    if (AppConfig.useMockApi) {
      return catalog;
    }

    try {
      final uri = Uri.parse('${AppConfig.apiBaseUrl}/products');
      final resp = await http.get(uri, headers: _headers);

      if (resp.statusCode == 200) {
        final list = jsonDecode(resp.body) as List;
        _catalog.clear();
        for (final item in list) {
          final m = item as Map<String, dynamic>;
          final prices = m['prices'] as List?;
          final images = m['images'] as List?;
          final audioRecordings = m['audio_recordings'] as List?;

          double price = 0;
          String priceReason = '';
          if (prices != null && prices.isNotEmpty) {
            final latestPrice = prices.first as Map<String, dynamic>;
            price = (latestPrice['recommended_price'] as num).toDouble();
            priceReason = latestPrice['reason'] as String? ?? '';
          } else {
            final raw = (m['raw_material_cost'] as num?)?.toDouble() ?? 100.0;
            final labour = (m['labour_cost'] as num?)?.toDouble() ?? 40.0;
            final packaging = (m['packaging_cost'] as num?)?.toDouble() ?? 20.0;
            price = (raw + labour + packaging) * 1.75;
            priceReason = 'Cost ₹${raw.toInt()} + labour + margin';
          }

          String? imageUrl;
          if (images != null && images.isNotEmpty) {
            imageUrl = images.first['original_url'] as String?;
          }

          String? audioUrl;
          if (audioRecordings != null && audioRecordings.isNotEmpty) {
            audioUrl = audioRecordings.first['audio_url'] as String?;
          }

          _catalog.add(
            Product(
              id: m['id'].toString(),
              imageUrl: imageUrl,
              descriptionHi: m['description_hi'] ?? '',
              descriptionEn: m['description_en'] ?? m['name'] ?? '',
              voiceTranscription: m['voice_transcription'],
              translatedVoiceText: m['translated_voice_text'],
              audioUrl: audioUrl,
              price: price,
              priceReason: priceReason,
            ),
          );
        }
      }
    } catch (_) {}
    return catalog;
  }

  Future<void> publish(Product product) async {
    final existingIndex = _catalog.indexWhere((p) => p.id == product.id);
    if (existingIndex >= 0) {
      _catalog[existingIndex] = product;
    } else {
      _catalog.insert(0, product);
    }
    _maybeGenerateEnquiry(product);

    if (!AppConfig.useMockApi) {
      try {
        final uri = Uri.parse('${AppConfig.apiBaseUrl}/products/${product.id}/publish');
        await http.post(uri, headers: _headers);
      } catch (_) {}
    }
  }

  void updateProduct(Product updated) {
    final index = _catalog.indexWhere((p) => p.id == updated.id);
    if (index != -1) {
      _catalog[index] = updated;
    }
    if (!AppConfig.useMockApi) {
      try {
        final intId = int.tryParse(updated.id);
        if (intId != null) {
          final uri = Uri.parse('${AppConfig.apiBaseUrl}/products/$intId');
          http.put(
            uri,
            headers: _headers,
            body: jsonEncode({
              'description_en': updated.descriptionEn,
              'description_hi': updated.descriptionHi,
            }),
          );
        }
      } catch (_) {}
    }
  }

  void deleteProduct(String id) {
    _catalog.removeWhere((p) => p.id == id);
    if (!AppConfig.useMockApi) {
      try {
        final intId = int.tryParse(id);
        if (intId != null) {
          final uri = Uri.parse('${AppConfig.apiBaseUrl}/products/$intId');
          http.delete(uri, headers: _headers);
        }
      } catch (_) {}
    }
  }

  // =========================================================================
  // B2B Wholesale Buyers & Match Linkage
  // =========================================================================

  Future<List<Buyer>> fetchBuyers({String? category, String? location}) async {
    if (AppConfig.useMockApi) {
      return [
        Buyer(
          id: 1,
          name: 'Rajesh Sharma',
          company: 'EcoCraft Wholesale',
          location: 'Mumbai',
          category: 'Home Decor',
          description: 'Large-scale distributor for sustainable bamboo and cane home decor.',
          phone: '+91-98200-11223',
          email: 'procurement@ecocraft-demo.in',
        ),
        Buyer(
          id: 2,
          name: 'Pooja Verma',
          company: 'Indian Handicraft Retail',
          location: 'Delhi',
          category: 'Handicrafts',
          description: 'Procures handcrafted decorative items and regional folk art.',
          phone: '+91-98111-44556',
          email: 'buyers@indianhandicraft-demo.com',
        ),
      ];
    }

    try {
      final queryParams = <String, String>{};
      if (category != null && category.isNotEmpty) queryParams['category'] = category;
      if (location != null && location.isNotEmpty) queryParams['location'] = location;

      final uri = Uri.parse('${AppConfig.apiBaseUrl}/buyers').replace(queryParameters: queryParams.isNotEmpty ? queryParams : null);
      final resp = await http.get(uri, headers: _headers);

      if (resp.statusCode == 200) {
        final list = jsonDecode(resp.body) as List;
        return list.map((item) => Buyer.fromJson(item as Map<String, dynamic>)).toList();
      }
    } catch (_) {}
    return [];
  }

  Future<List<BuyerMatch>> fetchMatchingBuyers(String productId) async {
    if (AppConfig.useMockApi) {
      final buyers = await fetchBuyers();
      return buyers
          .map((b) => BuyerMatch(
                buyer: b,
                score: 90,
                matchReason: 'Direct match for artisan craft category',
              ))
          .toList();
    }

    try {
      final uri = Uri.parse('${AppConfig.apiBaseUrl}/products/$productId/buyers');
      final resp = await http.get(uri, headers: _headers);

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        final list = data['buyers'] as List? ?? [];
        return list.map((item) => BuyerMatch.fromJson(item as Map<String, dynamic>)).toList();
      }
    } catch (_) {}
    return [];
  }

  Future<Enquiry> sendEnquiry({
    required int buyerId,
    required int productId,
    required String message,
  }) async {
    if (AppConfig.useMockApi) {
      return Enquiry(
        id: DateTime.now().millisecondsSinceEpoch,
        buyerId: buyerId,
        productId: productId,
        buyerCompany: 'EcoCraft Wholesale',
        productName: 'Artisan Craft',
        message: message,
        status: 'pending',
        createdAt: DateTime.now(),
      );
    }

    final uri = Uri.parse('${AppConfig.apiBaseUrl}/buyers/$buyerId/enquiries');
    final body = jsonEncode({
      'product_id': productId,
      'message': message,
    });

    final resp = await http.post(uri, headers: _headers, body: body);
    if (resp.statusCode == 201 || resp.statusCode == 200) {
      return Enquiry.fromJson(jsonDecode(resp.body) as Map<String, dynamic>);
    } else {
      throw Exception('Failed to send enquiry: ${resp.statusCode} ${resp.body}');
    }
  }

  // =========================================================================
  // Wholesale Enquiries Tracking
  // =========================================================================

  Future<List<Enquiry>> fetchEnquiries() async {
    if (AppConfig.useMockApi) {
      return [
        Enquiry(
          id: 1,
          buyerId: 1,
          productId: 1,
          buyerCompany: 'EcoCraft Wholesale',
          productName: 'Handmade Bamboo Basket',
          message: 'Interested in bulk procurement of 100 units for festive hampers.',
          status: 'pending',
          createdAt: DateTime.now().subtract(const Duration(hours: 3)),
        ),
      ];
    }

    try {
      final uri = Uri.parse('${AppConfig.apiBaseUrl}/enquiries');
      final resp = await http.get(uri, headers: _headers);

      if (resp.statusCode == 200) {
        final list = jsonDecode(resp.body) as List;
        return list.map((item) => Enquiry.fromJson(item as Map<String, dynamic>)).toList();
      }
    } catch (_) {}
    return [];
  }

  Future<Enquiry> respondToEnquiry({
    required int enquiryId,
    required String status,
    String? artisanResponse,
  }) async {
    if (AppConfig.useMockApi) {
      return Enquiry(
        id: enquiryId,
        buyerId: 1,
        productId: 1,
        buyerCompany: 'EcoCraft Wholesale',
        productName: 'Artisan Craft',
        message: 'Bulk order enquiry',
        status: status,
        artisanResponse: artisanResponse,
        createdAt: DateTime.now(),
        respondedAt: DateTime.now(),
      );
    }

    final uri = Uri.parse('${AppConfig.apiBaseUrl}/enquiries/$enquiryId');
    final body = jsonEncode({
      'status': status,
      if (artisanResponse != null) 'artisan_response': artisanResponse,
    });

    final resp = await http.put(uri, headers: _headers, body: body);
    if (resp.statusCode == 200) {
      return Enquiry.fromJson(jsonDecode(resp.body) as Map<String, dynamic>);
    } else {
      throw Exception('Failed to update enquiry: ${resp.statusCode} ${resp.body}');
    }
  }

  // =========================================================================
  // Digital Catalogs & Collections
  // =========================================================================

  Future<List<CatalogModel>> fetchCatalogs() async {
    if (AppConfig.useMockApi) {
      return [
        CatalogModel(
          id: 1,
          title: 'Festive Bamboo Collection',
          description: 'Curated eco-friendly handcrafted baskets and lamps',
          status: 'published',
          products: catalog,
          createdAt: DateTime.now(),
        ),
      ];
    }

    try {
      final uri = Uri.parse('${AppConfig.apiBaseUrl}/catalogs');
      final resp = await http.get(uri, headers: _headers);

      if (resp.statusCode == 200) {
        final list = jsonDecode(resp.body) as List;
        return list.map((item) => CatalogModel.fromJson(item as Map<String, dynamic>)).toList();
      }
    } catch (_) {}
    return [];
  }

  Future<CatalogModel> createCatalog({required String title, String? description}) async {
    if (AppConfig.useMockApi) {
      return CatalogModel(
        id: DateTime.now().millisecondsSinceEpoch,
        title: title,
        description: description,
        status: 'draft',
        products: [],
        createdAt: DateTime.now(),
      );
    }

    final uri = Uri.parse('${AppConfig.apiBaseUrl}/catalogs');
    final body = jsonEncode({
      'title': title,
      if (description != null) 'description': description,
    });

    final resp = await http.post(uri, headers: _headers, body: body);
    if (resp.statusCode == 201 || resp.statusCode == 200) {
      return CatalogModel.fromJson(jsonDecode(resp.body) as Map<String, dynamic>);
    } else {
      throw Exception('Failed to create catalog: ${resp.statusCode} ${resp.body}');
    }
  }

  Future<CatalogModel> publishCatalog(int catalogId) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/catalogs/$catalogId/publish');
    final resp = await http.post(uri, headers: _headers);
    if (resp.statusCode == 200) {
      return CatalogModel.fromJson(jsonDecode(resp.body) as Map<String, dynamic>);
    } else {
      throw Exception('Failed to publish catalog: ${resp.statusCode} ${resp.body}');
    }
  }

  Future<void> addProductToCatalog(int catalogId, int productId) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/catalogs/$catalogId/products/$productId');
    await http.post(uri, headers: _headers);
  }

  // =========================================================================
  // Public Marketplace
  // =========================================================================

  Future<List<Product>> fetchMarketplaceProducts({String? category}) async {
    try {
      final queryParams = <String, String>{};
      if (category != null && category.isNotEmpty) queryParams['category'] = category;

      final uri = Uri.parse('${AppConfig.apiBaseUrl}/marketplace/products')
          .replace(queryParameters: queryParams.isNotEmpty ? queryParams : null);
      final resp = await http.get(uri);

      if (resp.statusCode == 200) {
        final list = jsonDecode(resp.body) as List;
        final List<Product> result = [];
        for (final item in list) {
          final m = item as Map<String, dynamic>;
          final prices = m['prices'] as List?;
          final images = m['images'] as List?;
          double price = 0;
          String priceReason = '';
          if (prices != null && prices.isNotEmpty) {
            final latestPrice = prices.first as Map<String, dynamic>;
            price = (latestPrice['recommended_price'] as num).toDouble();
            priceReason = latestPrice['reason'] as String? ?? '';
          }
          String? imageUrl;
          if (images != null && images.isNotEmpty) {
            imageUrl = images.first['original_url'] as String?;
          }
          result.add(
            Product(
              id: m['id'].toString(),
              imageUrl: imageUrl,
              descriptionHi: m['description_hi'] ?? '',
              descriptionEn: m['description_en'] ?? m['name'] ?? '',
              voiceTranscription: m['voice_transcription'],
              translatedVoiceText: m['translated_voice_text'],
              price: price,
              priceReason: priceReason,
            ),
          );
        }
        return result;
      }
    } catch (_) {}
    return fetchCatalog();
  }

  Future<List<CatalogModel>> fetchMarketplaceCatalogs() async {
    try {
      final uri = Uri.parse('${AppConfig.apiBaseUrl}/marketplace/catalogs');
      final resp = await http.get(uri);

      if (resp.statusCode == 200) {
        final list = jsonDecode(resp.body) as List;
        return list.map((item) => CatalogModel.fromJson(item as Map<String, dynamic>)).toList();
      }
    } catch (_) {}
    return fetchCatalogs();
  }

  // =========================================================================
  // In-App Notifications
  // =========================================================================

  Future<List<NotificationItem>> fetchNotifications() async {
    if (AppConfig.useMockApi) {
      return [
        NotificationItem(
          id: 1,
          type: 'new_enquiry',
          title: 'New Wholesale Enquiry',
          message: 'EcoCraft Wholesale is interested in your Handwoven Basket.',
          isRead: false,
          createdAt: DateTime.now().subtract(const Duration(minutes: 45)),
        ),
      ];
    }

    try {
      final uri = Uri.parse('${AppConfig.apiBaseUrl}/notifications');
      final resp = await http.get(uri, headers: _headers);

      if (resp.statusCode == 200) {
        final decoded = jsonDecode(resp.body);
        // Backend returns { notifications: [...], total: N, unread_count: N }
        final List list;
        if (decoded is Map<String, dynamic> && decoded.containsKey('notifications')) {
          list = decoded['notifications'] as List;
        } else if (decoded is List) {
          list = decoded;
        } else {
          return [];
        }
        return list.map((item) => NotificationItem.fromJson(item as Map<String, dynamic>)).toList();
      }
    } catch (_) {}
    return [];
  }

  Future<int> fetchUnreadNotificationCount() async {
    if (AppConfig.useMockApi) return 1;

    try {
      final uri = Uri.parse('${AppConfig.apiBaseUrl}/notifications/unread-count');
      final resp = await http.get(uri, headers: _headers);

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        return (data['count'] ?? data['unread_count']) as int? ?? 0;
      }
    } catch (_) {}
    return 0;
  }

  Future<void> markAllNotificationsRead() async {
    if (AppConfig.useMockApi) return;

    try {
      final uri = Uri.parse('${AppConfig.apiBaseUrl}/notifications/read-all');
      await http.put(uri, headers: _headers);
    } catch (_) {}
  }

  // Mock buyer interest generator
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
    _mockEnquiries.insert(
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
