import 'package:flutter/material.dart';
import '../screens/home_screen.dart';

/// A persistent way back to Home from anywhere past login. Drop this
/// into any screen's AppBar actions so no one — teammates included —
/// ever gets stuck mid-flow with no way out.
class HomeAction extends StatelessWidget {
  const HomeAction({super.key});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.home_outlined),
      tooltip: 'Home',
      onPressed: () {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const HomeScreen()),
          (route) => false,
        );
      },
    );
  }
}
