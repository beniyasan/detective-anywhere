import 'package:dio/dio.dart';
import 'package:detective_anywhere/models/game_models.dart';

class ApiService {
  static const String _baseUrl = 'http://10.0.2.2:8000'; // Android エミュレータ用
  // 実機の場合は実際のIPアドレスを使用
  // static const String _baseUrl = 'http://192.168.1.100:8000';
  
  late final Dio _dio;
  
  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {
        'Content-Type': 'application/json',
      },
    ));
    
    // インターセプター追加（ログ用）
    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      requestHeader: true,
      responseHeader: false,
    ));
  }

  // ヘルスチェック
  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get('/health');
      return response.statusCode == 200;
    } catch (e) {
      print('Health check failed: $e');
      return false;
    }
  }

  // 周辺POI検索
  Future<List<POI>> getNearbyPOIs({
    required double lat,
    required double lng,
    int radius = 1000,
    int limit = 10,
  }) async {
    try {
      final response = await _dio.get(
        '/api/v1/poi/nearby',
        queryParameters: {
          'lat': lat,
          'lng': lng,
          'radius': radius,
          'limit': limit,
        },
      );

      final List<dynamic> poisData = response.data['pois'] ?? [];
      return poisData.map((poi) => POI.fromJson(poi)).toList();
    } catch (e) {
      print('Failed to get nearby POIs: $e');
      throw ApiException('周辺の施設情報の取得に失敗しました');
    }
  }

  // ゲーム作成可能エリアの検証
  Future<AreaValidationResult> validateGameArea({
    required double lat,
    required double lng,
    int radius = 1000,
  }) async {
    try {
      final response = await _dio.post(
        '/api/v1/poi/validate-area',
        queryParameters: {
          'lat': lat,
          'lng': lng,
          'radius': radius,
        },
      );

      return AreaValidationResult.fromJson(response.data);
    } catch (e) {
      print('Failed to validate area: $e');
      throw ApiException('エリア検証に失敗しました');
    }
  }

  // ゲーム開始
  Future<GameSession> startGame(GameStartRequest request) async {
    try {
      final response = await _dio.post(
        '/api/v1/game/start',
        data: request.toJson(),
      );

      return GameSession.fromJson(response.data);
    } catch (e) {
      print('Failed to start game: $e');
      if (e is DioException) {
        final errorMessage = e.response?.data?['detail']?['message'] ?? 
                           'ゲームの作成に失敗しました';
        throw ApiException(errorMessage);
      }
      throw ApiException('ゲームの作成に失敗しました');
    }
  }

  // ゲーム状態取得
  Future<GameStatus> getGameStatus(String gameId) async {
    try {
      final response = await _dio.get('/api/v1/game/$gameId');
      return GameStatus.fromJson(response.data);
    } catch (e) {
      print('Failed to get game status: $e');
      if (e is DioException && e.response?.statusCode == 404) {
        throw ApiException('ゲームセッションが見つかりません');
      }
      throw ApiException('ゲーム状態の取得に失敗しました');
    }
  }

  // 証拠発見
  Future<EvidenceDiscoveryResult> discoverEvidence({
    required String gameId,
    required String evidenceId,
    required Location playerLocation,
  }) async {
    try {
      final response = await _dio.post(
        '/api/v1/evidence/discover',
        data: {
          'game_id': gameId,
          'evidence_id': evidenceId,
          'player_location': playerLocation.toJson(),
        },
      );

      return EvidenceDiscoveryResult.fromJson(response.data);
    } catch (e) {
      print('Failed to discover evidence: $e');
      throw ApiException('証拠の発見に失敗しました');
    }
  }

  // 推理提出
  Future<DeductionResult> submitDeduction({
    required String gameId,
    required String culpritName,
    String? reasoning,
  }) async {
    try {
      final response = await _dio.post(
        '/api/v1/deduction/submit',
        data: {
          'game_id': gameId,
          'culprit_name': culpritName,
          'reasoning': reasoning,
        },
      );

      return DeductionResult.fromJson(response.data);
    } catch (e) {
      print('Failed to submit deduction: $e');
      throw ApiException('推理の提出に失敗しました');
    }
  }
}

