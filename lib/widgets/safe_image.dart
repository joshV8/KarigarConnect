import 'dart:io';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';

/// Displays a product photo from whichever source is available:
/// a remote [url] (once the real backend returns Cloudinary/S3
/// links) takes priority, then a local [file] (mock/demo mode). On
/// Flutter web, dart:io's File can't be read at all (Image.file
/// throws), so a local file falls back to a placeholder there —
/// this only matters for quick web preview; the real app runs on
/// Android/iOS.
class SafeImage extends StatelessWidget {
  final File? file;
  final String? url;
  final BoxFit fit;
  final BorderRadius? borderRadius;

  const SafeImage({super.key, this.file, this.url, this.fit = BoxFit.cover, this.borderRadius});

  @override
  Widget build(BuildContext context) {
    Widget child;
    if (url != null) {
      child = Image.network(
        url!,
        fit: fit,
        width: double.infinity,
        height: double.infinity,
        loadingBuilder: (context, widget, progress) =>
            progress == null ? widget : _placeholder(),
        errorBuilder: (context, error, stack) => _placeholder(),
      );
    } else if (file != null && !kIsWeb) {
      child = AnimatedSwitcher(
        duration: const Duration(milliseconds: 250),
        child: Image.file(
          file!,
          key: ValueKey(file!.path),
          fit: fit,
          width: double.infinity,
          height: double.infinity,
        ),
      );
    } else {
      child = _placeholder();
    }
    if (borderRadius != null) {
      return ClipRRect(borderRadius: borderRadius!, child: child);
    }
    return child;
  }

  Widget _placeholder() {
    return Container(
      color: const Color(0xFFE7EEF2),
      alignment: Alignment.center,
      child: const Icon(Icons.image_outlined, size: 36, color: Color(0xFFA9BFC9)),
    );
  }
}
