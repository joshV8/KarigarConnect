import '../language.dart';
import 'package:flutter/material.dart';
import '../models/enquiry.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/fade_slide_in.dart';

/// Screen allowing artisans to track wholesale deals, view buyer messages, and send responses.
class EnquiriesScreen extends StatefulWidget {
  const EnquiriesScreen({super.key});

  @override
  State<EnquiriesScreen> createState() => _EnquiriesScreenState();
}

class _EnquiriesScreenState extends State<EnquiriesScreen> {
  List<Enquiry> _enquiries = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final list = await ApiService.instance.fetchEnquiries();
    if (mounted) {
      setState(() {
        _enquiries = list;
        _loading = false;
      });
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'accepted':
        return AppTheme.success;
      case 'contacted':
        return AppTheme.accent;
      case 'rejected':
        return Colors.red.shade600;
      case 'pending':
      default:
        return Colors.orange.shade700;
    }
  }

  Color _getStatusBg(String status) {
    switch (status.toLowerCase()) {
      case 'accepted':
        return AppTheme.successBg;
      case 'contacted':
        return AppTheme.accentBg;
      case 'rejected':
        return Colors.red.shade50;
      case 'pending':
      default:
        return Colors.orange.shade50;
    }
  }

  void _showRespondDialog(Enquiry enquiry) {
    final responseController = TextEditingController(text: enquiry.artisanResponse ?? '');
    String currentStatus = enquiry.status;

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
                      Text(S.get('deal_details'), style: Theme.of(context).textTheme.titleLarge),
                      IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppTheme.surface,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          enquiry.buyerCompany ?? 'Wholesale Buyer',
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                        ),
                        if (enquiry.productName != null) ...[
                          const SizedBox(height: 4),
                          Text('${S.get('product_label')}: ${enquiry.productName}', style: const TextStyle(fontSize: 13, color: AppTheme.accent)),
                        ],
                        const SizedBox(height: 8),
                        Text(S.get('message_prefix'), style: TextStyle(fontSize: 12, color: AppTheme.ink.withValues(alpha: 0.5))),
                        const SizedBox(height: 2),
                        Text(enquiry.message, style: Theme.of(context).textTheme.bodyMedium),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(S.get('update_status'), style: const TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: ['pending', 'contacted', 'accepted', 'rejected'].map((st) {
                      final isSelected = currentStatus == st;
                      return ChoiceChip(
                        label: Text(st.toUpperCase()),
                        selected: isSelected,
                        onSelected: (val) {
                          if (val) setModalState(() => currentStatus = st);
                        },
                        selectedColor: _getStatusColor(st),
                        labelStyle: TextStyle(
                          color: isSelected ? Colors.white : AppTheme.ink,
                          fontWeight: isSelected ? FontWeight.w700 : FontWeight.normal,
                          fontSize: 12,
                        ),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),
                  Text(S.get('response_note'), style: const TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: responseController,
                    maxLines: 3,
                    decoration: InputDecoration(
                      hintText: S.get('response_hint'),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: () async {
                      final messenger = ScaffoldMessenger.of(context);
                      Navigator.pop(ctx);
                      try {
                        await ApiService.instance.respondToEnquiry(
                          enquiryId: enquiry.id,
                          status: currentStatus,
                          artisanResponse: responseController.text.trim(),
                        );
                        _load();
                        messenger.showSnackBar(
                          SnackBar(
                            backgroundColor: AppTheme.success,
                            content: Text(S.get('deal_updated')),
                          ),
                        );
                      } catch (e) {
                        messenger.showSnackBar(
                          SnackBar(content: Text('Error: $e')),
                        );
                      }
                    },
                    child: Text(S.get('save_response')),
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
        title: Text(S.get('deals_title')),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _enquiries.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.handshake_outlined, size: 64, color: AppTheme.ink.withValues(alpha: 0.25)),
                      const SizedBox(height: 16),
                      Text(
                        S.get('no_enquiries'),
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(20),
                    itemCount: _enquiries.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 14),
                    itemBuilder: (context, i) {
                      final enq = _enquiries[i];
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
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Expanded(
                                    child: Text(
                                      enq.buyerCompany ?? 'Wholesale Buyer',
                                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: _getStatusBg(enq.status),
                                      borderRadius: BorderRadius.circular(999),
                                    ),
                                    child: Text(
                                      enq.status.toUpperCase(),
                                      style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: FontWeight.w700,
                                        color: _getStatusColor(enq.status),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              if (enq.productName != null) ...[
                                const SizedBox(height: 4),
                                Text(
                                  '${S.get('product_label')}: ${enq.productName}',
                                  style: const TextStyle(fontSize: 13, color: AppTheme.accent, fontWeight: FontWeight.w500),
                                ),
                              ],
                              const SizedBox(height: 8),
                              Text(enq.message, style: Theme.of(context).textTheme.bodyMedium),
                              if (enq.artisanResponse != null && enq.artisanResponse!.isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Container(
                                  padding: const EdgeInsets.all(10),
                                  decoration: BoxDecoration(
                                    color: AppTheme.accentBg,
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Icon(Icons.reply, size: 16, color: AppTheme.accent),
                                      const SizedBox(width: 6),
                                      Expanded(
                                        child: Text(
                                          '${S.get('your_reply')}: "${enq.artisanResponse}"',
                                          style: const TextStyle(fontSize: 12, color: AppTheme.accent, fontWeight: FontWeight.w500),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                              const SizedBox(height: 12),
                              SizedBox(
                                width: double.infinity,
                                child: OutlinedButton.icon(
                                  icon: const Icon(Icons.edit_note, size: 18),
                                  label: Text(S.get('respond_update')),
                                  onPressed: () => _showRespondDialog(enq),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
