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

    // AI negotiation state
    NegotiationAnalysis? analysis;
    bool isAnalyzing = false;
    String? analysisError;

    // AI feasibility engine state
    FeasibilityReport? feasibility;
    bool isFeasibilityLoading = false;
    String? feasibilityError;
    bool showFeasibilityForm = false;
    // Capacity inputs
    int inventoryUnits = 80;
    int monthlyCapacity = 250;
    int numWorkers = 3;
    double rawMaterialPct = 60.0;

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
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Header
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(S.get('deal_details'), style: Theme.of(context).textTheme.titleLarge),
                        IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Enquiry details card
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

                    // ── AI NEGOTIATION ASSISTANT BUTTON ──────────────────────────
                    Container(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF7C3AED), Color(0xFF3B82F6)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(14),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF7C3AED).withValues(alpha: 0.25),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          )
                        ],
                      ),
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          borderRadius: BorderRadius.circular(14),
                          onTap: isAnalyzing
                              ? null
                              : () async {
                                  setModalState(() {
                                    isAnalyzing = true;
                                    analysis = null;
                                    analysisError = null;
                                  });
                                  try {
                                    final result = await ApiService.instance.analyzeEnquiry(enquiry.id);
                                    setModalState(() {
                                      analysis = result;
                                      isAnalyzing = false;
                                    });
                                  } catch (e) {
                                    setModalState(() {
                                      analysisError = 'Could not analyze: $e';
                                      isAnalyzing = false;
                                    });
                                  }
                                },
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                if (isAnalyzing)
                                  const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                                  )
                                else
                                  const Icon(Icons.auto_awesome, color: Colors.white, size: 20),
                                const SizedBox(width: 10),
                                Text(
                                  isAnalyzing ? 'Analyzing Offer...' : '💡 Analyze Offer with AI',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w700,
                                    fontSize: 15,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),

                    // ── AI ANALYSIS RESULT ────────────────────────────────────────
                    if (analysisError != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.red.shade200),
                        ),
                        child: Text(analysisError!, style: TextStyle(color: Colors.red.shade700, fontSize: 13)),
                      ),
                    ],

                    if (analysis != null) ...[
                      const SizedBox(height: 16),
                      // Sustainability badge
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                        decoration: BoxDecoration(
                          color: analysis!.isSustainable ? const Color(0xFFF0FDF4) : const Color(0xFFFFF7ED),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: analysis!.isSustainable ? const Color(0xFF86EFAC) : const Color(0xFFFBD38D),
                          ),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              analysis!.isSustainable ? '✅' : '⚠️',
                              style: const TextStyle(fontSize: 20),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    analysis!.isSustainable ? 'Fair Offer' : 'Below Sustainable Price',
                                    style: TextStyle(
                                      fontWeight: FontWeight.w700,
                                      fontSize: 14,
                                      color: analysis!.isSustainable ? const Color(0xFF15803D) : const Color(0xFFC2410C),
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    analysis!.evaluationSummary,
                                    style: TextStyle(
                                      fontSize: 13,
                                      color: analysis!.isSustainable ? const Color(0xFF166534) : const Color(0xFF9A3412),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 14),

                      // Counter-offer chips
                      if (analysis!.proposedCounterOffers.isNotEmpty) ...[
                        const Text(
                          '🤝 Suggested Counter-Offers',
                          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Tap a suggestion to copy it into your response',
                          style: TextStyle(fontSize: 11, color: Colors.grey),
                        ),
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: analysis!.proposedCounterOffers.map((offer) {
                            return GestureDetector(
                              onTap: () {
                                responseController.text = offer;
                                // Move cursor to end
                                responseController.selection = TextSelection.fromPosition(
                                  TextPosition(offset: offer.length),
                                );
                              },
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(
                                    colors: [Color(0xFFEDE9FE), Color(0xFFDBEAFE)],
                                  ),
                                  borderRadius: BorderRadius.circular(24),
                                  border: Border.all(color: const Color(0xFFC4B5FD)),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(Icons.touch_app_rounded, size: 14, color: Color(0xFF7C3AED)),
                                    const SizedBox(width: 6),
                                    Flexible(
                                      child: Text(
                                        offer,
                                        style: const TextStyle(
                                          fontSize: 12,
                                          color: Color(0xFF5B21B6),
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                        const SizedBox(height: 4),
                      ],
                    ],
                    const SizedBox(height: 16),

                    // ── AI ORDER FEASIBILITY ENGINE ───────────────────────────────
                    const Divider(height: 1, thickness: 1),
                    const SizedBox(height: 16),
                    Container(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF065F46), Color(0xFF0369A1)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(14),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF065F46).withValues(alpha: 0.25),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          borderRadius: BorderRadius.circular(14),
                          onTap: () => setModalState(() => showFeasibilityForm = !showFeasibilityForm),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.inventory_2_outlined, color: Colors.white, size: 20),
                                const SizedBox(width: 10),
                                const Expanded(
                                  child: Text(
                                    '📦 Check Order Feasibility',
                                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15),
                                  ),
                                ),
                                Icon(
                                  showFeasibilityForm ? Icons.expand_less : Icons.expand_more,
                                  color: Colors.white,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),

                    // Capacity input form (collapsible)
                    if (showFeasibilityForm) ...[
                      const SizedBox(height: 14),
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF0FDF4),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFF6EE7B7)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Enter Your Current Capacity',
                              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: Color(0xFF065F46)),
                            ),
                            const SizedBox(height: 12),

                            // Inventory
                            Row(children: [
                              const Icon(Icons.warehouse_outlined, size: 16, color: Color(0xFF065F46)),
                              const SizedBox(width: 6),
                              Text('Stock in Hand: $inventoryUnits units', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                            ]),
                            Slider(
                              value: inventoryUnits.toDouble(),
                              min: 0,
                              max: 500,
                              divisions: 50,
                              activeColor: const Color(0xFF065F46),
                              onChanged: (v) => setModalState(() => inventoryUnits = v.round()),
                            ),

                            // Monthly capacity
                            Row(children: [
                              const Icon(Icons.precision_manufacturing_outlined, size: 16, color: Color(0xFF065F46)),
                              const SizedBox(width: 6),
                              Text('Monthly Capacity: $monthlyCapacity units', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                            ]),
                            Slider(
                              value: monthlyCapacity.toDouble(),
                              min: 10,
                              max: 1000,
                              divisions: 99,
                              activeColor: const Color(0xFF065F46),
                              onChanged: (v) => setModalState(() => monthlyCapacity = v.round()),
                            ),

                            // Workers
                            Row(children: [
                              const Icon(Icons.people_outline, size: 16, color: Color(0xFF065F46)),
                              const SizedBox(width: 6),
                              Text('Workers: $numWorkers', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                            ]),
                            Slider(
                              value: numWorkers.toDouble(),
                              min: 1,
                              max: 20,
                              divisions: 19,
                              activeColor: const Color(0xFF065F46),
                              onChanged: (v) => setModalState(() => numWorkers = v.round()),
                            ),

                            // Raw material availability
                            Row(children: [
                              const Icon(Icons.grass_outlined, size: 16, color: Color(0xFF065F46)),
                              const SizedBox(width: 6),
                              Text('Raw Material: ${rawMaterialPct.round()}%', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                            ]),
                            Slider(
                              value: rawMaterialPct,
                              min: 0,
                              max: 100,
                              divisions: 20,
                              activeColor: const Color(0xFF065F46),
                              onChanged: (v) => setModalState(() => rawMaterialPct = v),
                            ),

                            const SizedBox(height: 8),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF065F46),
                                  foregroundColor: Colors.white,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                icon: isFeasibilityLoading
                                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                                    : const Icon(Icons.calculate_outlined, size: 18),
                                label: Text(isFeasibilityLoading ? 'Calculating...' : 'Calculate Feasibility'),
                                onPressed: isFeasibilityLoading
                                    ? null
                                    : () async {
                                        setModalState(() {
                                          isFeasibilityLoading = true;
                                          feasibility = null;
                                          feasibilityError = null;
                                        });
                                        try {
                                          final result = await ApiService.instance.checkFeasibility(
                                            enquiryId: enquiry.id,
                                            currentInventory: inventoryUnits,
                                            monthlyCapacity: monthlyCapacity,
                                            numWorkers: numWorkers,
                                            rawMaterialPct: rawMaterialPct,
                                          );
                                          setModalState(() {
                                            feasibility = result;
                                            isFeasibilityLoading = false;
                                          });
                                        } catch (e) {
                                          setModalState(() {
                                            feasibilityError = 'Error: $e';
                                            isFeasibilityLoading = false;
                                          });
                                        }
                                      },
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],

                    // Feasibility results
                    if (feasibilityError != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.red.shade200)),
                        child: Text(feasibilityError!, style: TextStyle(color: Colors.red.shade700, fontSize: 13)),
                      ),
                    ],

                    if (feasibility != null) ...[
                      const SizedBox(height: 16),
                      // Status banner
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                        decoration: BoxDecoration(
                          color: feasibility!.canFulfillOnTime ? const Color(0xFFF0FDF4) : const Color(0xFFFEF2F2),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: feasibility!.canFulfillOnTime ? const Color(0xFF6EE7B7) : const Color(0xFFFCA5A5)),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(feasibility!.statusEmoji, style: const TextStyle(fontSize: 22)),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    feasibility!.statusLabel,
                                    style: TextStyle(
                                      fontWeight: FontWeight.w700,
                                      fontSize: 14,
                                      color: feasibility!.canFulfillOnTime ? const Color(0xFF065F46) : const Color(0xFF991B1B),
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    feasibility!.summary,
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: feasibility!.canFulfillOnTime ? const Color(0xFF166534) : const Color(0xFF7F1D1D),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),

                      // Breakdown table
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF8FAFC),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFFE2E8F0)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('📊 Production Breakdown', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                            const SizedBox(height: 10),
                            _FeasibilityRow(label: 'Required units', value: '${feasibility!.breakdown.requiredUnits}'),
                            _FeasibilityRow(label: 'Current inventory', value: '${feasibility!.breakdown.inventoryAvailable} units'),
                            _FeasibilityRow(label: 'Units to produce', value: '${feasibility!.breakdown.unitsToProduce}', highlight: true),
                            _FeasibilityRow(label: 'Daily production rate', value: '${feasibility!.breakdown.productionRatePerDay.toStringAsFixed(1)} units/day'),
                            _FeasibilityRow(
                              label: 'Estimated time',
                              value: '~${feasibility!.breakdown.estimatedDays.toStringAsFixed(0)} days',
                              highlight: !feasibility!.canFulfillOnTime,
                              highlightColor: const Color(0xFF991B1B),
                            ),
                          ],
                        ),
                      ),

                      // Split delivery chip
                      if (feasibility!.splitDeliverySuggestion != null) ...[
                        const SizedBox(height: 12),
                        const Text('🚚 Split Delivery Suggestion', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                        const SizedBox(height: 6),
                        GestureDetector(
                          onTap: () {
                            final msg = feasibility!.recommendedResponse;
                            responseController.text = msg;
                            responseController.selection = TextSelection.fromPosition(TextPosition(offset: msg.length));
                          },
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFFECFDF5), Color(0xFFE0F2FE)],
                              ),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: const Color(0xFF6EE7B7)),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.touch_app_rounded, size: 16, color: Color(0xFF065F46)),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    feasibility!.splitDeliverySuggestion!,
                                    style: const TextStyle(fontSize: 12, color: Color(0xFF065F46), fontWeight: FontWeight.w600),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text('Tap to use this reply', style: TextStyle(fontSize: 10, color: Colors.grey)),
                      ],
                      const SizedBox(height: 4),
                    ],
                    const SizedBox(height: 16),

                    // Status update
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

                    // Response textarea
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

                              // Action buttons row — always visible on card
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  // Primary: Respond / Update
                                  OutlinedButton.icon(
                                    icon: const Icon(Icons.edit_note, size: 18),
                                    label: Text(S.get('respond_update')),
                                    onPressed: () => _showRespondDialog(enq),
                                  ),
                                  const SizedBox(height: 8),

                                  // AI Negotiation Assistant — prominent teal-purple pill
                                  _AiActionButton(
                                    icon: Icons.auto_awesome,
                                    label: '💡 AI Negotiation Assistant',
                                    subtitle: 'Evaluate offer & get counter-offers',
                                    colors: const [Color(0xFF7C3AED), Color(0xFF3B82F6)],
                                    onTap: () => _showRespondDialog(enq),
                                  ),
                                  const SizedBox(height: 8),

                                  // Feasibility Engine — teal-blue pill
                                  _AiActionButton(
                                    icon: Icons.inventory_2_outlined,
                                    label: '📦 Order Feasibility Engine',
                                    subtitle: 'Check capacity, timeline & split delivery',
                                    colors: const [Color(0xFF065F46), Color(0xFF0369A1)],
                                    onTap: () => _showRespondDialog(enq),
                                  ),
                                ],
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

/// Simple key-value row for the feasibility breakdown table.
class _FeasibilityRow extends StatelessWidget {
  final String label;
  final String value;
  final bool highlight;
  final Color? highlightColor;

  const _FeasibilityRow({
    required this.label,
    required this.value,
    this.highlight = false,
    this.highlightColor,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
          Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: highlight ? (highlightColor ?? const Color(0xFF065F46)) : Colors.black87,
            ),
          ),
        ],
      ),
    );
  }
}

class _AiActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final List<Color> colors;
  final VoidCallback onTap;

  const _AiActionButton({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.colors,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: colors,
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: colors.first.withValues(alpha: 0.2),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.2),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, color: Colors.white, size: 18),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        label,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                          fontSize: 13,
                        ),
                      ),
                      Text(
                        subtitle,
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.8),
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right, color: Colors.white70, size: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
