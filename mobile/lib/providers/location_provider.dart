import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:detective_anywhere/models/game_models.dart';

class LocationProvider extends ChangeNotifier {
  Position? _currentPosition;
  bool _isLocationEnabled = false;
  bool _hasLocationPermission = false;
  bool _isLoading = false;
  String? _error;

  // ゲッター
  Position? get currentPosition => _currentPosition;
  bool get isLocationEnabled => _isLocationEnabled;
  bool get hasLocationPermission => _hasLocationPermission;
  bool get isLoading => _isLoading;
  String? get error => _error;
  
  Location? get currentLocation {
    if (_currentPosition == null) return null;
    return Location(
      lat: _currentPosition!.latitude,
      lng: _currentPosition!.longitude,
    );
  }

  // 位置サービスが利用可能かどうか
  bool get isLocationAvailable => 
      _isLocationEnabled && _hasLocationPermission && _currentPosition != null;

  // 初期化
  Future<void> initialize() async {
    await checkLocationService();
    await checkLocationPermission();
    if (isLocationAvailable) {
      await getCurrentLocation();
    }
  }

  // 位置サービスの確認
  Future<void> checkLocationService() async {
    try {
      _isLocationEnabled = await Geolocator.isLocationServiceEnabled();
      notifyListeners();
    } catch (e) {
      _error = '位置サービスの確認に失敗しました';
      notifyListeners();
    }
  }

  // 位置情報権限の確認
  Future<void> checkLocationPermission() async {
    try {
      final permission = await Permission.location.status;
      _hasLocationPermission = permission.isGranted;
      notifyListeners();
    } catch (e) {
      _error = '位置情報権限の確認に失敗しました';
      notifyListeners();
    }
  }

  // 位置情報権限のリクエスト
  Future<bool> requestLocationPermission() async {
    try {
      if (!_isLocationEnabled) {
        _error = '位置サービスが無効になっています。設定で有効にしてください。';
        notifyListeners();
        return false;
      }

      final permission = await Permission.location.request();
      _hasLocationPermission = permission.isGranted;
      
      if (!_hasLocationPermission) {
        if (permission.isPermanentlyDenied) {
          _error = '位置情報の権限が永続的に拒否されました。設定から権限を有効にしてください。';
        } else {
          _error = '位置情報の権限が必要です。';
        }
      } else {
        _error = null;
      }
      
      notifyListeners();
      return _hasLocationPermission;
    } catch (e) {
      _error = '位置情報権限の取得に失敗しました';
      notifyListeners();
      return false;
    }
  }

  // 現在位置の取得
  Future<bool> getCurrentLocation() async {
    if (!_hasLocationPermission) {
      final granted = await requestLocationPermission();
      if (!granted) return false;
    }

    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _currentPosition = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 10),
      );
      
      _isLoading = false;
      _error = null;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _error = '現在位置の取得に失敗しました';
      notifyListeners();
      return false;
    }
  }

  // 位置情報の継続的な監視を開始
  void startLocationUpdates() {
    if (!_hasLocationPermission) return;

    Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // 10m移動したら更新
      ),
    ).listen(
      (Position position) {
        _currentPosition = position;
        notifyListeners();
      },
      onError: (error) {
        _error = '位置情報の更新に失敗しました';
        notifyListeners();
      },
    );
  }

  // 指定した位置との距離を計算
  double? getDistanceTo(Location targetLocation) {
    if (_currentPosition == null) return null;
    
    return Geolocator.distanceBetween(
      _currentPosition!.latitude,
      _currentPosition!.longitude,
      targetLocation.lat,
      targetLocation.lng,
    );
  }

  // 指定した位置が範囲内かどうかチェック
  bool isWithinRange(Location targetLocation, double radius) {
    final distance = getDistanceTo(targetLocation);
    return distance != null && distance <= radius;
  }

  // エラークリア
  void clearError() {
    _error = null;
    notifyListeners();
  }

  // 設定画面を開く
  Future<void> openLocationSettings() async {
    await openAppSettings();
  }
}