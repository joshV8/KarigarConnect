import 'package:flutter_test/flutter_test.dart';
import 'package:karigar_connect/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const ArtisanApp());
    expect(find.byType(ArtisanApp), findsOneWidget);
  });
}
