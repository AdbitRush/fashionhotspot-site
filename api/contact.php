<?php
/**
 * Submit contact form — sends message to WhatsApp admin group via bot
 */
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'POST required']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$name = trim($input['name'] ?? '');
$email = trim($input['email'] ?? '');
$message = trim($input['message'] ?? '');

if (!$name || !$email || !$message) {
    http_response_code(400);
    echo json_encode(['error' => 'name, email, and message are required']);
    exit;
}

// Forward to WhatsApp bot admin endpoint
$payload = json_encode([
    'source' => 'fashionhotspot.site',
    'type' => 'contact',
    'name' => $name,
    'email' => $email,
    'message' => $message,
    'ip' => $_SERVER['REMOTE_ADDR'] ?? '',
]);

$ch = curl_init('http://178.105.148.72:3001/api/notify');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => $payload,
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_TIMEOUT => 10,
]);
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode >= 200 && $httpCode < 300) {
    echo json_encode(['status' => 'ok', 'message' => 'Message sent! We\'ll get back to you soon.']);
} else {
    http_response_code(502);
    echo json_encode(['error' => 'Failed to send message', 'code' => $httpCode]);
}
