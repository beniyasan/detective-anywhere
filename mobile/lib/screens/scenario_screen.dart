import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:detective_anywhere/providers/game_provider.dart';
import 'package:detective_anywhere/screens/exploration_screen.dart';
import 'package:detective_anywhere/utils/theme.dart';

class ScenarioScreen extends StatelessWidget {
  const ScenarioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ミステリーシナリオ'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => _showExitDialog(context),
        ),
      ),
      body: Consumer<GameProvider>(
        builder: (context, gameProvider, child) {
          if (gameProvider.currentGame == null) {
            return const Center(
              child: Text('ゲーム情報を取得できませんでした'),
            );
          }

          final scenario = gameProvider.currentGame!.scenario;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(AppDimensions.paddingMedium),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // タイトルカード
                _buildTitleCard(context, scenario.title),
                
                const SizedBox(height: AppDimensions.paddingMedium),
                
                // あらすじカード
                _buildStoryCard(context, scenario.description),
                
                const SizedBox(height: AppDimensions.paddingMedium),
                
                // 被害者情報カード
                _buildVictimCard(context, scenario.victim),
                
                const SizedBox(height: AppDimensions.paddingMedium),
                
                // 容疑者一覧カード
                _buildSuspectsCard(context, scenario.suspects),
                
                const SizedBox(height: AppDimensions.paddingLarge),
                
                // 探索開始ボタン
                _buildStartExplorationButton(context, gameProvider),
                
                const SizedBox(height: AppDimensions.paddingMedium),
                
                // ゲーム情報
                _buildGameInfoCard(context, gameProvider),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildTitleCard(BuildContext context, String title) {
    return Card(
      color: AppTheme.primaryColor,
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingLarge),
        child: Column(
          children: [
            const Icon(
              Icons.quiz,
              color: Colors.white,
              size: AppDimensions.iconSizeLarge,
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Text(
              title,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStoryCard(BuildContext context, String description) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.menu_book, color: AppTheme.primaryColor),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  'あらすじ',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Text(
              description,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                height: 1.6,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVictimCard(BuildContext context, victim) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.person, color: AppColors.danger),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  '被害者',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Container(
              padding: const EdgeInsets.all(AppDimensions.paddingMedium),
              decoration: BoxDecoration(
                color: AppColors.danger.withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${victim.name} (${victim.age}歳)',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: AppDimensions.paddingSmall),
                  Text('職業: ${victim.occupation}'),
                  const SizedBox(height: AppDimensions.paddingSmall),
                  Text('性格: ${victim.personality}'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSuspectsCard(BuildContext context, List suspects) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.group, color: AppColors.warning),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  '容疑者 (${suspects.length}名)',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            ...suspects.asMap().entries.map((entry) {
              final index = entry.key;
              final suspect = entry.value;
              
              return Container(
                margin: const EdgeInsets.only(bottom: AppDimensions.paddingMedium),
                padding: const EdgeInsets.all(AppDimensions.paddingMedium),
                decoration: BoxDecoration(
                  color: AppColors.warning.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: AppColors.warning,
                          foregroundColor: Colors.white,
                          radius: 16,
                          child: Text('${index + 1}'),
                        ),
                        const SizedBox(width: AppDimensions.paddingSmall),
                        Expanded(
                          child: Text(
                            '${suspect.name} (${suspect.age}歳)',
                            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: AppDimensions.paddingSmall),
                    Text('職業: ${suspect.occupation}'),
                    const SizedBox(height: AppDimensions.paddingSmall / 2),
                    Text('性格: ${suspect.personality}'),
                    const SizedBox(height: AppDimensions.paddingSmall / 2),
                    Text('関係: ${suspect.relationship}'),
                    if (suspect.alibi != null) ...[
                      const SizedBox(height: AppDimensions.paddingSmall / 2),
                      Text(
                        'アリバイ: ${suspect.alibi}',
                        style: const TextStyle(fontStyle: FontStyle.italic),
                      ),
                    ],
                    if (suspect.motive != null) ...[
                      const SizedBox(height: AppDimensions.paddingSmall / 2),
                      Text(
                        '動機: ${suspect.motive}',
                        style: const TextStyle(color: AppColors.danger),
                      ),
                    ],
                  ],
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildStartExplorationButton(BuildContext context, GameProvider gameProvider) {
    return Container(
      width: double.infinity,
      height: 56,
      child: ElevatedButton.icon(
        onPressed: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (context) => const ExplorationScreen(),
            ),
          );
        },
        icon: const Icon(Icons.explore, size: 28),
        label: const Text(
          '証拠探索を開始',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.secondaryColor,
        ),
      ),
    );
  }

  Widget _buildGameInfoCard(BuildContext context, GameProvider gameProvider) {
    final game = gameProvider.currentGame!;
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.info, color: AppTheme.primaryColor),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  'ゲーム情報',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            _buildInfoRow('証拠数', '${game.evidence.length}件'),
            _buildInfoRow('発見半径', '${game.discoveryRadius.toInt()}m'),
            _buildInfoRow('難易度', _getDifficultyDisplayName(game.gameRules)),
            const SizedBox(height: AppDimensions.paddingSmall),
            Container(
              padding: const EdgeInsets.all(AppDimensions.paddingSmall),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
              ),
              child: const Text(
                '💡 ヒント: 証拠を全て発見したら推理を提出しましょう！',
                style: TextStyle(fontStyle: FontStyle.italic),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  String _getDifficultyDisplayName(Map<String, dynamic> gameRules) {
    // ゲームルールから難易度を推定（実際のAPIレスポンスに応じて調整）
    return '普通'; // デフォルト値
  }

  Future<void> _showExitDialog(BuildContext context) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('ゲームを終了しますか？'),
        content: const Text('進行中のゲームが失われます。本当に終了しますか？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('キャンセル'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text(
              '終了',
              style: TextStyle(color: AppColors.danger),
            ),
          ),
        ],
      ),
    );

    if (result == true && context.mounted) {
      context.read<GameProvider>().endGame();
      Navigator.of(context).pop();
    }
  }
}