// 追加のデータモデル
class POI {
  final String poiId;
  final String name;
  final String type;
  final Location location;
  final double distance;
  final bool suitableForEvidence;

  POI({
    required this.poiId,
    required this.name,
    required this.type,
    required this.location,
    required this.distance,
    required this.suitableForEvidence,
  });

  factory POI.fromJson(Map<String, dynamic> json) {
    return POI(
      poiId: json['poi_id'],
      name: json['name'],
      type: json['type'],
      location: Location.fromJson(json['location']),
      distance: json['distance'].toDouble(),
      suitableForEvidence: json['suitable_for_evidence'] ?? false,
    );
  }
}

class AreaValidationResult {
  final bool valid;
  final int totalPois;
  final int suitablePois;
  final String reason;
  final List<String> recommendations;

  AreaValidationResult({
    required this.valid,
    required this.totalPois,
    required this.suitablePois,
    required this.reason,
    required this.recommendations,
  });

  factory AreaValidationResult.fromJson(Map<String, dynamic> json) {
    return AreaValidationResult(
      valid: json['valid'],
      totalPois: json['total_pois'],
      suitablePois: json['suitable_pois'],
      reason: json['reason'],
      recommendations: List<String>.from(json['recommendations'] ?? []),
    );
  }
}

class GameStatus {
  final String gameId;
  final String status;
  final Scenario scenario;
  final List<Evidence> discoveredEvidence;
  final GameProgress progress;

  GameStatus({
    required this.gameId,
    required this.status,
    required this.scenario,
    required this.discoveredEvidence,
    required this.progress,
  });

  factory GameStatus.fromJson(Map<String, dynamic> json) {
    return GameStatus(
      gameId: json['game_id'],
      status: json['status'],
      scenario: Scenario.fromJson(json['scenario']),
      discoveredEvidence: (json['discovered_evidence'] as List)
          .map((e) => Evidence.fromJson(e))
          .toList(),
      progress: GameProgress.fromJson(json['progress']),
    );
  }
}

class GameProgress {
  final int totalEvidence;
  final int discoveredCount;
  final double completionRate;
  final int timeElapsed;

  GameProgress({
    required this.totalEvidence,
    required this.discoveredCount,
    required this.completionRate,
    required this.timeElapsed,
  });

  factory GameProgress.fromJson(Map<String, dynamic> json) {
    return GameProgress(
      totalEvidence: json['total_evidence'],
      discoveredCount: json['discovered_count'],
      completionRate: json['completion_rate'].toDouble(),
      timeElapsed: json['time_elapsed'],
    );
  }
}

class EvidenceDiscoveryResult {
  final bool discovered;
  final Evidence? evidence;
  final String message;

  EvidenceDiscoveryResult({
    required this.discovered,
    this.evidence,
    required this.message,
  });

  factory EvidenceDiscoveryResult.fromJson(Map<String, dynamic> json) {
    return EvidenceDiscoveryResult(
      discovered: json['discovered'],
      evidence: json['evidence'] != null 
          ? Evidence.fromJson(json['evidence'])
          : null,
      message: json['message'],
    );
  }
}

class DeductionResult {
  final bool correct;
  final String message;
  final String actualCulprit;
  final Map<String, dynamic>? gameResult;

  DeductionResult({
    required this.correct,
    required this.message,
    required this.actualCulprit,
    this.gameResult,
  });

  factory DeductionResult.fromJson(Map<String, dynamic> json) {
    return DeductionResult(
      correct: json['correct'],
      message: json['message'],
      actualCulprit: json['actual_culprit'],
      gameResult: json['game_result'],
    );
  }
}

class ApiException implements Exception {
  final String message;
  
  ApiException(this.message);
  
  @override
  String toString() => 'ApiException: $message';
}