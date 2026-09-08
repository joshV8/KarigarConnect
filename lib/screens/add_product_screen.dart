import 'dart:io';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import '../models/product.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/home_action.dart';
import 'processing_screen.dart';

/// The 3-step add-product flow: photo -> voice note -> raw cost.
/// One PageView keeps the shared [ProductDraft] alive across steps
/// without needing a state-management package.
class AddProductScreen extends StatefulWidget {
  final ProductDraft? initialDraft;
  const AddProductScreen({super.key, this.initialDraft});

  @override
  State<AddProductScreen> createState() => _AddProductScreenState();
}

class _AddProductScreenState extends State<AddProductScreen> {
  late final ProductDraft _draft = widget.initialDraft ?? ProductDraft();
  late final _pageController = PageController(initialPage: _stepFor(_draft));
  late int _step = _stepFor(_draft);

  int _stepFor(ProductDraft d) {
    if (d.photo != null && d.audioPath != null) return 2;
    if (d.photo != null) return 1;
    return 0;
  }

  @override
  void initState() {
    super.initState();
    // Track this draft so leaving mid-flow (e.g. the Home button)
    // doesn't lose it — Home offers to resume it next time.
    ApiService.instance.saveDraft(_draft);
  }

  void _next() {
    ApiService.instance.saveDraft(_draft);
    if (_step < 2) {
      _pageController.nextPage(
          duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
    } else {
      ApiService.instance.clearDraft();
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => ProcessingScreen(draft: _draft)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('नया सामान · Add product'),
        actions: const [HomeAction()],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(6),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: List.generate(3, (i) {
                final active = i <= _step;
                return Expanded(
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    curve: Curves.easeOut,
                    height: 5,
                    margin: EdgeInsets.only(right: i < 2 ? 6 : 0, bottom: 8),
                    decoration: BoxDecoration(
                      color: active ? AppTheme.accent : AppTheme.ink.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(999),
                    ),
                  ),
                );
              }),
            ),
          ),
        ),
      ),
      body: PageView(
        controller: _pageController,
        physics: const NeverScrollableScrollPhysics(), // force use of Continue button
        onPageChanged: (i) => setState(() => _step = i),
        children: [
          _PhotoStep(draft: _draft, onNext: _next),
          _VoiceStep(draft: _draft, onNext: _next),
          _PriceStep(draft: _draft, onNext: _next),
        ],
      ),
    );
  }
}

class _PhotoStep extends StatefulWidget {
  final ProductDraft draft;
  final VoidCallback onNext;
  const _PhotoStep({required this.draft, required this.onNext});

  @override
  State<_PhotoStep> createState() => _PhotoStepState();
}

class _PhotoStepState extends State<_PhotoStep> {
  Future<void> _takePhoto() async {
    final picked = await ImagePicker().pickImage(source: ImageSource.camera, imageQuality: 85);
    if (picked != null) {
      HapticFeedback.mediumImpact();
      setState(() => widget.draft.photo = File(picked.path));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('फोटो लें · Take a photo',
              textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 20),
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(color: AppTheme.ink.withValues(alpha: 0.15), width: 2),
                borderRadius: BorderRadius.circular(20),
              ),
              child: widget.draft.photo != null
                  ? Hero(
                      tag: 'product-photo',
                      child: SafeImage(file: widget.draft.photo, borderRadius: BorderRadius.circular(18)),
                    )
                  : Center(
                      child: Icon(Icons.image_outlined, size: 56, color: AppTheme.ink.withValues(alpha: 0.2)),
                    ),
            ),
          ),
          const SizedBox(height: 24),
          Center(
            child: GestureDetector(
              onTap: _takePhoto,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                width: 76,
                height: 76,
                decoration: const BoxDecoration(color: AppTheme.accent, shape: BoxShape.circle),
                child: const Icon(Icons.camera_alt, color: Colors.white, size: 30),
              ),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: widget.draft.photo != null ? widget.onNext : null,
            child: const Text('आगे बढ़ें · Continue'),
          ),
        ],
      ),
    );
  }
}

class _VoiceStep extends StatefulWidget {
  final ProductDraft draft;
  final VoidCallback onNext;
  const _VoiceStep({required this.draft, required this.onNext});

  @override
  State<_VoiceStep> createState() => _VoiceStepState();
}

