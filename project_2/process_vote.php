<?php
// Enable error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        // Validate required fields
        if (empty($_POST['category'])) {
            throw new Exception("Category is required");
        }
        if (empty($_POST['language'])) {
            throw new Exception("Language is required");
        }
        if (empty($_POST['voter'])) {
            throw new Exception("Voter name is required");
        }

        // Sanitize inputs
        $category = htmlspecialchars(trim($_POST['category']));
        $language = htmlspecialchars(trim($_POST['language']));
        $voter = htmlspecialchars(trim($_POST['voter']));

        // Connect to SQLite
        $db = new SQLite3('votes.db', SQLITE3_OPEN_CREATE | SQLITE3_OPEN_READWRITE);
        
        // Set busy timeout
        $db->busyTimeout(5000);

        // Create table
        $db->exec("CREATE TABLE IF NOT EXISTS votes (
            category TEXT, 
            language TEXT, 
            voter TEXT, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )");

        // Insert vote
        $stmt = $db->prepare("INSERT INTO votes (category, language, voter) VALUES (:category, :language, :voter)");
        $stmt->bindValue(':category', $category);
        $stmt->bindValue(':language', $language);
        $stmt->bindValue(':voter', $voter);
        
        if (!$stmt->execute()) {
            throw new Exception("Failed to execute query");
        }

        // Get counts
        $stmt = $db->prepare("SELECT COUNT(*) FROM votes WHERE category = :category");
        $stmt->bindValue(':category', $category);
        $totalVotes = $stmt->execute()->fetchArray()[0];

        $stmt = $db->prepare("SELECT COUNT(*) FROM votes WHERE category = :category AND language = :language");
        $stmt->bindValue(':category', $category);
        $stmt->bindValue(':language', $language);
        $languageVotes = $stmt->execute()->fetchArray()[0];

        // Return response
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'success',
            'totalVotes' => $totalVotes,
            'languageVotes' => $languageVotes
        ]);

    } catch (Exception $e) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'error',
            'message' => $e->getMessage()
        ]);
    }
} else {
    http_response_code(405);
    echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
}