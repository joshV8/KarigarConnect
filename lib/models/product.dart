import 'dart:io';

/// A product that has been through the AI pipeline and is ready to
/// preview / publish. [image] is used in mock/demo mode (a local
/// file straight from the camera); [imageUrl] is what the real
/// backend returns instead (Cloudinary/S3 link) once Person 2/3's
/// pipeline is wired in — see API_CONTRACT.md.
class Product {
  final String id;
  final File? image;
  final String? imageUrl;
  final String descriptionHi;
  final String descriptionEn;
  final double price;
  final String priceReason;

  Product({
    required this.id,
    this.image,
    this.imageUrl,
    required this.descriptionHi,
    required this.descriptionEn,
    required this.price,
    required this.priceReason,
  });
}

/// Holds the in-progress state of the Add Product flow (photo, voice
/// note, raw cost) as the user moves through the three steps, before
/// it's sent off for AI processing.
class ProductDraft {
  File? photo;
  String? audioPath;
  double rawMaterialCost;

  ProductDraft({this.photo, this.audioPath, this.rawMaterialCost = 100});
}