class _VoiceStepState extends State<_VoiceStep> with SingleTickerProviderStateMixin {
  final _recorder = AudioRecorder();
  late final AnimationController _waveController =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 900))..repeat(reverse: true);
  bool _isRecording = false;
  bool _hasRecording = false;

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      final path = await _recorder.stop();
      HapticFeedback.lightImpact();
      setState(() {
        _isRecording = false;
        _hasRecording = path != null;
        widget.draft.audioPath = path;
      });
    } else {
      if (await _recorder.hasPermission()) {
        final dir = await getTemporaryDirectory();
        final path = '${dir.path}/voice_note.m4a';
        await _recorder.start(const RecordConfig(), path: path);
        HapticFeedback.mediumImpact();
        setState(() => _isRecording = true);
      }
    }
  }

  @override
  void dispose() {
    _recorder.dispose();
    _waveController.dispose();
    super.dispose();
  }

  Widget _buildWave() {
    const baseHeights = [22.0, 42.0, 58.0, 34.0, 48.0, 20.0];
    return AnimatedBuilder(
      animation: _waveController,
      builder: (context, _) {
        final t = _waveController.value;
        return SizedBox(
          height: 64,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: baseHeights.asMap().entries.map((e) {
              final phase = e.key * 0.6;
              final scale = _isRecording ? (0.5 + 0.5 * sin((t * 2 * pi) + phase).abs()) : 0.3;
              return Container(
                width: 5,
                height: e.value * scale,
                margin: const EdgeInsets.symmetric(horizontal: 3),
                decoration: BoxDecoration(
                  color: _isRecording ? AppTheme.accent : AppTheme.ink.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(3),
                ),
              );
            }).toList(),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('बताइए, यह क्या है? · Describe it',
              textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          Text(
            _isRecording
                ? 'रिकॉर्डिंग जारी है... · Recording...'
                : (_hasRecording ? 'रिकॉर्ड हो गया · Recorded' : 'माइक दबाकर बोलें · Tap mic to speak'),
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const Spacer(),
          _buildWave(),
          const SizedBox(height: 12),
          Center(
            child: GestureDetector(
              onTap: _toggleRecording,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                width: 88,
                height: 88,
                decoration: BoxDecoration(
                  color: _isRecording ? AppTheme.danger : AppTheme.accent,
                  shape: BoxShape.circle,
                ),
                child: Icon(_isRecording ? Icons.stop_rounded : Icons.mic, color: Colors.white, size: 34),
              ),
            ),
          ),
          const Spacer(),
          ElevatedButton(
            onPressed: _hasRecording && !_isRecording ? widget.onNext : null,
            child: const Text('आगे बढ़ें · Continue'),
          ),
        ],
      ),
    );
  }
}

class _PriceStep extends StatefulWidget {
  final ProductDraft draft;
  final VoidCallback onNext;
  const _PriceStep({required this.draft, required this.onNext});

  @override
  State<_PriceStep> createState() => _PriceStepState();
}

class _PriceStepState extends State<_PriceStep> {
  void _adjust(double delta) {
    HapticFeedback.selectionClick();
    setState(() {
      widget.draft.rawMaterialCost = (widget.draft.rawMaterialCost + delta).clamp(0, 100000);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('सामान की कीमत · Raw material cost',
              textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleLarge),
          const Spacer(),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              const Text('₹', style: TextStyle(fontSize: 30, fontWeight: FontWeight.w600)),
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 200),
                transitionBuilder: (child, anim) => ScaleTransition(scale: anim, child: child),
                child: Text(
                  widget.draft.rawMaterialCost.toInt().toString(),
                  key: ValueKey(widget.draft.rawMaterialCost),
                  style: const TextStyle(fontSize: 44, fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _roundButton(Icons.remove, () => _adjust(-10)),
              const SizedBox(width: 24),
              _roundButton(Icons.add, () => _adjust(10)),
            ],
          ),
          const Spacer(),
          ElevatedButton(onPressed: widget.onNext, child: const Text('आगे बढ़ें · Continue')),
        ],
      ),
    );
  }

  Widget _roundButton(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 56,
        height: 56,
        decoration: BoxDecoration(
          border: Border.all(color: AppTheme.ink.withValues(alpha: 0.15), width: 1.5),
          shape: BoxShape.circle,
        ),
        child: Icon(icon, size: 26, color: AppTheme.ink),
      ),
    );
  }
}
