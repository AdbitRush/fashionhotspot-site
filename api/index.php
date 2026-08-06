<?php
/**
 * fashionhotspot.site REST API Bridge
 * 
 * Forward API requests from the static site to the whatsapp bot backend.
 * The backend runs on the VPS at 178.105.148.72:3002
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

define('API_BACKEND', 'http://178.105.148.72:3002');
define('API_TIMEOUT', 10);

$path = $_GET['path'] ?? '';
$action = $_GET['action'] ?? '';

// --- Routes ---
$routes = [
    'deals'    => '/store?format=json&limit=50',
    'health'   => '/health',
    'deals/amazon' => '/store?platform=amazon&format=json&limit=30',
    'deals/aliexpress' => '/store?platform=aliexpress&format=json&limit=30',
];

// Match route
$backendPath = null;
if ($path && isset($routes[$path])) {
    $backendPath = $routes[$path];
} elseif ($action === 'search') {
    $q = urlencode($_GET['q'] ?? '');
    $backendPath = "/store?search={$q}&format=json&limit=20";
} elseif ($action === 'latest') {
    $backendPath = '/store?format=json&limit=10';
}

if (!$backendPath) {
    http_response_code(404);
    echo json_encode(['error' => 'Unknown endpoint', 'available' => array_keys($routes)]);
    exit;
}

// Forward request to backend
$url = API_BACKEND . $backendPath;

$ch = curl_init();
curl_setopt_array($ch, [
    CURLOPT_URL => $url,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => API_TIMEOUT,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_USERAGENT => 'fashionhotspot-api-bridge/1.0',
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($error) {
    http_response_code(502);
    echo json_encode(['error' => 'Backend unavailable', 'detail' => $error]);
    exit;
}

http_response_code($httpCode);
echo $response;
