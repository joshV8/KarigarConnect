import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/fade_slide_in.dart';
import '../widgets/home_action.dart';

/// Market Linkage: shows buyer interest coming in through B2B
/// marketplaces, government e-marketplaces, and direct buyers. Mock
/// data for now (see ApiService) — swap for a real feed once Person
/// 3's backend exposes it, per API_CONTRACT.md.
class BuyerEnquiriesScreen extends StatelessWidget {
  const BuyerEnquiriesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final enquiries = ApiService.instance.enquiries;
    return Scaffold(
      appBar: AppBar(
        title: const Text('खरीदार पूछताछ · Buyer enquiries'),
        actions: const [HomeAction()],
      ),
      body: enquiries.isEmpty
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  'अभी कोई पूछताछ नहीं\nNo enquiries yet',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(20),
              itemCount: enquiries.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, i) {
                final e = enquiries[i];
                return FadeSlideIn(
                  delay: Duration(milliseconds: 50 * i),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                e.buyerName,
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                              ),
                            ),
                            Text(_relativeTime(e.receivedAt),
                                style: TextStyle(fontSize: 12, color: AppTheme.ink.withValues(alpha: 0.45))),
                          ],
                        ),
                        const SizedBox(height: 6),
                        _channelBadge(e.channel),
                        const SizedBox(height: 10),
                        Text(e.message, style: Theme.of(context).textTheme.bodyLarge),
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppTheme.canvas,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  e.productDescription,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.7)),
                                ),
                              ),
                              Text('₹${e.productPrice.toInt()}',
                                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }

  Widget _channelBadge(String channel) {
    final color = switch (channel) {
      'B2B Marketplace' => AppTheme.accent,
      'Government e-Marketplace' => AppTheme.success,
      _ => AppTheme.danger,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(999)),
      child: Text(channel, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color)),
    );
  }

  String _relativeTime(DateTime t) {
    final diff = DateTime.now().difference(t);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}
