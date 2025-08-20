import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:detective_anywhere/providers/game_provider.dart';
import 'package:detective_anywhere/screens/result_screen.dart';
import 'package:detective_anywhere/utils/theme.dart';

class DeductionScreen extends StatefulWidget {
  const DeductionScreen({super.key});

  @override
  State<DeductionScreen> createState() => _DeductionScreenState();
}

class _DeductionScreenState extends State<DeductionScreen> {
  String? _selectedCulprit;
  final _reasoningController = TextEditingController();
  bool _isSubmitting = false;

  @override
  void dispose() {
    _reasoningController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('推理'),
        backgroundColor: AppColors.warning,
      ),
      body: Consumer<GameProvider>(
        builder: (context, gameProvider, child) {
          if (gameProvider.currentGame == null) {
            return const Center(
              child: Text('ゲーム情報を読み込めませんでした'),
            );
          }

          final scenario = gameProvider.currentGame!.scenario;
          final discoveredCount = gameProvider.discoveredEvidenceCount;
          final totalCount = gameProvider.totalEvidenceCount;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(AppDimensions.paddingMedium),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 推理状況カード
                _buildStatusCard(discoveredCount, totalCount),
                
                const SizedBox(height: AppDimensions.paddingMedium),
                
                // 発見済み証拠表示
                _buildDiscoveredEvidenceCard(gameProvider),
                
                const SizedBox(height: AppDimensions.paddingMedium),
                
                // 容疑者選択カード
                _buildSuspectSelectionCard(scenario.suspects),
                
                const SizedBox(height: AppDimensions.paddingMedium),
                
                // 推理入力カード
                _buildReasoningCard(),
                
                const SizedBox(height: AppDimensions.paddingLarge),
                
                // 推理提出ボタン
                _buildSubmitButton(gameProvider),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildStatusCard(int discoveredCount, int totalCount) {
    final isReady = discoveredCount >= totalCount / 2;
    
    return Card(
      color: isReady ? AppColors.success.withOpacity(0.1) : AppColors.warning.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          children: [
            Icon(
              isReady ? Icons.check_circle : Icons.warning,
              color: isReady ? AppColors.success : AppColors.warning,
              size: AppDimensions.iconSizeLarge,
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Text(
              isReady ? '推理準備完了' : '証拠収集中',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: isReady ? AppColors.success : AppColors.warning,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: AppDimensions.paddingSmall),
            Text(
              '発見済み証拠: $discoveredCount / $totalCount',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: AppDimensions.paddingSmall),
            LinearProgressIndicator(
              value: discoveredCount / totalCount,
              backgroundColor: Colors.grey[300],
              valueColor: AlwaysStoppedAnimation<Color>(
                isReady ? AppColors.success : AppColors.warning,
              ),
            ),
            if (!isReady) ...[
              const SizedBox(height: AppDimensions.paddingSmall),
              const Text(
                'より多くの証拠を発見することで推理の精度が向上します',
                style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic),
                textAlign: TextAlign.center,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDiscoveredEvidenceCard(GameProvider gameProvider) {
    final discoveredEvidence = gameProvider.currentGame!.evidence
        .where((e) => e.discovered)
        .toList();

    if (discoveredEvidence.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(AppDimensions.paddingMedium),
          child: Column(
            children: [
              const Icon(
                Icons.search_off,
                color: Colors.grey,
                size: AppDimensions.iconSizeLarge,
              ),
              const SizedBox(height: AppDimensions.paddingMedium),
              Text(
                '発見済み証拠なし',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: Colors.grey,
                ),
              ),
              const SizedBox(height: AppDimensions.paddingSmall),
              const Text(
                'まずは証拠を探索して情報を収集しましょう',
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.assignment, color: AppTheme.primaryColor),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  '発見済み証拠 (${discoveredEvidence.length}件)',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            ...discoveredEvidence.map((evidence) {
              return Container(
                margin: const EdgeInsets.only(bottom: AppDimensions.paddingSmall),
                padding: const EdgeInsets.all(AppDimensions.paddingMedium),
                decoration: BoxDecoration(
                  color: evidence.importanceColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
                  border: Border.all(
                    color: evidence.importanceColor.withOpacity(0.3),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          evidence.typeIcon,
                          color: evidence.importanceColor,
                          size: 20,
                        ),
                        const SizedBox(width: AppDimensions.paddingSmall),
                        Expanded(
                          child: Text(
                            evidence.name,
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: evidence.importanceColor,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: AppDimensions.paddingSmall,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: evidence.importanceColor,
                            borderRadius: BorderRadius.circular(AppDimensions.radiusSmall),
                          ),
                          child: Text(
                            _getImportanceText(evidence.importance),
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: AppDimensions.paddingSmall),
                    Text(
                      '場所: ${evidence.poiName}',
                      style: const TextStyle(fontSize: 12),
                    ),
                    const SizedBox(height: AppDimensions.paddingSmall / 2),
                    Text(
                      evidence.description,
                      style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic),
                    ),
                  ],
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildSuspectSelectionCard(List suspects) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.person_search, color: AppColors.danger),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  '真犯人を選択',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            const Text(
              '収集した証拠を基に、真犯人だと思う人物を選択してください。',
              style: TextStyle(fontStyle: FontStyle.italic),
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            ...suspects.map((suspect) {
              return Container(
                margin: const EdgeInsets.only(bottom: AppDimensions.paddingSmall),
                child: RadioListTile<String>(
                  title: Text(
                    '${suspect.name} (${suspect.age}歳)',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('職業: ${suspect.occupation}'),
                      Text('関係: ${suspect.relationship}'),
                      if (suspect.motive != null)
                        Text(
                          '動機: ${suspect.motive}',
                          style: const TextStyle(color: AppColors.danger),
                        ),
                    ],
                  ),
                  value: suspect.name,
                  groupValue: _selectedCulprit,
                  onChanged: (value) {
                    setState(() {
                      _selectedCulprit = value;
                    });
                  },
                  contentPadding: const EdgeInsets.all(AppDimensions.paddingSmall),
                  tileColor: _selectedCulprit == suspect.name
                      ? AppColors.danger.withOpacity(0.1)
                      : null,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
                  ),
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildReasoningCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.psychology, color: AppTheme.primaryColor),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  '推理の根拠',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            const Text(
              '選択した人物が真犯人だと考える理由を記入してください（任意）',
              style: TextStyle(fontStyle: FontStyle.italic),
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            TextField(
              controller: _reasoningController,
              maxLines: 4,
              decoration: const InputDecoration(
                hintText: '例：発見した証拠から、○○の動機が最も強く...',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubmitButton(GameProvider gameProvider) {
    final canSubmit = _selectedCulprit != null && !_isSubmitting;
    
    return Container(
      width: double.infinity,
      height: 56,
      child: ElevatedButton.icon(
        onPressed: canSubmit ? () => _submitDeduction(gameProvider) : null,
        icon: _isSubmitting
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : const Icon(Icons.gavel, size: 28),
        label: Text(
          _isSubmitting ? '推理提出中...' : '推理を提出',
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: canSubmit ? AppColors.danger : Colors.grey,
        ),
      ),
    );
  }

  String _getImportanceText(String importance) {
    switch (importance) {
      case 'critical':
        return '重要';
      case 'important':
        return '有力';
      case 'misleading':
        return '注意';
      default:
        return '通常';
    }
  }

  Future<void> _submitDeduction(GameProvider gameProvider) async {
    if (_selectedCulprit == null) return;

    setState(() {
      _isSubmitting = true;
    });

    try {
      final result = await gameProvider.submitDeduction(
        culpritName: _selectedCulprit!,
        reasoning: _reasoningController.text.trim().isEmpty
            ? null
            : _reasoningController.text.trim(),
      );

      if (result != null && mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => ResultScreen(result: result),
          ),
        );
      } else {
        _showSnackBar('推理の提出に失敗しました');
      }
    } catch (e) {
      _showSnackBar('エラーが発生しました: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  void _showSnackBar(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: AppColors.danger,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }
}