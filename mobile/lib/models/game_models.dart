// ゲーム関連のデータモデル

class Location {
  final double lat;
  final double lng;

  Location({required this.lat, required this.lng});

  factory Location.fromJson(Map<String, dynamic> json) {
    return Location(
      lat: json['lat'].toDouble(),
      lng: json['lng'].toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'lat': lat,
      'lng': lng,
    };
  }
}

class Character {
  final String name;
  final int age;
  final String occupation;
  final String personality;
  final String temperament;
  final String relationship;
  final String? alibi;
  final String? motive;

  Character({
    required this.name,
    required this.age,
    required this.occupation,
    required this.personality,
    required this.temperament,
    required this.relationship,
    this.alibi,
    this.motive,
  });

  factory Character.fromJson(Map<String, dynamic> json) {
    return Character(
      name: json['name'],
      age: json['age'],
      occupation: json['occupation'],
      personality: json['personality'],
      temperament: json['temperament'],
      relationship: json['relationship'],
      alibi: json['alibi'],
      motive: json['motive'],
    );
  }
}

class Scenario {
  final String title;
  final String description;
  final Character victim;
  final List<Character> suspects;
  final String culprit;

  Scenario({
    required this.title,
    required this.description,
    required this.victim,
    required this.suspects,
    required this.culprit,
  });

  factory Scenario.fromJson(Map<String, dynamic> json) {
    return Scenario(
      title: json['title'],
      description: json['description'],
      victim: Character.fromJson(json['victim']),
      suspects: (json['suspects'] as List)
          .map((suspect) => Character.fromJson(suspect))
          .toList(),
      culprit: json['culprit'],
    );
  }
}

class Evidence {
  final String evidenceId;
  final String name;
  final String description;
  final Location location;
  final String poiName;
  final String poiType;
  final String importance;
  bool discovered;

  Evidence({
    required this.evidenceId,
    required this.name,
    required this.description,
    required this.location,
    required this.poiName,
    required this.poiType,
    required this.importance,
    this.discovered = false,
  });

  factory Evidence.fromJson(Map<String, dynamic> json) {
    return Evidence(
      evidenceId: json['evidence_id'],
      name: json['name'],
      description: json['description'],
      location: Location.fromJson(json['location']),
      poiName: json['poi_name'],
      poiType: json['poi_type'],
      importance: json['importance'],
    );
  }

  Color get importanceColor {
    switch (importance) {
      case 'critical':
        return Colors.red;
      case 'important':
        return Colors.orange;
      case 'misleading':
        return Colors.grey;
      default:
        return Colors.blue;
    }
  }

  IconData get typeIcon {
    switch (poiType) {
      case 'cafe':
        return Icons.local_cafe;
      case 'restaurant':
        return Icons.restaurant;
      case 'park':
        return Icons.park;
      case 'shop':
        return Icons.store;
      case 'landmark':
        return Icons.location_city;
      case 'station':
        return Icons.train;
      default:
        return Icons.place;
    }
  }
}

class GameSession {
  final String gameId;
  final String playerId;
  final Scenario scenario;
  final List<Evidence> evidence;
  final Map<String, dynamic> gameRules;
  String status;

  GameSession({
    required this.gameId,
    required this.playerId,
    required this.scenario,
    required this.evidence,
    required this.gameRules,
    this.status = 'active',
  });

  factory GameSession.fromJson(Map<String, dynamic> json) {
    return GameSession(
      gameId: json['game_id'],
      playerId: json['player_id'] ?? 'anonymous',
      scenario: Scenario.fromJson(json['scenario']),
      evidence: (json['evidence'] as List)
          .map((evidence) => Evidence.fromJson(evidence))
          .toList(),
      gameRules: json['game_rules'] ?? {},
      status: json['status'] ?? 'active',
    );
  }

  double get discoveryRadius => 
      (gameRules['discovery_radius'] as num?)?.toDouble() ?? 50.0;
  
  int get discoveredCount => evidence.where((e) => e.discovered).length;
  
  double get completionRate => 
      evidence.isEmpty ? 0.0 : discoveredCount / evidence.length;
}

class GameStartRequest {
  final String playerId;
  final Location location;
  final String difficulty;

  GameStartRequest({
    required this.playerId,
    required this.location,
    required this.difficulty,
  });

  Map<String, dynamic> toJson() {
    return {
      'player_id': playerId,
      'location': location.toJson(),
      'difficulty': difficulty,
    };
  }
}

enum GameDifficulty {
  easy,
  normal,
  hard,
}

extension GameDifficultyExtension on GameDifficulty {
  String get name {
    switch (this) {
      case GameDifficulty.easy:
        return 'easy';
      case GameDifficulty.normal:
        return 'normal';
      case GameDifficulty.hard:
        return 'hard';
    }
  }

  String get displayName {
    switch (this) {
      case GameDifficulty.easy:
        return '簡単';
      case GameDifficulty.normal:
        return '普通';
      case GameDifficulty.hard:
        return '難しい';
    }
  }

  String get description {
    switch (this) {
      case GameDifficulty.easy:
        return '初心者向け：ヒント多め、証拠発見しやすい';
      case GameDifficulty.normal:
        return '標準：適度な難易度でバランスの良いゲーム';
      case GameDifficulty.hard:
        return '上級者向け：ヒント少なめ、複雑な推理が必要';
    }
  }
}