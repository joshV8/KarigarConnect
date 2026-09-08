import 'dart:io';
import 'dart:typed_data';

/// A product that has been through the AI pipeline and is ready to
/// preview / publish. [image] or [imageBytes] is used for local
/// preview; [imageUrl] is what the real backend returns (Cloudinary/S3).
class Product {
  final String id;
  final File? image;
  final Uint8List? imageBytes;
  final String? imageUrl;
  final String descriptionHi;
  final String descriptionEn;
  final String? voiceTranscription;
  final String? translatedVoiceText;
  final String? audioUrl;
  final double price;
  final String priceReason;

  Product({
    required this.id,
    this.image,
    this.imageBytes,
    this.imageUrl,
    required this.descriptionHi,
    required this.descriptionEn,
    this.voiceTranscription,
    this.translatedVoiceText,
    this.audioUrl,
    required this.price,
    required this.priceReason,
  });
}

/// Holds the in-progress state of the Add Product flow (photo, voice
/// note, raw cost) as the user moves through the three steps, before
/// it's sent off for AI processing.
class ProductDraft {
  File? photo;
  Uint8List? photoBytes;
  String? photoName;
  String? photoPath;
  String? audioPath;
  Uint8List? audioBytes;
  String? audioName;
  String language;
  double? audioDuration;
  double rawMaterialCost;

  ProductDraft({
    this.photo,
    this.photoBytes,
    this.photoName,
    this.photoPath,
    this.audioPath,
    this.audioBytes,
    this.audioName,
    this.language = 'hi',
    this.audioDuration,
    this.rawMaterialCost = 100,
  });
}
