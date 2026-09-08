import '../language.dart';
import 'package:flutter/material.dart';
import '../models/notification_item.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/fade_slide_in.dart';

/// Screen displaying in-app alerts, wholesale enquiries received, and system updates.
class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<NotificationItem> _notifications = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final items = await ApiService.instance.fetchNotifications();
    if (mounted) {
      setState(() {
        _notifications = items;
        _loading = false;
      });
    }
  }

  Future<void> _markAllAsRead() async {
    await ApiService.instance.markAllNotificationsRead();
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(S.get('notifications_title')),
        actions: [
          if (_notifications.isNotEmpty)
            TextButton.icon(
              icon: const Icon(Icons.done_all, size: 18),
              label: Text(S.get('mark_all_read')),
              onPressed: _markAllAsRead,
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _notifications.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.notifications_none_outlined, size: 64, color: AppTheme.ink.withValues(alpha: 0.25)),
                      const SizedBox(height: 16),
                      Text(
                        S.get('no_notifications'),
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
                    itemCount: _notifications.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, i) {
                      final notif = _notifications[i];
                      return FadeSlideIn(
                        delay: Duration(milliseconds: 40 * i),
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: notif.isRead ? Colors.white : AppTheme.accent.withValues(alpha: 0.05),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: notif.isRead
                                  ? AppTheme.ink.withValues(alpha: 0.06)
                                  : AppTheme.accent.withValues(alpha: 0.3),
                            ),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: notif.isRead ? AppTheme.surface : AppTheme.accentBg,
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  notif.type == 'new_enquiry'
                                      ? Icons.storefront_outlined
                                      : Icons.notifications_active_outlined,
                                  size: 20,
                                  color: notif.isRead ? AppTheme.ink.withValues(alpha: 0.6) : AppTheme.accent,
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Expanded(
                                          child: Text(
                                            notif.title,
                                            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                                          ),
                                        ),
                                        if (!notif.isRead)
                                          Container(
                                            width: 8,
                                            height: 8,
                                            decoration: const BoxDecoration(
                                              color: AppTheme.accent,
                                              shape: BoxShape.circle,
                                            ),
                                          ),
                                      ],
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      notif.message,
                                      style: Theme.of(context).textTheme.bodyMedium,
                                    ),
                                    if (notif.createdAt != null) ...[
                                      const SizedBox(height: 8),
                                      Text(
                                        '${notif.createdAt!.day}/${notif.createdAt!.month}/${notif.createdAt!.year} ${notif.createdAt!.hour}:${notif.createdAt!.minute.toString().padLeft(2, '0')}',
                                        style: TextStyle(fontSize: 11, color: AppTheme.ink.withValues(alpha: 0.4)),
                                      ),
                                    ],
                                  ],
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
