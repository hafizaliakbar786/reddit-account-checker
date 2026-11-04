import os
import re
from urllib.parse import urlsplit
from pathlib import Path
from dotenv import load_dotenv
from reddit_client import RedditClient, RedditAccessError
from datetime import datetime, timezone


from flask import Flask, request, render_template_string

app = Flask(__name__)

load_dotenv(Path(__file__).with_name(".env"))
reddit = RedditClient()
app.config["MAX_CONTENT_LENGTH"] = 16384

HTML_TEMPLATE = """
<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <title>Reddit Account Info Checker</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">

  <style>
    :root {
      --bg-dark: #050510;
      --card-dark: #111126;
      --accent-dark: #4f8cff;
      --accent-soft: #9c6bff;
      --text-dark: #f8f8ff;
      --muted-dark: #b0b4d4;
      --border-dark: #26263f;

      --bg-light: #f7f7ff;
      --card-light: #ffffff;
      --accent-light: #3d5afe;
      --accent-soft-light: #aa47ff;
      --text-light: #11111f;
      --muted-light: #5f637a;
      --border-light: #dadcf5;

      --radius-lg: 18px;
      --radius-pill: 999px;
      --shadow-soft: 0 22px 60px rgba(0,0,0,0.25);
      --shadow-light: 0 18px 40px rgba(15,23,42,0.22);

      --font-lg: 18px;
      --font-base: 17px;
      --font-sm: 15px;
      --font-xs: 13px;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html, body {
      height: 100%;
    }

    body {
      font-family: "Poppins", sans-serif;
      background: radial-gradient(circle at top left, #2a2a72, #050510 55%, #000000 100%);
      color: var(--text-dark);
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 20px;
    }

    html[data-theme="light"] body {
      background: radial-gradient(circle at top left, #ffffff, #dfe4ff 40%, #c9d3ff 80%);
      color: var(--text-light);
    }

    .app-shell {
      width: 100%;
      max-width: 1200px;
      background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(79,140,255,0.15));
      border-radius: 26px;
      padding: 20px;
      box-shadow: var(--shadow-soft);
      border: 1px solid rgba(255,255,255,0.12);
      backdrop-filter: blur(22px);
    }

    html[data-theme="light"] .app-shell {
      background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(231,235,255,0.98));
      box-shadow: var(--shadow-light);
      border: 1px solid rgba(15,23,42,0.06);
    }

    .header {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      margin-bottom: 20px;
    }

    .title-block {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .title {
      font-size: 26px;
      font-weight: 700;
      letter-spacing: 0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .title-pill {
      font-size: 11px;
      padding: 4px 10px;
      border-radius: 999px;
      background: linear-gradient(135deg, rgba(79,140,255,0.15), rgba(156,107,255,0.25));
      border: 1px solid rgba(156,107,255,0.6);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    html[data-theme="light"] .title-pill {
      background: linear-gradient(135deg, rgba(61,90,254,0.08), rgba(170,71,255,0.15));
      border-color: rgba(61,90,254,0.55);
    }

    .subtitle {
      font-size: var(--font-sm);
      color: var(--muted-dark);
    }

    html[data-theme="light"] .subtitle {
      color: var(--muted-light);
    }

    .controls {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }

    .theme-toggle {
      display: inline-flex;
      align-items: center;
      border-radius: var(--radius-pill);
      padding: 5px;
      background: rgba(0,0,0,0.22);
      border: 1px solid rgba(255,255,255,0.16);
      cursor: pointer;
      font-size: var(--font-sm);
    }

    html[data-theme="light"] .theme-toggle {
      background: rgba(255,255,255,0.9);
      border-color: rgba(15,23,42,0.08);
    }

    .theme-toggle span {
      padding: 5px 12px;
      border-radius: var(--radius-pill);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .theme-toggle span.active {
      background: linear-gradient(135deg, var(--accent-dark), var(--accent-soft));
      color: #ffffff;
    }

    html[data-theme="light"] .theme-toggle span.active {
      background: linear-gradient(135deg, var(--accent-light), var(--accent-soft-light));
    }

    .chip {
      font-size: 11px;
      padding: 4px 9px;
      border-radius: var(--radius-pill);
      background: rgba(0,0,0,0.28);
      border: 1px solid rgba(255,255,255,0.22);
      color: var(--muted-dark);
    }

    html[data-theme="light"] .chip {
      background: rgba(255,255,255,0.8);
      border-color: rgba(15,23,42,0.08);
      color: var(--muted-light);
    }

    .card {
      background: rgba(5,5,20,0.85);
      border-radius: var(--radius-lg);
      padding: 18px;
      border: 1px solid var(--border-dark);
      margin-bottom: 18px;
    }

    html[data-theme="light"] .card {
      background: var(--card-light);
      border-color: var(--border-light);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }

    .card-title {
      font-size: 18px;
      font-weight: 600;
    }

    .card-subtitle {
      font-size: var(--font-sm);
      color: var(--muted-dark);
    }

    html[data-theme="light"] .card-subtitle {
      color: var(--muted-light);
    }

    textarea {
      width: 100%;
      min-height: 120px;
      resize: vertical;
      border-radius: 14px;
      padding: 12px 14px;
      font-size: var(--font-base);
      background: rgba(0,0,0,0.45);
      color: var(--text-dark);
      border: 1px solid rgba(255,255,255,0.15);
      outline: none;
      line-height: 1.5;
    }

    html[data-theme="light"] textarea {
      background: rgba(255,255,255,0.98);
      color: var(--text-light);
      border-color: rgba(15,23,42,0.12);
    }

    textarea::placeholder {
      color: rgba(176,180,212,0.8);
    }

    html[data-theme="light"] textarea::placeholder {
      color: rgba(95,99,122,0.88);
    }

    .hint {
      margin-top: 6px;
      font-size: var(--font-sm);
      color: var(--muted-dark);
    }

    html[data-theme="light"] .hint {
      color: var(--muted-light);
    }

    .btn-row {
      display: flex;
      justify-content: flex-end;
      margin-top: 12px;
    }

    .btn-primary {
      padding: 10px 20px;
      border-radius: var(--radius-pill);
      border: none;
      font-size: var(--font-base);
      font-weight: 600;
      cursor: pointer;
      background: linear-gradient(135deg, #4f8cff, #9c6bff);
      color: #ffffff;
      box-shadow: 0 12px 30px rgba(79,140,255,0.5);
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .btn-primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 16px 40px rgba(79,140,255,0.65);
    }

    .btn-primary:active {
      transform: translateY(0);
      box-shadow: 0 8px 20px rgba(79,140,255,0.4);
    }

    .btn-icon {
      font-size: 18px;
    }

    .results-card {
      margin-top: 6px;
    }

    .results-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      font-size: var(--font-sm);
      color: var(--muted-dark);
    }

    html[data-theme="light"] .results-meta {
      color: var(--muted-light);
    }

    .results-meta strong {
      font-size: var(--font-base);
      color: inherit;
    }

    .table-wrapper {
      width: 100%;
      overflow-x: auto;
      border-radius: 16px;
      border: 1px solid var(--border-dark);
      background: radial-gradient(circle at top left, rgba(79,140,255,0.08), rgba(5,5,25,0.88));
    }

    html[data-theme="light"] .table-wrapper {
      border-color: var(--border-light);
      background: radial-gradient(circle at top left, rgba(61,90,254,0.05), rgba(255,255,255,0.98));
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: var(--font-base);
    }

    thead {
      background: linear-gradient(135deg, rgba(79,140,255,0.45), rgba(156,107,255,0.35));
      color: #ffffff;
    }

    html[data-theme="light"] thead {
      background: linear-gradient(135deg, rgba(61,90,254,0.8), rgba(170,71,255,0.7));
    }

    th, td {
      padding: 10px 12px;
      text-align: left;
      white-space: nowrap;
    }

    th {
      font-size: 15px;
      font-weight: 600;
      border-bottom: 1px solid rgba(0,0,0,0.12);
    }

    tbody tr {
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    html[data-theme="light"] tbody tr {
      border-bottom: 1px solid rgba(15,23,42,0.06);
    }

    tbody tr:nth-child(even) {
      background: rgba(255,255,255,0.02);
    }

    html[data-theme="light"] tbody tr:nth-child(even) {
      background: rgba(15,23,42,0.02);
    }

    .username-cell {
      font-weight: 600;
      font-size: 17px;
    }

    .karma-cell {
      font-variant-numeric: tabular-nums;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 500;
    }

    .status-active {
      background: rgba(34,197,94,0.16);
      color: #4ade80;
      border: 1px solid rgba(34,197,94,0.6);
    }

    .status-inactive {
      background: rgba(245,158,11,0.16);
      color: #fbbf24;
      border: 1px solid rgba(245,158,11,0.65);
    }

    .status-error {
      background: rgba(248,113,113,0.16);
      color: #fb7185;
      border: 1px solid rgba(248,113,113,0.7);
    }

    .btn-overview {
      padding: 7px 14px;
      border-radius: var(--radius-pill);
      border: none;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      background: rgba(79,140,255,0.12);
      color: var(--accent-dark);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      text-decoration: none;
    }

    html[data-theme="light"] .btn-overview {
      background: rgba(61,90,254,0.12);
      color: var(--accent-light);
    }

    .btn-overview:hover {
      background: rgba(79,140,255,0.22);
    }

    .btn-overview.disabled {
      opacity: 0.5;
      cursor: not-allowed;
      background: rgba(148,163,184,0.18);
      color: rgba(148,163,184,0.8);
    }

    .small-note {
      margin-top: 8px;
      font-size: 12px;
      color: var(--muted-dark);
    }

    html[data-theme="light"] .small-note {
      color: var(--muted-light);
    }

    .error-banner {
      margin-top: 10px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(248,113,113,0.6);
      background: rgba(127,29,29,0.5);
      color: #fecaca;
      font-size: 13px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    html[data-theme="light"] .error-banner {
      background: #fef2f2;
      color: #b91c1c;
      border-color: #fecaca;
    }

    .error-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #f97373;
    }

    @media (max-width: 768px) {
      .title {
        font-size: 22px;
      }

      th, td {
        padding: 8px 10px;
      }

      .app-shell {
        padding: 14px;
      }
    }
    /* White and orange theme */
html[data-theme] {
  --text-dark: #202124;
  --text-light: #202124;
  --muted-dark: #667085;
  --muted-light: #667085;
  --border-dark: #e5e7eb;
  --border-light: #e5e7eb;
  --accent-dark: #c43b00;
  --accent-light: #c43b00;
}

html[data-theme] body {
  background: #f6f7f8;
  color: #202124;
}

html[data-theme] .app-shell {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 12px 36px rgba(16, 24, 40, 0.08);
  backdrop-filter: none;
}

html[data-theme] .title {
  color: #c43b00;
}

html[data-theme] .title-pill {
  background: #fff1e8;
  color: #a83200;
  border-color: #ffcfb8;
}

html[data-theme] .card {
  background: #ffffff;
  border-color: #e5e7eb;
}

html[data-theme] textarea {
  background: #fafafa;
  color: #202124;
  border: 1px solid #d0d5dd;
}

html[data-theme] textarea::placeholder {
  color: #667085;
}

html[data-theme] textarea:focus {
  border-color: #e64400;
  box-shadow: 0 0 0 3px rgba(230, 68, 0, 0.12);
}

html[data-theme] .btn-primary {
  background: linear-gradient(135deg, #c43b00, #e64400);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(196, 59, 0, 0.18);
}

html[data-theme] .btn-primary:hover {
  background: #b53600;
  box-shadow: 0 6px 16px rgba(196, 59, 0, 0.24);
}

html[data-theme] .chip {
  background: #f9fafb;
  color: #667085;
  border-color: #e5e7eb;
}

html[data-theme] .table-wrapper {
  background: #ffffff;
  border-color: #e5e7eb;
}

html[data-theme] thead {
  background: #fff1e8;
  color: #9a3000;
}

html[data-theme] th {
  border-bottom: 1px solid #ffd6c2;
}

html[data-theme] tbody tr {
  border-bottom: 1px solid #eef0f2;
}

html[data-theme] tbody tr:nth-child(even) {
  background: #fafafa;
}

html[data-theme] tbody tr:hover {
  background: #fff8f3;
}

html[data-theme] .btn-overview {
  background: #fff1e8;
  color: #a83200;
}

html[data-theme] .btn-overview:hover {
  background: #ffe0cc;
}

html[data-theme] .btn-overview.disabled {
  background: #f2f4f7;
  color: #667085;
  opacity: 1;
}

html[data-theme] .status-active {
  background: #ecfdf3;
  color: #166534;
  border-color: #a7e3bc;
}

html[data-theme] .status-inactive {
  background: #fffbeb;
  color: #92400e;
  border-color: #fcd68a;
}

html[data-theme] .status-error,
html[data-theme] .error-banner {
  background: #fff1f2;
  color: #b42318;
  border-color: #fecdd3;
}

/* Hide theme switch while using the fixed white theme */
html[data-theme] .theme-toggle {
  display: none;
}
  </style>
</head>
<body>
  <div class="app-shell">
    <div class="header">
      <div class="title-block">
        <div class="title">
          Reddit Account Info Checker
          <span class="title-pill">Multi account · Live data</span>
        </div>
        <div class="subtitle">
          Paste up to 10 Reddit usernames. Get post karma, comment karma, age, status, and quick overview links.
        </div>
      </div>
      <div class="controls">
        <div class="theme-toggle" id="theme-toggle">
          <span id="theme-dark" class="active">
            🌙 Dark
          </span>
          <span id="theme-light">
            ☀️ Light
          </span>
        </div>
        <span class="chip">
          Large font · Clean rows & columns
        </span>
      </div>
    </div>

    <form method="post">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Usernames input</div>
        </div>
        <textarea name="usernames" placeholder="Example:
u/example_user
example_user2
example_user3" required>{{ usernames_text or "" }}</textarea>
        <div class="hint">
          Put one username per line. Both <strong>u/username</strong> and <strong>username</strong> formats are accepted.
        </div>
        <div class="btn-row">
          <button type="submit" class="btn-primary">
            <span class="btn-icon">🔍</span>
            <span>Check accounts</span>
          </button>
        </div>
        {% if error_message %}
        <div class="error-banner">
          <span class="error-dot"></span>
          <span>{{ error_message }}</span>
        </div>
        {% endif %}
      </div>
    </form>

    {% if results %}
    <div class="card results-card">
      <div class="results-meta">
        <div>
          <strong>{{ results|length }}</strong> account(s) checked.
        </div>
        <div>
          Available profiles have a <strong>View overview</strong> button.
        </div>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Post karma</th>
              <th>Comment karma</th>
              <th>Total karma</th>
              <th>Account age</th>
              <th>Status</th>
              <th>Overview</th>
            </tr>
          </thead>
          <tbody>
          {% for r in results %}
            <tr>
              <td class="username-cell">{{ r.username }}</td>
              <td class="karma-cell">{{ r.post_karma }}</td>
              <td class="karma-cell">{{ r.comment_karma }}</td>
              <td class="karma-cell">{{ r.total_karma }}</td>
              <td>{{ r.age }}</td>
              <td>
                <span class="status-pill
                  {% if r.status_code == "active" %}status-active
                  {% elif r.status_code == "inactive" %}status-inactive
                  {% else %}status-error{% endif %}">
                  {{ r.status_text }}
                </span>
              </td>
              <td>
                {% if r.overview_url and r.status_code == "active" %}
                  <a href="{{ r.overview_url }}" target="_blank" rel="noopener noreferrer" class="btn-overview">
                    <span>View overview</span> ↗
                  </a>
                {% else %}
                  <button class="btn-overview disabled" type="button" disabled>
                    Not available
                  </button>
                {% endif %}
              </td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="small-note">
        Note: Karma does not establish account activity. Access errors do not establish account bans.
      </div>
    </div>
    {% endif %}
  </div>

  <script>
    const htmlEl = document.documentElement;
    const toggle = document.getElementById("theme-toggle");
    const darkBtn = document.getElementById("theme-dark");
    const lightBtn = document.getElementById("theme-light");

    function applyTheme(theme) {
      if (theme === "light") {
        htmlEl.setAttribute("data-theme", "light");
        lightBtn.classList.add("active");
        darkBtn.classList.remove("active");
      } else {
        htmlEl.setAttribute("data-theme", "dark");
        darkBtn.classList.add("active");
        lightBtn.classList.remove("active");
      }
      localStorage.setItem("reddit_checker_theme", theme);
    }

    const savedTheme = localStorage.getItem("reddit_checker_theme");
    if (savedTheme === "light" || savedTheme === "dark") {
      applyTheme(savedTheme);
    }

    toggle.addEventListener("click", function(event) {
      const current = htmlEl.getAttribute("data-theme") || "dark";
      if (current === "dark") {
        applyTheme("light");
      } else {
        applyTheme("dark");
      }
    });
  </script>
</body>
</html>
"""

