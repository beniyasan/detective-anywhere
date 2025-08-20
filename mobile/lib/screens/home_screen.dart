import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:detective_anywhere/models/game_models.dart';
import 'package:detective_anywhere/providers/game_provider.dart';
import 'package:detective_anywhere/providers/location_provider.dart';
import 'package:detective_anywhere/screens/scenario_screen.dart';
import 'package:detective_anywhere/utils/theme.dart';
import 'package:uuid/uuid.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  GameDifficulty _selectedDifficulty = GameDifficulty.normal;
  bool _isInitializing = true;

  @override
  void initState() {
    super.initState();
    _initializeLocation();
  }

  Future<void> _initializeLocation() async {
    final locationProvider = context.read<LocationProvider>();
    await locationProvider.initialize();
    setState(() {
      _isInitializing = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AIミステリー散歩'),
      ),
      body: _isInitializing
          ? const Center(child: CircularProgressIndicator())
          : Consumer2<LocationProvider, GameProvider>(
              builder: (context, locationProvider, gameProvider, child) {
                return SingleChildScrollView(
                  padding: const EdgeInsets.all(AppDimensions.paddingMedium),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // アプリ紹介カード
                      _buildWelcomeCard(),
                      
                      const SizedBox(height: AppDimensions.paddingLarge),
                      
                      // 位置情報ステータス
                      _buildLocationStatusCard(locationProvider),
                      
                      const SizedBox(height: AppDimensions.paddingLarge),
                      
                      // ゲーム設定
                      _buildGameSettingsCard(locationProvider),
                      
                      const SizedBox(height: AppDimensions.paddingLarge),
                      
                      // ゲーム開始ボタン
                      _buildStartGameButton(locationProvider, gameProvider),
                      
                      // エラー表示
                      if (gameProvider.error != null)
                        _buildErrorCard(gameProvider),
                    ],
                  ),
                );
              },
            ),
    );
  }

  Widget _buildWelcomeCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          children: [
            const Icon(
              Icons.location_searching,
              size: AppDimensions.iconSizeExtraLarge,
              color: AppTheme.primaryColor,
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Text(
              'AIミステリー散歩へようこそ',
              style: Theme.of(context).textTheme.headlineMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppDimensions.paddingSmall),
            Text(
              '現在地を中心としたミステリーゲームを楽しみましょう。AIが生成する謎解きに挑戦してください。',
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLocationStatusCard(LocationProvider locationProvider) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.my_location),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  '位置情報',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            
            _buildStatusItem(
              '位置サービス',
              locationProvider.isLocationEnabled,
            ),
            _buildStatusItem(
              '位置情報権限',
              locationProvider.hasLocationPermission,
            ),
            _buildStatusItem(
              '現在位置',
              locationProvider.currentPosition != null,
            ),
            
            if (locationProvider.error != null)
              Container(
                margin: const EdgeInsets.only(top: AppDimensions.paddingSmall),
                padding: const EdgeInsets.all(AppDimensions.paddingSmall),
                decoration: BoxDecoration(
                  color: AppColors.danger.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error, color: AppColors.danger, size: 20),
                    const SizedBox(width: AppDimensions.paddingSmall),
                    Expanded(
                      child: Text(
                        locationProvider.error!,
                        style: const TextStyle(color: AppColors.danger),
                      ),
                    ),
                  ],
                ),
              ),
            
            if (!locationProvider.isLocationAvailable)
              Container(
                margin: const EdgeInsets.only(top: AppDimensions.paddingMedium),
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: locationProvider.isLoading
                      ? null
                      : () async {
                          if (!locationProvider.hasLocationPermission) {
                            await locationProvider.requestLocationPermission();
                          }
                          await locationProvider.getCurrentLocation();
                        },
                  icon: locationProvider.isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.location_on),
                  label: Text(locationProvider.isLoading ? '取得中...' : '位置情報を取得'),
                ),
              ),
            
            if (locationProvider.currentPosition != null)
              Container(
                margin: const EdgeInsets.only(top: AppDimensions.paddingSmall),
                padding: const EdgeInsets.all(AppDimensions.paddingSmall),
                decoration: BoxDecoration(
                  color: AppColors.success.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle, color: AppColors.success, size: 20),
                    const SizedBox(width: AppDimensions.paddingSmall),
                    Expanded(
                      child: Text(
                        '現在位置: ${locationProvider.currentPosition!.latitude.toStringAsFixed(4)}, ${locationProvider.currentPosition!.longitude.toStringAsFixed(4)}',
                        style: const TextStyle(color: AppColors.success),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusItem(String title, bool status) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(
            status ? Icons.check_circle : Icons.cancel,
            color: status ? AppColors.success : AppColors.danger,
            size: 20,
          ),
          const SizedBox(width: AppDimensions.paddingSmall),
          Text(title),
        ],
      ),
    );
  }

  Widget _buildGameSettingsCard(LocationProvider locationProvider) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.settings),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  'ゲーム設定',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            
            Text(
              '難易度',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: AppDimensions.paddingSmall),
            
            ...GameDifficulty.values.map((difficulty) {
              return RadioListTile<GameDifficulty>(
                title: Text(difficulty.displayName),
                subtitle: Text(
                  difficulty.description,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                value: difficulty,
                groupValue: _selectedDifficulty,
                onChanged: (value) {
                  setState(() {
                    _selectedDifficulty = value!;
                  });
                },
                contentPadding: EdgeInsets.zero,
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildStartGameButton(LocationProvider locationProvider, GameProvider gameProvider) {
    final canStartGame = locationProvider.isLocationAvailable && !gameProvider.isLoading;
    
    return Container(
      margin: const EdgeInsets.symmetric(vertical: AppDimensions.paddingMedium),
      width: double.infinity,
      height: 56,
      child: ElevatedButton.icon(
        onPressed: canStartGame ? () => _startGame(locationProvider, gameProvider) : null,
        icon: gameProvider.isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : const Icon(Icons.play_arrow, size: 28),
        label: Text(
          gameProvider.isLoading ? 'ゲーム準備中...' : 'ミステリー開始',
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: canStartGame ? AppTheme.primaryColor : Colors.grey,
        ),
      ),
    );
  }

  Widget _buildErrorCard(GameProvider gameProvider) {
    return Card(
      color: AppColors.danger.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Row(
          children: [
            const Icon(Icons.error, color: AppColors.danger),
            const SizedBox(width: AppDimensions.paddingSmall),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'エラーが発生しました',
                    style: TextStyle(
                      color: AppColors.danger,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    gameProvider.error!,
                    style: const TextStyle(color: AppColors.danger),
                  ),
                ],
              ),
            ),
            TextButton(
              onPressed: () => gameProvider.clearError(),
              child: const Text('閉じる'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _startGame(LocationProvider locationProvider, GameProvider gameProvider) async {
    const uuid = Uuid();
    
    final success = await gameProvider.startGame(
      playerId: uuid.v4(),
      location: locationProvider.currentLocation!,
      difficulty: _selectedDifficulty,
    );
    
    if (success && mounted) {
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => const ScenarioScreen(),
        ),
      );
    }
  }
}