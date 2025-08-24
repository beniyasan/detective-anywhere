/**
 * Service Worker for AIミステリー散歩 PWA
 */

const CACHE_NAME = 'detective-anywhere-v1';
const urlsToCache = [
  '/',
  '/web-demo.html',
  '/manifest.json',
  '/static/css/mobile.css',
  '/static/js/app.js'
];

// キャッシュ戦略
const CACHE_STRATEGIES = {
  networkFirst: [
    '/api/',  // APIコールは常にネットワーク優先
  ],
  cacheFirst: [
    '/static/',  // 静的アセットはキャッシュ優先
    '/icons/',
    '.png',
    '.jpg',
    '.css',
    '.js'
  ],
  staleWhileRevalidate: [
    '/',  // HTMLページは古いキャッシュを表示しつつ更新
    '.html'
  ]
};

// インストール時の処理
self.addEventListener('install', event => {
  console.log('[Service Worker] Install');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .catch(err => console.error('[Service Worker] Cache failed:', err))
  );
  
  // 即座にアクティベート
  self.skipWaiting();
});

// アクティベート時の処理
self.addEventListener('activate', event => {
  console.log('[Service Worker] Activate');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // すべてのクライアントを制御
  self.clients.claim();
});

// フェッチ時の処理
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // 同一オリジンのリクエストのみ処理
  if (url.origin !== location.origin) {
    return;
  }
  
  // キャッシュ戦略を選択
  const strategy = getStrategy(url.pathname);
  
  switch (strategy) {
    case 'networkFirst':
      event.respondWith(networkFirst(request));
      break;
    case 'cacheFirst':
      event.respondWith(cacheFirst(request));
      break;
    case 'staleWhileRevalidate':
      event.respondWith(staleWhileRevalidate(request));
      break;
    default:
      event.respondWith(networkFirst(request));
  }
});

// キャッシュ戦略の判定
function getStrategy(pathname) {
  for (const [strategy, patterns] of Object.entries(CACHE_STRATEGIES)) {
    for (const pattern of patterns) {
      if (pathname.includes(pattern)) {
        return strategy;
      }
    }
  }
  return 'networkFirst';
}

// ネットワーク優先戦略
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    
    // 成功レスポンスをキャッシュ
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[Service Worker] Network request failed, fallback to cache');
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // オフラインページを返す
    return caches.match('/offline.html');
  }
}

// キャッシュ優先戦略
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    // 成功レスポンスをキャッシュ
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[Service Worker] Fetch failed:', error);
    throw error;
  }
}

// Stale While Revalidate戦略
async function staleWhileRevalidate(request) {
  const cachedResponse = await caches.match(request);
  
  const fetchPromise = fetch(request).then(networkResponse => {
    if (networkResponse.ok) {
      const cache = caches.open(CACHE_NAME);
      cache.then(c => c.put(request, networkResponse.clone()));
    }
    return networkResponse;
  });
  
  return cachedResponse || fetchPromise;
}

// バックグラウンド同期
self.addEventListener('sync', event => {
  console.log('[Service Worker] Background sync:', event.tag);
  
  if (event.tag === 'sync-game-data') {
    event.waitUntil(syncGameData());
  }
});

// ゲームデータの同期
async function syncGameData() {
  try {
    // IndexedDBから未同期データを取得
    const unsyncedData = await getUnsyncedData();
    
    // サーバーに送信
    for (const data of unsyncedData) {
      await fetch('/api/v1/game/sync', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
      });
    }
    
    console.log('[Service Worker] Game data synced successfully');
  } catch (error) {
    console.error('[Service Worker] Sync failed:', error);
  }
}

// プッシュ通知
self.addEventListener('push', event => {
  console.log('[Service Worker] Push received');
  
  const options = {
    title: 'AIミステリー散歩',
    body: event.data ? event.data.text() : '新しい証拠が近くにあります！',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: '探索する',
        icon: '/static/icons/explore.png'
      },
      {
        action: 'close',
        title: '閉じる',
        icon: '/static/icons/close.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('AIミステリー散歩', options)
  );
});

// 通知クリック処理
self.addEventListener('notificationclick', event => {
  console.log('[Service Worker] Notification click');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/game/explore')
    );
  }
});

// メッセージ処理
self.addEventListener('message', event => {
  console.log('[Service Worker] Message received:', event.data);
  
  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// IndexedDBからの未同期データ取得（仮実装）
async function getUnsyncedData() {
  // TODO: IndexedDB実装
  return [];
}