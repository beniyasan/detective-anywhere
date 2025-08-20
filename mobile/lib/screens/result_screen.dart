import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:detective_anywhere/models/game_models.dart';
import 'package:detective_anywhere/services/api_service.dart';
import 'package:detective_anywhere/providers/game_provider.dart';
import 'package:detective_anywhere/screens/home_screen.dart';
import 'package:detective_anywhere/utils/theme.dart';

class ResultScreen extends StatelessWidget {
  final DeductionResult result;

  const ResultScreen({
    super.key,
    required this.result,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('推理結果'),
        backgroundColor: result.correct ? AppColors.success : AppColors.danger,
        automaticallyImplyLeading: false,
      ),
      body: Consumer<GameProvider>(
        builder: (context, gameProvider, child) {
          final game = gameProvider.currentGame;
          
          return SingleChildScrollView(
            padding: const EdgeInsets.all(AppDimensions.paddingMedium),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 結果表示カード
                _buildResultCard(),
                
                const SizedBox(height: AppDimensions.paddingMedium),
                
                // 推理詳細カード
                _buildDeductionDetailCard(),
                
                const SizedBox(height: AppDimensions.paddingMedium),
                
                // 正解・真相カード
                _buildTruthCard(),
                
                if (game != null) ...[
                  const SizedBox(height: AppDimensions.paddingMedium),
                  
                  // ゲーム統計カード
                  _buildGameStatsCard(game),
                ],
                
                const SizedBox(height: AppDimensions.paddingLarge),
                
                // アクションボタン
                _buildActionButtons(context, gameProvider),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildResultCard() {
    return Card(
      color: result.correct
          ? AppColors.success.withOpacity(0.1)
          : AppColors.danger.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingLarge),
        child: Column(
          children: [
            Icon(
              result.correct ? Icons.celebration : Icons.close,
              size: AppDimensions.iconSizeExtraLarge * 1.5,
              color: result.correct ? AppColors.success : AppColors.danger,
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Text(
              result.correct ? '🎉 推理成功！' : '❌ 推理失敗',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: result.correct ? AppColors.success : AppColors.danger,
              ),
            ),
            const SizedBox(height: AppDimensions.paddingSmall),
            Text(
              result.correct
                  ? '見事に真犯人を特定しました！'
                  : '残念！真犯人は別の人物でした。',
              style: const TextStyle(fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Container(
              padding: const EdgeInsets.all(AppDimensions.paddingMedium),
              decoration: BoxDecoration(
                color: result.correct ? AppColors.success : AppColors.danger,
                borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
              ),
              child: Text(
                result.message,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDeductionDetailCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.assignment_ind, color: AppTheme.primaryColor),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  'あなたの推理',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Container(
              padding: const EdgeInsets.all(AppDimensions.paddingMedium),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '推理した犯人:',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: AppDimensions.paddingSmall),
                  Text(
                    '不明', // 実際の推理結果から取得
                    style: const TextStyle(fontSize: 16),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTruthCard() {
    return Card(
      color: AppColors.warning.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.psychology, color: AppColors.warning),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  '真相',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Container(
              padding: const EdgeInsets.all(AppDimensions.paddingMedium),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
                border: Border.all(color: AppColors.warning.withOpacity(0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '真犯人:',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: AppDimensions.paddingSmall),
                  Text(
                    result.actualCulprit,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: AppColors.danger,
                    ),
                  ),
                  const SizedBox(height: AppDimensions.paddingMedium),
                  Container(
                    padding: const EdgeInsets.all(AppDimensions.paddingSmall),
                    decoration: BoxDecoration(
                      color: AppColors.warning.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(AppDimensions.radiusSmall),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '事件の真相:',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: AppDimensions.paddingSmall),
                        Text(_generateTruthExplanation()),
                      ],
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

  Widget _buildGameStatsCard(GameSession game) {
    final discoveredCount = game.evidence.where((e) => e.discovered).length;
    final totalCount = game.evidence.length;
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.analytics, color: AppTheme.primaryColor),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  'ゲーム統計',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            _buildStatRow('発見した証拠', '$discoveredCount / $totalCount件'),
            _buildStatRow('発見率', '${(discoveredCount / totalCount * 100).toInt()}%'),
            _buildStatRow('推理結果', result.correct ? '正解' : '不正解'),
            const SizedBox(height: AppDimensions.paddingMedium),
            
            // スコア表示
            Container(
              padding: const EdgeInsets.all(AppDimensions.paddingMedium),
              decoration: BoxDecoration(
                color: _getScoreColor().withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    '総合評価',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  Row(
                    children: [
                      Text(
                        _getScoreRating(),
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: _getScoreColor(),
                        ),
                      ),
                      const SizedBox(width: AppDimensions.paddingSmall),
                      ...List.generate(5, (index) {
                        return Icon(
                          index < _getStarCount() ? Icons.star : Icons.star_border,
                          color: AppColors.warning,
                          size: 20,
                        );
                      }),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
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

  Widget _buildActionButtons(BuildContext context, GameProvider gameProvider) {
    return Column(
      children: [
        // 新しいゲームを開始
        SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton.icon(
            onPressed: () => _startNewGame(context, gameProvider),
            icon: const Icon(Icons.refresh, size: 28),
            label: const Text(
              '新しいミステリーに挑戦',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.secondaryColor,
            ),
          ),
        ),
        
        const SizedBox(height: AppDimensions.paddingMedium),
        
        // ホームに戻る
        SizedBox(
          width: double.infinity,
          height: 48,
          child: OutlinedButton.icon(
            onPressed: () => _goHome(context, gameProvider),
            icon: const Icon(Icons.home),
            label: const Text('ホームに戻る'),
          ),
        ),
      ],
    );
  }

  Color _getScoreColor() {
    if (result.correct) {
      return AppColors.success;
    } else {
      return AppColors.warning;
    }
  }

  String _getScoreRating() {
    if (result.correct) {
      return '名探偵';
    } else {
      return '見習い探偵';
    }
  }

  int _getStarCount() {
    if (result.correct) {
      return 5; // 正解なら5つ星
    } else {
      return 2; // 不正解なら2つ星
    }
  }

  String _generateTruthExplanation() {
    // 実際のアプリでは、AIで生成された詳細な説明が入る
    return '${result.actualCulprit}が犯人でした。発見された証拠から、動機と機会が最も揃っていたのがこの人物だったのです。';
  }

  void _startNewGame(BuildContext context, GameProvider gameProvider) {
    gameProvider.endGame();
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (context) => const HomeScreen()),
      (route) => false,
    );
  }

  void _goHome(BuildContext context, GameProvider gameProvider) {
    gameProvider.endGame();
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (context) => const HomeScreen()),
      (route) => false,
    );
  }
}