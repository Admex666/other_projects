import 'package:flutter/material.dart';
import 'package:frontend/screens/auth/auth_wrapper.dart';

void main() {
  runApp(NestCashApp());
}

class NestCashApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'NestCash',
      theme: ThemeData(primarySwatch: Colors.teal),
      home: AuthWrapper(),
    );
  }
}
