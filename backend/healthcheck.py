#!/usr/bin/env python3
"""
ヘルスチェック用スクリプト
Dockerコンテナのヘルスチェックで使用
"""

import sys
import httpx
import asyncio
from typing import Dict, Any

async def check_health() -> bool:
    """
    アプリケーションの健全性をチェック
    
    Returns:
        bool: ヘルシーな場合True
    """
    
    try:
        # APIサーバーのヘルスチェック
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8000/health")
            
            if response.status_code != 200:
                print(f"Health endpoint returned status: {response.status_code}")
                return False
            
            health_data = response.json()
            
            # サービス状態の確認
            if health_data.get("status") != "healthy":
                print(f"Application reports unhealthy status: {health_data}")
                return False
            
            # 各サービスの状態確認
            services = health_data.get("services", {})
            
            required_services = ["api", "firestore"]
            for service in required_services:
                if services.get(service) != "connected" and services.get(service) != "running":
                    print(f"Service {service} is not healthy: {services.get(service)}")
                    return False
            
            print("✅ Health check passed")
            return True
            
    except httpx.ConnectError:
        print("❌ Cannot connect to application")
        return False
    except httpx.TimeoutException:
        print("❌ Health check timed out")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """メイン関数"""
    try:
        is_healthy = asyncio.run(check_health())
        
        if is_healthy:
            print("🟢 Application is healthy")
            sys.exit(0)
        else:
            print("🔴 Application is unhealthy")
            sys.exit(1)
            
    except Exception as e:
        print(f"🔴 Health check error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()