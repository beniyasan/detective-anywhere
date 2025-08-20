import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:detective_anywhere/models/game_models.dart';
import 'package:detective_anywhere/providers/game_provider.dart';
import 'package:detective_anywhere/providers/location_provider.dart';
import 'package:detective_anywhere/utils/theme.dart';

class EvidenceScreen extends StatefulWidget {
  final Evidence evidence;

  const EvidenceScreen({
    super.key,
    required this.evidence,
  });

  @override
  State<EvidenceScreen> createState() => _EvidenceScreenState();
}

class _EvidenceScreenState extends State<EvidenceScreen> {
  bool _isDiscovering = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.evidence.discovered ? '証拠詳細' : '証拠発見'),
        backgroundColor: widget.evidence.importanceColor,
      ),
      body: Consumer2<GameProvider, LocationProvider>(
        builder: (context, gameProvider, locationProvider, child) {
          final distance = locationProvider.currentPosition != null
              ? gameProvider.calculateDistance(
                  locationProvider.currentPosition!.latitude,
                  locationProvider.currentPosition!.longitude,
                  widget.evidence.location.lat,
                  widget.evidence.location.lng,
                )
              : null;

          final isInRange = distance != null &&
              distance <= gameProvider.currentGame!.discoveryRadius;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(AppDimensions.paddingMedium),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 証拠情報カード
                _buildEvidenceCard(),

                const SizedBox(height: AppDimensions.paddingMedium),

                // 位置情報カード
                _buildLocationCard(distance, isInRange),

                const SizedBox(height: AppDimensions.paddingMedium),

                // 発見ボタンまたは詳細表示
                if (widget.evidence.discovered)
                  _buildEvidenceDetails()
                else if (isInRange)
                  _buildDiscoveryButton(gameProvider, locationProvider)
                else
                  _buildOutOfRangeMessage(),

                const SizedBox(height: AppDimensions.paddingMedium),

                // ヒントカード
                _buildHintCard(isInRange),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildEvidenceCard() {
    return Card(
      color: widget.evidence.importanceColor.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          children: [
            Icon(
              widget.evidence.discovered
                  ? Icons.visibility
                  : Icons.help_outline,
              size: AppDimensions.iconSizeExtraLarge,
              color: widget.evidence.importanceColor,
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Text(
              widget.evidence.discovered ? widget.evidence.name : '未発見の証拠',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: widget.evidence.importanceColor,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppDimensions.paddingSmall),
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppDimensions.paddingMedium,
                vertical: AppDimensions.paddingSmall,
              ),
              decoration: BoxDecoration(
                color: widget.evidence.importanceColor,
                borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
              ),
              child: Text(
                _getImportanceText(widget.evidence.importance),
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLocationCard(double? distance, bool isInRange) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  widget.evidence.typeIcon,
                  color: AppTheme.primaryColor,
                ),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  '場所情報',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            _buildInfoRow('施設名', widget.evidence.poiName),
            _buildInfoRow('施設タイプ', _getPoiTypeText(widget.evidence.poiType)),
            if (distance != null) ...[
              _buildInfoRow(
                '距離',
                '${distance.toInt()}m',
                valueColor: isInRange ? AppColors.success : AppColors.warning,
              ),
              Container(
                margin: const EdgeInsets.only(top: AppDimensions.paddingSmall),
                padding: const EdgeInsets.all(AppDimensions.paddingSmall),
                decoration: BoxDecoration(
                  color: (isInRange ? AppColors.success : AppColors.warning)
                      .withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
                ),
                child: Row(
                  children: [
                    Icon(
                      isInRange ? Icons.location_on : Icons.location_off,
                      color: isInRange ? AppColors.success : AppColors.warning,
                      size: 20,
                    ),
                    const SizedBox(width: AppDimensions.paddingSmall),
                    Expanded(
                      child: Text(
                        isInRange
                            ? '発見可能範囲内です'
                            : 'もう少し近づく必要があります（発見範囲: 50m）',
                        style: TextStyle(
                          color: isInRange ? AppColors.success : AppColors.warning,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: valueColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEvidenceDetails() {
    return Card(
      color: AppColors.success.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.check_circle, color: AppColors.success),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  '証拠発見完了',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: AppColors.success,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppDimensions.paddingMedium),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
                border: Border.all(color: AppColors.success.withOpacity(0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '証拠の詳細',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: AppDimensions.paddingSmall),
                  Text(
                    widget.evidence.description,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      height: 1.6,
                    ),
                  ),
                  const SizedBox(height: AppDimensions.paddingMedium),
                  Container(
                    padding: const EdgeInsets.all(AppDimensions.paddingSmall),
                    decoration: BoxDecoration(
                      color: widget.evidence.importanceColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(AppDimensions.radiusSmall),
                    ),
                    child: Text(
                      _getEvidenceAnalysis(widget.evidence),
                      style: TextStyle(
                        fontStyle: FontStyle.italic,
                        color: widget.evidence.importanceColor,
                      ),
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

  Widget _buildDiscoveryButton(GameProvider gameProvider, LocationProvider locationProvider) {
    return Container(
      width: double.infinity,
      height: 56,
      child: ElevatedButton.icon(
        onPressed: _isDiscovering
            ? null
            : () => _discoverEvidence(gameProvider, locationProvider),
        icon: _isDiscovering
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : const Icon(Icons.search, size: 28),
        label: Text(
          _isDiscovering ? '調査中...' : '証拠を調査する',
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: widget.evidence.importanceColor,
        ),
      ),
    );
  }

  Widget _buildOutOfRangeMessage() {
    return Card(
      color: AppColors.warning.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          children: [
            const Icon(
              Icons.location_off,
              color: AppColors.warning,
              size: AppDimensions.iconSizeLarge,
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Text(
              '証拠発見範囲外',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: AppColors.warning,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: AppDimensions.paddingSmall),
            const Text(
              '証拠を発見するには、指定された場所の50m以内に近づく必要があります。',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHintCard(bool isInRange) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.lightbulb, color: AppColors.warning),
                const SizedBox(width: AppDimensions.paddingSmall),
                Text(
                  'ヒント',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ],
            ),
            const SizedBox(height: AppDimensions.paddingMedium),
            Container(
              padding: const EdgeInsets.all(AppDimensions.paddingMedium),
              decoration: BoxDecoration(
                color: AppColors.warning.withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppDimensions.radiusMedium),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    widget.evidence.discovered
                        ? '📍 この証拠は既に発見されています。'
                        : isInRange
                            ? '🔍 この場所を詳しく調査してみましょう。'
                            : '🚶 ${widget.evidence.poiName}に向かってください。',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: AppDimensions.paddingSmall),
                  Text(_getLocationHint(widget.evidence.poiType)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getImportanceText(String importance) {
    switch (importance) {
      case 'critical':
        return '重要な証拠';
      case 'important':
        return '有力な証拠';
      case 'misleading':
        return '注意が必要';
      default:
        return '通常の証拠';
    }
  }

  String _getPoiTypeText(String poiType) {
    switch (poiType) {
      case 'cafe':
        return 'カフェ';
      case 'restaurant':
        return 'レストラン';
      case 'park':
        return '公園';
      case 'shop':
        return '店舗';
      case 'landmark':
        return 'ランドマーク';
      case 'station':
        return '駅';
      default:
        return '施設';
    }
  }

  String _getLocationHint(String poiType) {
    switch (poiType) {
      case 'cafe':
        return 'カフェの中やテラス席を確認してみてください。';
      case 'restaurant':
        return 'レストランの入口や看板周辺を調べてみてください。';
      case 'park':
        return '公園のベンチや木の近くを探してみてください。';
      case 'shop':
        return '店舗の入口やショーウィンドウを確認してみてください。';
      case 'landmark':
        return 'ランドマークの周辺や案内板を調べてみてください。';
      case 'station':
        return '駅の構内や出入口付近を確認してみてください。';
      default:
        return '施設の周辺を詳しく調べてみてください。';
    }
  }

  String _getEvidenceAnalysis(Evidence evidence) {
    switch (evidence.importance) {
      case 'critical':
        return 'この証拠は事件解決の鍵となる重要な情報を含んでいます。';
      case 'important':
        return 'この証拠は犯人特定に役立つ有力な情報です。';
      case 'misleading':
        return 'この証拠は真実から遠ざける可能性があります。注意深く検討してください。';
      default:
        return 'この証拠は事件に関連する情報を提供しています。';
    }
  }

  Future<void> _discoverEvidence(GameProvider gameProvider, LocationProvider locationProvider) async {
    if (locationProvider.currentLocation == null) {
      _showSnackBar('現在位置を取得できませんでした');
      return;
    }

    setState(() {
      _isDiscovering = true;
    });

    try {
      final result = await gameProvider.tryDiscoverEvidence(
        evidenceId: widget.evidence.evidenceId,
        playerLocation: locationProvider.currentLocation!,
      );

      if (result != null && result.discovered) {
        widget.evidence.discovered = true;
        _showSnackBar('証拠を発見しました！', isSuccess: true);
        
        // 画面を更新して詳細を表示
        setState(() {});
      } else {
        _showSnackBar(result?.message ?? '証拠の発見に失敗しました');
      }
    } catch (e) {
      _showSnackBar('エラーが発生しました: $e');
    } finally {
      setState(() {
        _isDiscovering = false;
      });
    }
  }

  void _showSnackBar(String message, {bool isSuccess = false}) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: isSuccess ? AppColors.success : AppColors.danger,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }
}