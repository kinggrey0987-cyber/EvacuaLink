<?php
$title = "EvacuaLink";
$year = date("Y");
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title><?php echo $title; ?> - Home</title>
    <style>
        :root {
            --bg: #0f172a;
            --card: #111827;
            --text: #e5e7eb;
            --muted: #9ca3af;
            --accent: #22c55e;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: linear-gradient(135deg, #0b1024, var(--bg));
            color: var(--text);
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 24px;
        }
        .card {
            width: min(760px, 100%);
            background: rgba(17, 24, 39, 0.92);
            border: 1px solid #1f2937;
            border-radius: 14px;
            padding: 28px;
            box-shadow: 0 10px 30px rgba(0,0,0,.35);
        }
        h1 { margin: 0 0 10px; font-size: 2rem; }
        p { margin: 0 0 18px; color: var(--muted); line-height: 1.6; }
        .actions { display: flex; gap: 12px; flex-wrap: wrap; }
        .btn {
            display: inline-block;
            text-decoration: none;
            color: #0b1024;
            background: var(--accent);
            padding: 10px 16px;
            border-radius: 10px;
            font-weight: bold;
        }
        .btn.secondary {
            background: transparent;
            color: var(--text);
            border: 1px solid #374151;
        }
        footer {
            margin-top: 22px;
            color: var(--muted);
            font-size: .9rem;
        }
    </style>
</head>
<body>
    <main class="card">
        <h1>Welcome to <?php echo $title; ?></h1>
        <p>
            This is a sample homepage template in PHP. Replace this content with your
            real project sections (services, announcements, contact, and dashboard links).
        </p>

        <div class="actions">
            <a class="btn" href="#">Get Started</a>
            <a class="btn secondary" href="#">Learn More</a>
        </div>

        <footer>© <?php echo $year; ?> <?php echo $title; ?>. All rights reserved.</footer>
    </main>
</body>
</html>