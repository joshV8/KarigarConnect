import 'package:flutter/material.dart';

/// Singleton that holds the selected language and notifies listeners.
class AppLanguage extends ChangeNotifier {
  static final AppLanguage instance = AppLanguage._();
  AppLanguage._();

  /// 'en' or 'hi'
  String _locale = 'en';

  String get locale => _locale;
  bool get isHindi => _locale == 'hi';
  bool get isEnglish => _locale == 'en';

  void setLanguage(String code) {
    _locale = code;
    notifyListeners();
  }
}

/// All UI strings in both languages. Access via S.get('key').
class S {
  static bool get isHindi => AppLanguage.instance.isHindi;
  static bool get isEnglish => AppLanguage.instance.isEnglish;

  static String get(String key) {
    final lang = AppLanguage.instance.locale;
    final map = lang == 'hi' ? _hi : _en;
    return map[key] ?? _en[key] ?? key;
  }

  // ---------- English ----------
  static const Map<String, String> _en = {
    // Language Select
    'choose_language': 'Choose your language',

    // Login
    'login_title': 'Log in',
    'phone_hint': 'Phone number',
    'send_otp': 'Send OTP',
    'verify': 'Verify',

    // Home / Nav
    'app_title': 'KarigarConnect',
    'catalog_tooltip': 'Catalog',
    'notifications_tooltip': 'Notifications',
    'nav_shop': 'Shop',
    'nav_buyers': 'Buyers',
    'nav_deals': 'Deals',
    'nav_market': 'Market',
    'add_product': 'Add product',
    'wholesale_buyers': 'Wholesale Buyers',
    'active_deals': 'Active Deals',
    'digital_catalog': 'My Collections',
    'public_market': 'Public Market',
    'my_products': 'My Products',
    'view_all': 'View all',
    'no_products': 'No products added yet',
    'find_buyers': 'Find Buyers',

    // Add Product
    'add_product_title': 'Add product',
    'take_photo': 'Take a photo',
    'photo_saved': 'Photo selected',
    'record_voice': 'Tap to record voice description',
    'recording_started': 'Recording...',
    'recording_stopped': 'Voice recorded',
    'play_voice': 'Voice note attached',
    'material_cost': 'Raw material cost (₹)',
    'material_cost_hint': 'e.g. 350',
    'generate_btn': 'Analyze with AI',
    'fill_all_fields': 'Please add a photo and material cost',

    // Processing
    'processing_title': 'AI is analyzing your craft...',
    'processing_subtitle': 'Removing background, writing bilingual descriptions, generating SEO tags, and calculating fair market pricing.',

    // Preview
    'preview_title': 'Product Preview',
    'original_voice': 'Artisan Voice Note',
    'ai_translation': 'AI Translation',
    'description_hi': 'Hindi Description (विवरण)',
    'description_en': 'English Description',
    'suggested_price': 'Fair Market Price',
    'find_buyers_btn': 'Find Buyers',
    'publish': 'Publish Listing',

    // Catalog
    'catalog_title': 'Product Catalog',
    'new_collection': 'New Collection',
    'title_label': 'Collection Title',
    'title_hint': 'e.g. Festive Brass Ware',
    'description_label': 'Description (optional)',
    'cancel': 'Cancel',
    'create': 'Create',
    'collection_created': 'Collection created successfully',
    'add_to_collection': 'Add to',
    'no_products_available': 'No products available to add',
    'product_added': 'Product added to collection',
    'add_btn': 'Add',
    'publish_btn': 'Publish to Market',
    'published_to_marketplace': 'Published to public marketplace',
    'all_items': 'All Products',
    'digital_collections': 'Collections',
    'no_items': 'No products in catalog yet',
    'no_collections': 'No collections created yet',
    'create_collection': 'Create First Collection',
    'items_included': 'items included',

    // Buyers
    'buyers_title': 'Wholesale Buyers',
    'verified_buyers': 'Verified B2B Buyers',
    'all_categories': 'All Categories',
    'match_score': 'Match Score',
    'send_proposal': 'Send Proposal',
    'proposal_dialog_title': 'Send Wholesale Proposal',
    'proposal_msg_hint': 'Describe your production capacity, lead time, and bulk discount...',
    'send_btn': 'Send Proposal',
    'proposal_sent': 'Proposal sent to buyer!',
    'no_buyers': 'No wholesale buyers found for this category',

    // Deals / Enquiries
    'deals_title': 'Wholesale Deals',
    'deal_status_pending': 'Pending',
    'deal_status_contacted': 'Contacted',
    'deal_status_accepted': 'Accepted',
    'deal_status_rejected': 'Rejected',
    'accept_deal': 'Accept Deal',
    'reject_deal': 'Decline',
    'response_hint': 'Enter message or counter-offer for the buyer...',
    'submit_response': 'Submit Response',
    'deal_updated': 'Deal status updated',
    'no_deals': 'No active wholesale enquiries yet',

    // Marketplace
    'marketplace_title': 'Public Marketplace',
    'browse_products': 'Products',
    'browse_collections': 'Curated Collections',
    'no_market_products': 'No items currently published in the marketplace',
    'no_market_collections': 'No public collections available',

    // Notifications
    'notifications_title': 'Notifications',
    'mark_all_read': 'Mark all as read',
    'no_notifications': 'No notifications right now',
  };

