import '../language.dart';
import 'package:flutter/material.dart';
import '../models/buyer.dart';
import '../models/product.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/fade_slide_in.dart';

/// Screen allowing artisans to discover verified B2B wholesale buyers and dispatch proposals.
class BuyersScreen extends StatefulWidget {
  final Product? selectedProduct;
  const BuyersScreen({super.key, this.selectedProduct});

  @override
  State<BuyersScreen> createState() => _BuyersScreenState();
}

class _BuyersScreenState extends State<BuyersScreen> {
  List<Buyer> _buyers = [];
  List<BuyerMatch> _matchedBuyers = [];
  bool _loading = true;
  String? _selectedCategory;
  Product? _activeProduct;

  final List<String> _categories = [
    'All',
    'Home Decor',
    'Handicrafts',
    'Eco-Friendly Lifestyle',
    'Pottery & Terracotta',
    'Textiles & Handloom',
    'Bamboo & Wooden Craft',
    'Metal & Brass Crafts',
  ];

  @override
  void initState() {
    super.initState();
    _activeProduct = widget.selectedProduct;
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);

    if (_activeProduct != null) {
      final matches = await ApiService.instance.fetchMatchingBuyers(_activeProduct!.id);
      if (mounted) {
        setState(() {
          _matchedBuyers = matches;
          _buyers = matches.map((m) => m.buyer).toList();
          _loading = false;
        });
      }
    } else {
      final categoryFilter = _selectedCategory == 'All' ? null : _selectedCategory;
      final list = await ApiService.instance.fetchBuyers(category: categoryFilter);
      if (mounted) {
        setState(() {
          _buyers = list;
          _loading = false;
        });
      }
    }
  }

  void _showSendEnquiryDialog(Buyer buyer) {
    final catalog = ApiService.instance.catalog;
    if (catalog.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(S.get('add_product_first'))),
      );
      return;
    }

    Product selected = _activeProduct ?? catalog.first;
    final messageController = TextEditingController(
      text: S.get('proposal_greeting').replaceAll('इस सामान', '"${selected.descriptionEn}"'),
    );

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 24,
                bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(S.get('send_proposal'), style: Theme.of(context).textTheme.titleLarge),
                      IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'To: ${buyer.company} (${buyer.name}) • ${buyer.location}',
                    style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.6)),
                  ),
                  const SizedBox(height: 16),
                  Text(S.get('select_product'), style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<Product>(
                    initialValue: selected,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                    ),
                    items: catalog.map((p) {
                      return DropdownMenuItem(
                        value: p,
                        child: Text('${p.descriptionEn} (₹${p.price.toInt()})', maxLines: 1, overflow: TextOverflow.ellipsis),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) {
                        setModalState(() {
                          selected = val;
                          messageController.text =
                              S.get('proposal_greeting').replaceAll('इस सामान', '"${selected.descriptionEn}"');
                        });
                      }
                    },
                  ),
                  const SizedBox(height: 16),
                  Text(S.get('message_label'), style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: messageController,
                    maxLines: 3,
                    decoration: InputDecoration(
                      hintText: 'Type wholesale enquiry message...',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.send),
                    label: const Text('पूछताछ भेजें · Send Proposal'),
                    onPressed: () async {
                      final messenger = ScaffoldMessenger.of(context);
                      Navigator.pop(ctx);
                      try {
                        await ApiService.instance.sendEnquiry(
                          buyerId: buyer.id,
                          productId: int.tryParse(selected.id) ?? 1,
                          message: messageController.text.trim(),
                        );
                        messenger.showSnackBar(
                          SnackBar(
                            backgroundColor: AppTheme.success,
                            content: Text(S.get('proposal_sent') + ' ${buyer.company}'),
                          ),
                        );
                      } catch (e) {
                        messenger.showSnackBar(
                          SnackBar(content: Text('Error: $e')),
                        );
                      }
                    },
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          _activeProduct != null ? S.get('matched_buyers') : S.get('wholesale_buyers_title'),
        ),
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (_activeProduct == null)
            SizedBox(
              height: 48,
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                scrollDirection: Axis.horizontal,
                itemCount: _categories.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, i) {
                  final cat = _categories[i];
                  final isSelected = (_selectedCategory ?? 'All') == cat;
                  return ChoiceChip(
                    label: Text(cat),
                    selected: isSelected,
                    onSelected: (val) {
                      setState(() => _selectedCategory = cat);
                      _load();
                    },
                    selectedColor: AppTheme.accent,
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.white : AppTheme.ink,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      fontSize: 13,
                    ),
                  );
                },
              ),
            ),
          const SizedBox(height: 8),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _buyers.isEmpty
                    ? Center(
                        child: Text(
                          S.get('no_buyers'),
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _load,
                        child: ListView.separated(
                          padding: const EdgeInsets.all(20),
                          itemCount: _buyers.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 14),
                          itemBuilder: (context, i) {
                            final buyer = _buyers[i];
                            final match = _matchedBuyers.isNotEmpty && i < _matchedBuyers.length
                                ? _matchedBuyers[i]
                                : null;

                            return FadeSlideIn(
                              delay: Duration(milliseconds: 40 * i),
                              child: Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(18),
                                  border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                buyer.company,
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.w700,
                                                  fontSize: 17,
                                                ),
                                              ),
                                              const SizedBox(height: 2),
                                              Row(
                                                children: [
                                                  const Icon(Icons.location_on_outlined, size: 14, color: AppTheme.accent),
                                                  const SizedBox(width: 4),
                                                  Text(
                                                    '${buyer.name} • ${buyer.location}',
                                                    style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.6)),
                                                  ),
                                                ],
                                              ),
                                            ],
                                          ),
                                        ),
                                        if (match != null)
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                            decoration: BoxDecoration(
                                              color: AppTheme.successBg,
                                              borderRadius: BorderRadius.circular(999),
                                            ),
                                            child: Text(
                                              '${match.score}% Match',
                                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.success),
                                            ),
                                          ),
                                      ],
                                    ),
                                    const SizedBox(height: 10),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: AppTheme.accentBg,
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        buyer.category,
                                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.accent),
                                      ),
                                    ),
                                    if (buyer.description != null) ...[
                                      const SizedBox(height: 8),
                                      Text(
                                        buyer.description!,
                                        style: Theme.of(context).textTheme.bodyMedium,
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                    const SizedBox(height: 14),
                                    SizedBox(
                                      width: double.infinity,
                                      child: OutlinedButton.icon(
                                        icon: const Icon(Icons.chat_bubble_outline, size: 18),
                                        label: const Text('थोक प्रस्ताव भेजें · Send Proposal'),
                                        onPressed: () => _showSendEnquiryDialog(buyer),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}
