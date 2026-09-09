import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';

/// Displays a product photo from whichever source is available:
/// 1. A remote [url] (Cloudinary / S3 / backend static storage or base64 data URI)
/// 2. Raw [bytes] (Uint8List — works everywhere including Web)
/// 3. A local [file] (dart:io File on Mobile / Desktop)
/// 4. Fallback to aesthetic placeholder
class SafeImage extends StatelessWidget {
  final File? file;
  final Uint8List? bytes;
  final String? url;
  final BoxFit fit;
  final BorderRadius? borderRadius;

  const SafeImage({
    super.key,
    this.file,
    this.bytes,
    this.url,
    this.fit = BoxFit.cover,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    Widget child;
    if (url != null && url!.isNotEmpty) {
      if (url!.startsWith('data:image')) {
        try {
          final commaIndex = url!.indexOf(',');
          final base64String = commaIndex != -1 ? url!.substring(commaIndex + 1) : url!;
          final decodedBytes = base64Decode(base64String);
          child = Image.memory(
            decodedBytes,
            fit: fit,
            width: double.infinity,
            height: double.infinity,
            errorBuilder: (context, error, stack) => _placeholder(),
          );
        } catch (_) {
          child = _placeholder();
        }
      } else {
        child = Image.network(
          url!,
          fit: fit,
          width: double.infinity,
          height: double.infinity,
          loadingBuilder: (context, widget, progress) =>
              progress == null ? widget : _placeholder(),
          errorBuilder: (context, error, stack) => _placeholder(),
        );
      }
    } else if (bytes != null && bytes!.isNotEmpty) {
      child = AnimatedSwitcher(
        duration: const Duration(milliseconds: 250),
        child: Image.memory(
          bytes!,
          fit: fit,
          width: double.infinity,
          height: double.infinity,
        ),
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
