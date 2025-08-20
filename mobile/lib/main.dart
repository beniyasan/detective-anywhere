import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:detective_anywhere/providers/game_provider.dart';
import 'package:detective_anywhere/providers/location_provider.dart';
import 'package:detective_anywhere/screens/home_screen.dart';
import 'package:detective_anywhere/utils/theme.dart';

void main() {
  runApp(const DetectiveAnywhereApp());
}

class DetectiveAnywhereApp extends StatelessWidget {
  const DetectiveAnywhereApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => GameProvider()),
        ChangeNotifierProvider(create: (_) => LocationProvider()),
      ],
      child: MaterialApp(
        title: 'AIミステリー散歩',
        theme: AppTheme.lightTheme,
        home: const HomeScreen(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}