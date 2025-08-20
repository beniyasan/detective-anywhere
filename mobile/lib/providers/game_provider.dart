import 'package:flutter/material.dart';
import 'package:detective_anywhere/models/game_models.dart';
import 'package:detective_anywhere/services/api_service.dart';

class GameProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  // ゲーム状態
  GameSession? _currentGame;
  GameStatus? _gameStatus;
  bool _isLoading = false;
  String? _error;
  
  // ゲッター
  GameSession? get currentGame => _currentGame;
  GameStatus? get gameStatus => _gameStatus;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasGame => _currentGame != null;
  
  // ゲーム中かどうか
  bool get isGameActive => _currentGame != null && _currentGame!.status == 'active';
  
  // 発見済み証拠数
  int get discoveredEvidenceCount {
    if (_currentGame == null) return 0;
    return _currentGame!.evidence.where((e) => e.discovered).length;
  }
  
  // 総証拠数
  int get totalEvidenceCount => _currentGame?.evidence.length ?? 0;
  
  // 完了率
  double get completionRate {
    if (totalEvidenceCount == 0) return 0.0;
    return discoveredEvidenceCount / totalEvidenceCount;
  }

  // エラークリア
  void clearError() {
    _error = null;
    notifyListeners();
  }

  // ゲーム開始
  Future<bool> startGame({
    required String playerId,
    required Location location,
    required GameDifficulty difficulty,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final request = GameStartRequest(
        playerId: playerId,
        location: location,
        difficulty: difficulty.name,
      );

      _currentGame = await _apiService.startGame(request);
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString().replaceFirst('ApiException: ', '');
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // ゲーム状態更新
  Future<void> refreshGameStatus() async {
    if (_currentGame == null) return;

    try {
      _gameStatus = await _apiService.getGameStatus(_currentGame!.gameId);
      
      // 発見済み証拠の状態を更新
      for (final discoveredEvidence in _gameStatus!.discoveredEvidence) {
        final evidenceIndex = _currentGame!.evidence.indexWhere(
          (e) => e.evidenceId == discoveredEvidence.evidenceId,
        );
        if (evidenceIndex != -1) {
          _currentGame!.evidence[evidenceIndex].discovered = true;
        }
      }
      
      notifyListeners();
    } catch (e) {
      _error = e.toString().replaceFirst('ApiException: ', '');
      notifyListeners();
    }
  }

  // 証拠発見試行
  Future<EvidenceDiscoveryResult?> tryDiscoverEvidence({
    required String evidenceId,
    required Location playerLocation,
  }) async {
    if (_currentGame == null) return null;

    try {
      final result = await _apiService.discoverEvidence(
        gameId: _currentGame!.gameId,
        evidenceId: evidenceId,
        playerLocation: playerLocation,
      );

      if (result.discovered && result.evidence != null) {
        // 証拠を発見済みに更新
        final evidenceIndex = _currentGame!.evidence.indexWhere(
          (e) => e.evidenceId == evidenceId,
        );
        if (evidenceIndex != -1) {
          _currentGame!.evidence[evidenceIndex].discovered = true;
        }
        notifyListeners();
      }

      return result;
    } catch (e) {
      _error = e.toString().replaceFirst('ApiException: ', '');
      notifyListeners();
      return null;
    }
  }

  // 推理提出
  Future<DeductionResult?> submitDeduction({
    required String culpritName,
    String? reasoning,
  }) async {
    if (_currentGame == null) return null;

    _isLoading = true;
    notifyListeners();

    try {
      final result = await _apiService.submitDeduction(
        gameId: _currentGame!.gameId,
        culpritName: culpritName,
        reasoning: reasoning,
      );

      // ゲーム終了状態に更新
      if (result.correct || _currentGame!.evidence.every((e) => e.discovered)) {
        _currentGame!.status = 'completed';
      }

      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _error = e.toString().replaceFirst('ApiException: ', '');
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  // ゲーム終了
  void endGame() {
    _currentGame = null;
    _gameStatus = null;
    _error = null;
    notifyListeners();
  }

  // 指定された証拠を取得
  Evidence? getEvidenceById(String evidenceId) {
    if (_currentGame == null) return null;
    
    try {
      return _currentGame!.evidence.firstWhere(
        (evidence) => evidence.evidenceId == evidenceId,
      );
    } catch (e) {
      return null;
    }
  }

  // 近くの証拠を取得（指定半径内）
  List<Evidence> getNearbyEvidence(Location playerLocation, {double radius = 100.0}) {
    if (_currentGame == null) return [];

    return _currentGame!.evidence.where((evidence) {
      final distance = calculateDistance(
        playerLocation.lat,
        playerLocation.lng,
        evidence.location.lat,
        evidence.location.lng,
      );
      return distance <= radius;
    }).toList();
  }

  // 発見可能な証拠を取得（ゲームルールの半径内）
  List<Evidence> getDiscoverableEvidence(Location playerLocation) {
    final radius = _currentGame?.discoveryRadius ?? 50.0;
    return getNearbyEvidence(playerLocation, radius: radius)
        .where((evidence) => !evidence.discovered)
        .toList();
  }

  // 距離計算（簡易版：実際のアプリでは Geolocator.distanceBetween を使用）
  double calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    // Haversine formula の簡易版
    const double earthRadius = 6371000; // meters
    
    final double dLat = (lat2 - lat1) * (3.14159 / 180);
    final double dLon = (lon2 - lon1) * (3.14159 / 180);
    
    final double a = (dLat / 2) * (dLat / 2) +
        (lat1 * 3.14159 / 180).cos() * (lat2 * 3.14159 / 180).cos() *
        (dLon / 2) * (dLon / 2);
    
    final double c = 2 * (a.sqrt()).atan2((1 - a).sqrt());
    
    return earthRadius * c;
  }
}