def normalize_username(name: str) -> str:
    name = name.strip()
    if not name:
        return ""
    if name.startswith(("https://", "http://")):
        parsed = urlsplit(name)
        if parsed.hostname not in {"reddit.com", "www.reddit.com", "old.reddit.com"}:
            raise ValueError("Only Reddit profile links are accepted.")
        parts = parsed.path.strip("/").split("/")
        if len(parts) != 2 or parts[0].lower() not in {"u", "user"}:
            raise ValueError("Enter a Reddit profile URL, not a post URL.")
        name = parts[1]
    name = re.sub(r"^/?u/", "", name, flags=re.I)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,20}", name):
        raise ValueError("Invalid username. Use letters, digits, underscore or hyphen; maximum 20 characters.")
    return name

def format_age(created_utc: float) -> str:
    try:
        created_dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
    except Exception:
        return "Unknown"

    now = datetime.now(tz=timezone.utc)
    delta = now - created_dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} seconds"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} minutes"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hours"
    days = hours / 24
    if days < 60:
        return f"{int(days)} days"
    months = days / 30.4375
    if months < 24:
        return f"{int(months)} months"
    years = months / 12
    return f"{years:.1f} years"

def detect_status_and_data(username: str) -> dict:
    """
    Fetch account info from Reddit.
    Tries to classify status as:
      - active
      - inactive (no posts/comments yet)
      - error (suspended / banned / deleted / not found / API error)
    """
    base_result = {
        "username": username,
        "post_karma": "-",
        "comment_karma": "-",
        "total_karma": "-",
        "age": "Unknown",
        "status_text": "Error",
        "status_code": "error",
        "overview_url": None
    }

    try:
        data = reddit.about(username)
        if data.get("is_suspended"):
            base_result["status_text"] = "Suspended (reported by Reddit)"
            return base_result
        values = [data[key] for key in ("link_karma", "comment_karma", "total_karma")]
        if not all(type(value) is int for value in values):
            raise ValueError()
        created = data["created_utc"]
        if type(created) not in (int, float) or not 0 <= created <= datetime.now(timezone.utc).timestamp():
            raise ValueError()
        age = format_age(created)
        if age == "Unknown":
            raise ValueError()
    except RedditAccessError as error:
        base_result["status_text"] = str(error)
        return base_result
    except (KeyError, TypeError, ValueError):
        base_result["status_text"] = "Incomplete profile data; karma unavailable"
        return base_result
    base_result.update(post_karma=values[0], comment_karma=values[1],
        total_karma=values[2], age=age, status_text="Profile available",
        status_code="active", overview_url=f"https://www.reddit.com/user/{username}/")

    return base_result

@app.route("/", methods=["GET", "POST"])
def index():
    usernames_text = ""
    results = []
    error_message = None

    if request.method == "POST":
        usernames_text = request.form.get("usernames", "")
        raw_lines = usernames_text.splitlines()
        try:
            cleaned = [normalize_username(line) for line in raw_lines]
        except ValueError as error:
            return render_template_string(HTML_TEMPLATE, usernames_text=usernames_text,
                results=[], error_message=str(error))
        cleaned = [u for u in cleaned if u]
        cleaned = list({u.lower(): u for u in reversed(cleaned)}.values())[::-1]  # dedupe, keep order

        if not cleaned:
            error_message = "Please enter at least one valid username."
        else:
            if len(cleaned) > 10:
                cleaned = cleaned[:10]
                error_message = "Limited to 10 usernames per check while API access is verified."

            results = [detect_status_and_data(u) for u in cleaned]

            # preserve original order by re-sorting
            order_map = {name: idx for idx, name in enumerate(cleaned)}
            results.sort(key=lambda r: order_map.get(r["username"], 0))

    return render_template_string(
        HTML_TEMPLATE,
        usernames_text=usernames_text,
        results=results,
        error_message=error_message
    )

@app.after_request
def prevent_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port)