  // ---------- Hindi ----------
  static const Map<String, String> _hi = {
    // Language Select
    'choose_language': 'अपनी भाषा चुनें',

    // Login
    'login_title': 'लॉगिन करें',
    'phone_hint': 'फ़ोन नंबर दर्ज करें',
    'send_otp': 'OTP भेजें',
    'verify': 'सत्यापित करें',

    // Home / Nav
    'app_title': 'कारीगर कनेक्ट',
    'catalog_tooltip': 'कैटलॉग',
    'notifications_tooltip': 'सूचनाएं',
    'nav_shop': 'दुकान',
    'nav_buyers': 'खरीदार',
    'nav_deals': 'सौदा',
    'nav_market': 'बाज़ार',
    'add_product': 'नया सामान जोड़ें',
    'wholesale_buyers': 'थोक खरीदार',
    'active_deals': 'सक्रिय सौदे',
    'digital_catalog': 'मेरे संग्रह',
    'public_market': 'सार्वजनिक बाज़ार',
    'my_products': 'मेरा सामान',
    'view_all': 'सभी देखें',
    'no_products': 'अभी कोई सामान नहीं जोड़ा गया',
    'find_buyers': 'खरीदार खोजें',

    // Add Product
    'add_product_title': 'नया सामान जोड़ें',
    'take_photo': 'तस्वीर लें',
    'photo_saved': 'तस्वीर चुनी गई',
    'record_voice': 'आवाज़ में बताएं (रिकॉर्ड करें)',
    'recording_started': 'रिकॉर्डिंग जारी है...',
    'recording_stopped': 'आवाज़ रिकॉर्ड हो गई',
    'play_voice': 'आवाज़ संदेश संलग्न है',
    'material_cost': 'कच्चे माल की लागत (₹)',
    'material_cost_hint': 'उदा. 350',
    'generate_btn': 'AI से तैयार करें',
    'fill_all_fields': 'कृपया तस्वीर और लागत दर्ज करें',

    // Processing
    'processing_title': 'AI आपके शिल्प का विश्लेषण कर रहा है...',
    'processing_subtitle': 'पृष्ठभूमि हटाना, दोनों भाषाओं में विवरण लिखना, और सही बाज़ार मूल्य तय करना।',

    // Preview
    'preview_title': 'सामान का पूर्वावलोकन',
    'original_voice': 'आपकी मूल आवाज़',
    'ai_translation': 'AI अनुवाद',
    'description_hi': 'हिंदी विवरण',
    'description_en': 'अंग्रेज़ी विवरण (English)',
    'suggested_price': 'उचित बाज़ार मूल्य',
    'find_buyers_btn': 'खरीदार खोजें',
    'publish': 'कैटलॉग में प्रकाशित करें',

    // Catalog
    'catalog_title': 'उत्पाद कैटलॉग',
    'new_collection': 'नया संग्रह',
    'title_label': 'संग्रह का नाम',
    'title_hint': 'उदा. दिवाली मिट्टी के दीये',
    'description_label': 'विवरण (वैकल्पिक)',
    'cancel': 'रद्द करें',
    'create': 'बनाएं',
    'collection_created': 'नया संग्रह सफलतापूर्वक बन गया',
    'add_to_collection': 'संग्रह में जोड़ें',
    'no_products_available': 'जोड़ने के लिए कोई सामान उपलब्ध नहीं है',
    'product_added': 'सामान संग्रह में जोड़ा गया',
    'add_btn': 'जोड़ें',
    'publish_btn': 'बाज़ार में प्रकाशित करें',
    'published_to_marketplace': 'सार्वजनिक बाज़ार में प्रकाशित हो गया',
    'all_items': 'सभी सामान',
    'digital_collections': 'डिजिटल संग्रह',
    'no_items': 'कैटलॉग में अभी कोई सामान नहीं है',
    'no_collections': 'अभी कोई संग्रह नहीं बनाया गया',
    'create_collection': 'पहला संग्रह बनाएं',
    'items_included': 'सामान शामिल हैं',

    // Buyers
    'buyers_title': 'थोक खरीदार',
    'verified_buyers': 'सत्यापित B2B खरीदार',
    'all_categories': 'सभी श्रेणियां',
    'match_score': 'मैच स्कोर',
    'send_proposal': 'प्रस्ताव भेजें',
    'proposal_dialog_title': 'थोक प्रस्ताव भेजें',
    'proposal_msg_hint': 'अपनी क्षमता, डिलीवरी का समय और थोक छूट लिखें...',
    'send_btn': 'प्रस्ताव भेजें',
    'proposal_sent': 'खरीदार को प्रस्ताव भेज दिया गया!',
    'no_buyers': 'इस श्रेणी के लिए कोई खरीदार नहीं मिला',

    // Deals / Enquiries
    'deals_title': 'थोक सौदे व पूछताछ',
    'deal_status_pending': 'लंबित',
    'deal_status_contacted': 'संपर्क किया',
    'deal_status_accepted': 'स्वीकृत',
    'deal_status_rejected': 'अस्वीकृत',
    'accept_deal': 'सौदा स्वीकार करें',
    'reject_deal': 'अस्वीकार करें',
    'response_hint': 'खरीदार के लिए संदेश या काउंटर-ऑफ़र लिखें...',
    'submit_response': 'जवाब भेजें',
    'deal_updated': 'सौदे की स्थिति अपडेट हो गई',
    'no_deals': 'अभी कोई सक्रिय थोक पूछताछ नहीं है',

    // Marketplace
    'marketplace_title': 'सार्वजनिक बाज़ार',
    'browse_products': 'सामान',
    'browse_collections': 'डिजिटल संग्रह',
    'no_market_products': 'बाज़ार में अभी कोई सामान प्रकाशित नहीं है',
    'no_market_collections': 'कोई सार्वजनिक संग्रह उपलब्ध नहीं है',

    // Notifications
    'notifications_title': 'सूचनाएं',
    'mark_all_read': 'सभी को पढ़ा हुआ चिह्नित करें',
    'no_notifications': 'अभी कोई सूचना नहीं है',
  };
}
