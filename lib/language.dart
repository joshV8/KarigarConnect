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
    'continue_btn': 'Continue',
    'describe_it': 'Describe it',
    'recording': 'Recording...',
    'recorded': 'Recorded',
    'tap_mic': 'Tap mic to speak',
    'raw_material_cost': 'Raw material cost',

    // Processing
    'ai_preparing': 'AI is preparing your listing',

    // Preview
    'preview_title': 'Preview',
    'ai_enhanced': 'AI Enhanced',
    'original_voice': 'Original Voice',
    'ai_translation': 'AI English Translation',
    'description_hi': 'Description (Hindi)',
    'description_en': 'Description (English)',
    'suggested_price': 'Suggested price',
    'find_buyers_btn': 'Buyers',
    'publish': 'Publish',

    // Buyers
    'matched_buyers': 'Matched Buyers',
    'wholesale_buyers_title': 'Wholesale Buyers',
    'send_proposal': 'Send Proposal',
    'select_product': 'Select Product',
    'message_label': 'Message',
    'no_buyers': 'No buyers found in this category',
    'add_product_first': 'Please add a product first',
    'proposal_sent': 'Proposal sent to',

    // Enquiries
    'deals_title': 'Wholesale Deals',
    'deal_details': 'Deal Details',
    'product_label': 'Product',
    'message_prefix': 'Message:',
    'update_status': 'Update Deal Status',
    'response_note': 'Artisan Response Note',
    'response_hint': 'Enter pricing discount, bulk availability or delivery timeline...',
    'save_response': 'Save Response',
    'deal_updated': 'Deal updated successfully',
    'no_enquiries': 'No wholesale enquiries yet',
    'respond_update': 'Respond / Update',
    'your_reply': 'Your reply',

    // Marketplace
    'marketplace_title': 'Marketplace',
    'products_tab': 'Products',
    'collections_tab': 'Collections',
    'no_marketplace_products': 'No published products on marketplace yet',
    'no_published_collections': 'No published collections yet',

    // Catalog
    'catalog_title': 'Catalog',
    'new_collection': 'New Collection',
    'title_label': 'Title',
    'title_hint': 'e.g. Festive Terracotta Collection',
    'description_label': 'Description (Optional)',
    'cancel': 'Cancel',
    'collection_created': 'Collection created successfully',
    'create': 'Create',
    'no_products_available': 'No products available',
    'add_to_collection': 'Add to',
    'add_btn': 'Add',
    'product_added': 'Product added to collection',
    'published_to_marketplace': 'Published to Marketplace',
    'all_items': 'All Items',
    'digital_collections': 'Digital Collections',
    'no_items': 'No products yet',
    'no_collections': 'No collections created yet',
    'create_collection': 'Create Collection',
    'add_item': 'Add Item',
    'publish_btn': 'Publish',
    'items_included': 'Items included',

    // Notifications
    'notifications_title': 'Notifications',
    'mark_all_read': 'Mark all read',
    'no_notifications': 'No new notifications',
  };

  // ---------- Hindi ----------
  static const Map<String, String> _hi = {
    // Language Select
    'choose_language': 'अपनी भाषा चुनें',

    // Login
    'login_title': 'लॉगिन करें',
    'phone_hint': 'फ़ोन नंबर',
    'send_otp': 'OTP भेजें',
    'verify': 'जांचें',

    // Home / Nav
    'app_title': 'कारीगर कनेक्ट',
    'catalog_tooltip': 'कैटलॉग और संग्रह',
    'notifications_tooltip': 'सूचनाएं',
    'nav_shop': 'दुकान',
    'nav_buyers': 'खरीदार',
    'nav_deals': 'सौदे',
    'nav_market': 'बाज़ार',
    'add_product': 'नया सामान जोड़ें',
    'wholesale_buyers': 'थोक खरीदार',
    'active_deals': 'थोक सौदे',
    'digital_catalog': 'डिजिटल कैटलॉग',
    'public_market': 'कारीगर बाज़ार',
    'my_products': 'मेरे उत्पाद',
    'view_all': 'सब देखें',
    'no_products': 'अभी कोई सामान नहीं',
    'find_buyers': 'खरीदार खोजें',

    // Add Product
    'add_product_title': 'नया सामान',
    'take_photo': 'फोटो लें',
    'continue_btn': 'आगे बढ़ें',
    'describe_it': 'बताइए, यह क्या है?',
    'recording': 'रिकॉर्डिंग जारी है...',
    'recorded': 'रिकॉर्ड हो गया',
    'tap_mic': 'माइक दबाकर बोलें',
    'raw_material_cost': 'सामान की कीमत',

    // Processing
    'ai_preparing': 'AI तैयार कर रहा है...',

    // Preview
    'preview_title': 'पूर्वावलोकन',
    'ai_enhanced': 'AI Enhanced',
    'original_voice': 'आपकी आवाज़',
    'ai_translation': 'AI अंग्रेजी अनुवाद',
    'description_hi': 'विवरण (हिंदी)',
    'description_en': 'विवरण (अंग्रेजी)',
    'suggested_price': 'सुझाई गई कीमत',
    'find_buyers_btn': 'खरीदार खोजें',
    'publish': 'कैटलॉग में जोड़ें',

    // Buyers
    'matched_buyers': 'मैचिंग खरीदार',
    'wholesale_buyers_title': 'थोक खरीदार',
    'send_proposal': 'थोक प्रस्ताव भेजें',
    'select_product': 'सामान चुनें',
    'message_label': 'संदेश',
    'no_buyers': 'इस श्रेणी में कोई खरीदार नहीं मिला',
    'add_product_first': 'कृपया पहले सामान जोड़ें',
    'proposal_sent': 'पूछताछ सफलतापूर्वक भेजी गई!',

    // Enquiries
    'deals_title': 'थोक सौदे',
    'deal_details': 'पूछताछ विवरण',
    'product_label': 'सामान',
    'message_prefix': 'संदेश:',
    'update_status': 'स्थिति बदलें',
    'response_note': 'आपका उत्तर',
    'response_hint': 'कीमत छूट, थोक उपलब्धता या डिलीवरी समय...',
    'save_response': 'सेव करें',
    'deal_updated': 'स्थिति अपडेट हो गई!',
    'no_enquiries': 'अभी कोई पूछताछ नहीं है',
    'respond_update': 'जवाब दें / स्थिति बदलें',
    'your_reply': 'आपका उत्तर',

    // Marketplace
    'marketplace_title': 'कारीगर बाज़ार',
    'products_tab': 'सामान',
    'collections_tab': 'संग्रह',
    'no_marketplace_products': 'बाज़ार में अभी कोई सामान नहीं है',
    'no_published_collections': 'कोई सार्वजनिक संग्रह नहीं है',

    // Catalog
    'catalog_title': 'कैटलॉग और संग्रह',
    'new_collection': 'नया संग्रह',
    'title_label': 'शीर्षक',
    'title_hint': 'जैसे: उत्सव टेराकोटा संग्रह',
    'description_label': 'विवरण (वैकल्पिक)',
    'cancel': 'रद्द करें',
    'collection_created': 'संग्रह बन गया!',
    'create': 'बनाएं',
    'no_products_available': 'कोई सामान उपलब्ध नहीं है',
    'add_to_collection': 'संग्रह में जोड़ें',
    'add_btn': 'जोड़ें',
    'product_added': 'सामान जोड़ दिया गया!',
    'published_to_marketplace': 'बाज़ार में प्रकाशित हो गया!',
    'all_items': 'सभी सामान',
    'digital_collections': 'डिजिटल संग्रह',
    'no_items': 'अभी कोई सामान नहीं',
    'no_collections': 'कोई संग्रह नहीं है',
    'create_collection': 'नया संग्रह बनाएं',
    'add_item': 'सामान जोड़ें',
    'publish_btn': 'प्रकाशित करें',
    'items_included': 'सामान शामिल हैं',

    // Notifications
    'notifications_title': 'सूचनाएं',
    'mark_all_read': 'सब पढ़ें',
    'no_notifications': 'कोई नई सूचना नहीं है',
  };
}
