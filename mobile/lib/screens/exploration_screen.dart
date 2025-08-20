import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:detective_anywhere/providers/game_provider.dart';
import 'package:detective_anywhere/providers/location_provider.dart';
import 'package:detective_anywhere/screens/evidence_screen.dart';
import 'package:detective_anywhere/screens/deduction_screen.dart';
import 'package:detective_anywhere/utils/theme.dart';

class ExplorationScreen extends StatefulWidget {
  const ExplorationScreen({super.key});

  @override
  State<ExplorationScreen> createState() => _ExplorationScreenState();
}

class _ExplorationScreenState extends State<ExplorationScreen> {
  GoogleMapController? _mapController;
  Set<Marker> _markers = {};
  Set<Circle> _circles = {};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _updateMapMarkers();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('証拠探索'),
        actions: [
          Consumer<GameProvider>(
            builder: (context, gameProvider, child) {
              return IconButton(
                icon: Stack(
                  children: [
                    const Icon(Icons.lightbulb),
                    if (gameProvider.discoveredEvidenceCount >= gameProvider.totalEvidenceCount / 2)
                      Positioned(
                        right: 0,
                        top: 0,
                        child: Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                            color: AppColors.success,
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                  ],
                ),
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => const DeductionScreen(),
                    ),
                  );
                },
                tooltip: '推理を提出',
              );
            },
          ),
        ],
      ),
      body: Consumer2<GameProvider, LocationProvider>(
        builder: (context, gameProvider, locationProvider, child) {
          if (gameProvider.currentGame == null) {
            return const Center(
              child: Text('ゲーム情報を読み込めませんでした'),
            );
          }

          return Stack(
            children: [
              // Google Map
              _buildMap(locationProvider, gameProvider),
              
              // 上部の進捗表示
              _buildProgressCard(gameProvider),
              
              // 下部の証拠リスト
              _buildEvidenceList(gameProvider, locationProvider),
            ],
          );
        },
      ),
      floatingActionButton: Consumer<LocationProvider>(
        builder: (context, locationProvider, child) {
          return FloatingActionButton(
            onPressed: locationProvider.isLoading
                ? null
                : () => _centerToCurrentLocation(locationProvider),
            child: locationProvider.isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.my_location),
          );
        },
      ),
    );
  }

  Widget _buildMap(LocationProvider locationProvider, GameProvider gameProvider) {
    if (locationProvider.currentPosition == null) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    final currentPosition = LatLng(
      locationProvider.currentPosition!.latitude,
      locationProvider.currentPosition!.longitude,
    );

    return GoogleMap(
      onMapCreated: (controller) {
        _mapController = controller;
        _updateMapMarkers();
      },
      initialCameraPosition: CameraPosition(
        target: currentPosition,
        zoom: 16.0,
      ),
      markers: _markers,
      circles: _circles,
      myLocationEnabled: true,
      myLocationButtonEnabled: false,
      compassEnabled: true,
      mapToolbarEnabled: false,
    );
  }

  Widget _buildProgressCard(GameProvider gameProvider) {
    return Positioned(
      top: AppDimensions.paddingMedium,
      left: AppDimensions.paddingMedium,
      right: AppDimensions.paddingMedium,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(AppDimensions.paddingMedium),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '証拠発見状況',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    '${gameProvider.discoveredEvidenceCount}/${gameProvider.totalEvidenceCount}',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryColor,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppDimensions.paddingSmall),
              LinearProgressIndicator(
                value: gameProvider.completionRate,
                backgroundColor: Colors.grey[300],
                valueColor: AlwaysStoppedAnimation<Color>(
                  gameProvider.completionRate >= 1.0
                      ? AppColors.success
                      : AppTheme.primaryColor,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEvidenceList(GameProvider gameProvider, LocationProvider locationProvider) {
    return DraggableScrollableSheet(
      initialChildSize: 0.3,
      minChildSize: 0.1,
      maxChildSize: 0.8,
      builder: (context, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(
              top: Radius.circular(AppDimensions.radiusLarge),
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black26,
                blurRadius: 10,
                offset: Offset(0, -2),
              ),
            ],
          ),
          child: Column(
            children: [
              // ハンドル
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.symmetric(vertical: AppDimensions.paddingSmall),
                decoration: BoxDecoration(
                  color: Colors.grey[400],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              
              // タイトル
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: AppDimensions.paddingMedium),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '証拠一覧',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    if (gameProvider.discoveredEvidenceCount >= gameProvider.totalEvidenceCount / 2)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: AppDimensions.paddingSmall,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.success,
                          borderRadius: BorderRadius.circular(AppDimensions.radiusSmall),
                        ),
                        child: const Text(
                          '推理可能',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
              
              const SizedBox(height: AppDimensions.paddingSmall),
              
              // 証拠リスト
              Expanded(
                child: ListView.builder(
                  controller: scrollController,
                  padding: const EdgeInsets.symmetric(horizontal: AppDimensions.paddingMedium),
                  itemCount: gameProvider.currentGame!.evidence.length,
                  itemBuilder: (context, index) {
                    final evidence = gameProvider.currentGame!.evidence[index];
                    final distance = locationProvider.currentPosition != null
                        ? gameProvider.calculateDistance(
                            locationProvider.currentPosition!.latitude,
                            locationProvider.currentPosition!.longitude,
                            evidence.location.lat,
                            evidence.location.lng,
                          )
                        : null;
                    
                    final isNearby = distance != null && 
                        distance <= gameProvider.currentGame!.discoveryRadius;

                    return Card(
                      margin: const EdgeInsets.only(bottom: AppDimensions.paddingSmall),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: evidence.discovered
                              ? AppColors.success
                              : isNearby
                                  ? evidence.importanceColor
                                  : Colors.grey[400],
                          foregroundColor: Colors.white,
                          child: evidence.discovered
                              ? const Icon(Icons.check, size: 20)
                              : Icon(evidence.typeIcon, size: 20),
                        ),
                        title: Text(
                          evidence.discovered ? evidence.name : '???',
                          style: TextStyle(
                            fontWeight: evidence.discovered || isNearby
                                ? FontWeight.w600
                                : FontWeight.normal,
                            color: evidence.discovered
                                ? AppColors.success
                                : isNearby
                                    ? AppTheme.primaryColor
                                    : Colors.grey[600],
                          ),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(evidence.poiName),
                            if (distance != null)
                              Text(
                                '距離: ${distance.toInt()}m',
                                style: TextStyle(
                                  color: isNearby ? AppColors.success : Colors.grey[600],
                                  fontWeight: isNearby ? FontWeight.w600 : FontWeight.normal,
                                ),
                              ),
                          ],
                        ),
                        trailing: evidence.discovered
                            ? const Icon(Icons.visibility, color: AppColors.success)
                            : isNearby
                                ? const Icon(Icons.location_on, color: AppTheme.primaryColor)
                                : null,
                        onTap: evidence.discovered || isNearby
                            ? () {
                                Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (context) => EvidenceScreen(evidence: evidence),
                                  ),
                                );
                              }
                            : null,
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _updateMapMarkers() {
    final gameProvider = context.read<GameProvider>();
    final game = gameProvider.currentGame;
    
    if (game == null) return;

    final Set<Marker> markers = {};
    final Set<Circle> circles = {};

    for (final evidence in game.evidence) {
      final markerId = MarkerId(evidence.evidenceId);
      final position = LatLng(evidence.location.lat, evidence.location.lng);

      // マーカー
      markers.add(
        Marker(
          markerId: markerId,
          position: position,
          icon: evidence.discovered
              ? BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen)
              : BitmapDescriptor.defaultMarkerWithHue(_getMarkerHue(evidence.importance)),
          infoWindow: InfoWindow(
            title: evidence.discovered ? evidence.name : '???',
            snippet: evidence.poiName,
          ),
          onTap: () {
            if (evidence.discovered) {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (context) => EvidenceScreen(evidence: evidence),
                ),
              );
            }
          },
        ),
      );

      // 発見範囲の円（発見済みの証拠のみ）
      if (evidence.discovered) {
        circles.add(
          Circle(
            circleId: CircleId('${evidence.evidenceId}_range'),
            center: position,
            radius: game.discoveryRadius,
            fillColor: AppColors.success.withOpacity(0.1),
            strokeColor: AppColors.success.withOpacity(0.3),
            strokeWidth: 2,
          ),
        );
      }
    }

    setState(() {
      _markers = markers;
      _circles = circles;
    });
  }

  double _getMarkerHue(String importance) {
    switch (importance) {
      case 'critical':
        return BitmapDescriptor.hueRed;
      case 'important':
        return BitmapDescriptor.hueOrange;
      case 'misleading':
        return BitmapDescriptor.hueViolet;
      default:
        return BitmapDescriptor.hueBlue;
    }
  }

  void _centerToCurrentLocation(LocationProvider locationProvider) {
    if (_mapController != null && locationProvider.currentPosition != null) {
      _mapController!.animateCamera(
        CameraUpdate.newLatLng(
          LatLng(
            locationProvider.currentPosition!.latitude,
            locationProvider.currentPosition!.longitude,
          ),
        ),
      );
    }
  }
}