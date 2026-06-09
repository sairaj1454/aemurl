from flask import Flask, request, render_template_string
from urllib.parse import urlparse, urlunparse, urljoin
import json
import os
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

CACHE_FILE = "stats_cache.json"

# Predefined environments mapping
DOMAINS = {
    "qa": "qa-author.honeywellaerospace.com",
    "stage": "stage-author.honeywellaerospace.com",
    "prod": "author.honeywellaerospace.com",
    "local": "localhost:4502",
    "custom": ""  
}

def load_cached_stats():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                return data.get("total_processed", 0)
        except Exception:
            return 0
    return 0

def update_cached_stats(count_to_add):
    current_total = load_cached_stats()
    new_total = current_total + count_to_add
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"total_processed": new_total}, f)
    except Exception as e:
        print(f"Cache write error: {e}")
    return new_total

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Advanced AEM URL Transformer & Deep Image Scraper</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; max-width: 1000px; color: #333; background-color: #fcfcfc; }
        h2 { color: #222; border-bottom: 2px solid #007bff; padding-bottom: 8px; margin-bottom: 15px; }
        h3 { color: #333; margin-top: 0; }
        
        .stats-dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .stat-box { background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 15px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .stat-val { font-size: 24px; font-weight: bold; color: #2b6cb0; margin-bottom: 4px; }
        .stat-label { font-size: 13px; color: #718096; font-weight: 500; }
        .time-saved { color: #2f855a; }
        
        .section-container { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.01); }
        .section-title { font-size: 16px; font-weight: bold; color: #0056b3; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;}

        .input-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .input-group { display: flex; flex-direction: column; }
        .input-group label { font-weight: bold; margin-bottom: 8px; font-size: 14px; color: #495057; }
        textarea, input[type="url"] { width: 100%; font-family: monospace; padding: 12px; box-sizing: border-box; border: 1px solid #ced4da; border-radius: 4px; resize: vertical; }
        textarea { height: 140px; }
        textarea:focus, input[type="url"]:focus { border-color: #80bdff; outline: 0; box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25); }
        
        .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; background: #f1f3f5; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef; }
        .option-group { display: flex; flex-direction: column; }
        .option-group label { font-weight: bold; margin-bottom: 6px; font-size: 14px; }
        select, input[type="text"] { padding: 8px; border: 1px solid #ccc; border-radius: 4px; background-color: white; font-size: 14px; }
        .custom-domain-container { margin-top: 10px; }
        .custom-domain-container input { padding: 8px; width: 100%; font-family: monospace; box-sizing: border-box; }
        .checkbox-group { display: flex; align-items: center; gap: 10px; margin-top: 10px; font-size: 14px; }
        .checkbox-group input { width: 16px; height: 16px; cursor: pointer; }
        
        .replace-pair-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 5px; }
        .replace-pair-grid input { font-family: monospace; width: 100%; box-sizing: border-box; }

        .btn-primary { padding: 12px 28px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 15px; font-weight: 600; transition: background 0.2s; }
        .btn-primary:hover { background-color: #0056b3; }
        .btn-secondary { padding: 6px 12px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; min-width: 65px; transition: background 0.2s; }
        .btn-secondary:hover { background-color: #5a6268; }
        .btn-danger { padding: 6px 12px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; min-width: 65px; transition: background 0.2s; }
        .btn-danger:hover { background-color: #bd2130; }
        .btn-copy-all { padding: 6px 14px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 600; transition: background 0.2s; }
        .btn-copy-all:hover { background-color: #218838; }
        
        .actions-container { display: flex; gap: 6px; align-items: center; }
        .results-controls { display: flex; align-items: center; gap: 20px; }
        
        .toggle-container { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: #495057; background: #e9ecef; padding: 6px 12px; border-radius: 4px; border: 1px solid #ced4da; }
        .toggle-container input { cursor: pointer; width: 15px; height: 15px; }

        .results-box { margin-top: 25px; border-top: 2px solid #dee2e6; padding-top: 20px; }
        .results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        
        .result-group-block { background: #fdfdfd; border: 1px solid #e2e8f0; border-radius: 6px; padding: 15px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
        .result-group-title { font-size: 13px; font-weight: bold; color: #4a5568; margin-bottom: 10px; border-bottom: 1px dashed #cbd5e0; padding-bottom: 4px; }
        
        .result-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 10px 12px; background-color: #ffffff; border: 1px solid #edf2f7; border-radius: 4px; font-family: monospace; font-size: 13px; }
        
        .type-original { border-left: 5px solid #007bff; }
        .type-migrated { border-left: 5px solid #28a745; }
        .type-legacy { border-left: 5px solid #ffc107; }
        .type-image { border-left: 5px solid #17a2b8; }
        
        .result-url { word-break: break-all; flex-grow: 1; padding-right: 15px; }
        .result-url a { color: #1a0dab; text-decoration: none; }
        .result-url a:hover { text-decoration: underline; }
        .url-badge { font-size: 11px; font-weight: bold; text-transform: uppercase; padding: 2px 6px; border-radius: 3px; margin-right: 8px; display: inline-block; vertical-align: middle; min-width: 90px; text-align: center; }
        .badge-original { background-color: #ebf8ff; color: #2b6cb0; }
        .badge-migrated { background-color: #f0fff4; color: #22543d; }
        .badge-legacy { background-color: #fffaf0; color: #744210; }
        .badge-image { background-color: #e3f2fd; color: #006699; }

        .alert-error { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 12px; border-radius: 4px; margin-bottom: 20px; font-size: 14px;}
    </style>
    <script>
        function toggleCustomInput() {
            var envSelect = document.getElementById("env");
            var customContainer = document.getElementById("custom_domain_container");
            if (envSelect && envSelect.value === "custom") {
                customContainer.style.display = "block";
                document.getElementById("custom_domain").required = true;
            } else if (customContainer) {
                customContainer.style.display = "none";
                document.getElementById("custom_domain").required = false;
            }
        }

        function copyToClipboard(text, button) {
            navigator.clipboard.writeText(text).then(function() {
                var originalText = button.innerText;
                button.innerText = "Copied!";
                button.style.backgroundColor = "#28a745";
                
                var autoDeleteToggle = document.getElementById("auto_delete_toggle");
                var autoDeleteEnabled = autoDeleteToggle ? autoDeleteToggle.checked : false;
                
                if (autoDeleteEnabled) {
                    setTimeout(function() {
                        deleteRow(button);
                    }, 400);
                } else {
                    setTimeout(function() {
                        button.innerText = originalText;
                        button.style.backgroundColor = "";
                    }, 1500);
                }
            });
        }

        function deleteRow(button) {
            var row = button.closest('.result-item');
            var parentBlock = button.closest('.result-group-block');
            if (row) { row.remove(); }
            
            if (parentBlock && parentBlock.querySelectorAll('.result-item').length === 0) {
                parentBlock.remove();
            }
        }

        function copyAllUrls() {
            var links = document.querySelectorAll('.result-url-link');
            var urls = [];
            links.forEach(function(link) { urls.push(link.href); });
            
            var joinString = urls.join('\n');
            var copyAllBtn = document.getElementById('copy_all_btn');
            
            navigator.clipboard.writeText(joinString).then(function() {
                var originalText = copyAllBtn.innerText;
                copyAllBtn.innerText = "All Links Copied!";
                copyAllBtn.style.backgroundColor = "#1e7e34";
                setTimeout(function() {
                    copyAllBtn.innerText = originalText;
                    copyAllBtn.style.backgroundColor = "";
                }, 2000);
            });
        }

        window.onload = toggleCustomInput;
    </script>
</head>
<body>
    <h2>Advanced AEM URL Transformer & Deep Inspector</h2>
    
    <div class="stats-dashboard">
        <div class="stat-box">
            <span class="stat-val">{{ total_processed }}</span>
            <span class="stat-label">Total Core Transformation Pairs Processed</span>
        </div>
        <div class="stat-box">
            <span class="stat-val time-saved">{{ hours_saved }}h {{ mins_saved }}m</span>
            <span class="stat-label">Estimated Manual Entry Time Saved (1.5 min / pair)</span>
        </div>
    </div>

    {% if error_msg %}
    <div class="alert-error">
        ❌ <strong>Error:</strong> {{ error_msg }}
    </div>
    {% endif %}

    <div class="section-container">
        <div class="section-title">🔍 Feature: Deep Inspect & Scrape All Images (Src, Srcset, Lazy Data, CSS Backgrounds)</div>
        <form method="POST" action="/">
            <input type="hidden" name="action_type" value="extract_images">
            <div class="input-group">
                <label for="scrape_url">Target Webpage URL to Scrape:</label>
                <div style="display: flex; gap: 10px;">
                    <input type="url" id="scrape_url" name="scrape_url" placeholder="https://example.com/page.html" required value="{{ scraped_target_url }}">
                    <input type="submit" class="btn-primary" value="Inspect & Extract" style="padding: 0 20px; white-space: nowrap;">
                </div>
            </div>
        </form>
    </div>
    
    <div class="section-container">
        <div class="section-title">🚀 Feature: Batch URL Transformation & Pairing</div>
        <form method="POST" action="/">
            <input type="hidden" name="action_type" value="transform_urls">
            
            <div class="input-grid">
                <div class="input-group">
                    <label for="url_input">1. Original URLs / Paths (One per line):</label>
                    <textarea name="url_input" id="url_input" placeholder="/content/aerobt/us/en/page1"></textarea>
                </div>
                <div class="input-group">
                    <label for="legacy_input">2. Corresponding Legacy URLs / Plain Paths (One per line):</label>
                    <textarea name="legacy_input" id="legacy_input" placeholder="/content/legacy/us/en/old-page1"></textarea>
                </div>
            </div>
            
            <div class="options-grid">
                <div class="option-group">
                    <label for="env">Target Environment / Domain:</label>
                    <select name="env" id="env" onchange="toggleCustomInput()">
                        <option value="qa" {% if selected_opts.env == 'qa' %}selected{% endif %}>QA Author</option>
                        <option value="stage" {% if selected_opts.env == 'stage' %}selected{% endif %}>Stage Author</option>
                        <option value="prod" {% if selected_opts.env == 'prod' %}selected{% endif %}>Prod Author</option>
                        <option value="local" {% if selected_opts.env == 'local' %}selected{% endif %}>Local SDK (localhost:4502)</option>
                        <option value="custom" {% if selected_opts.env == 'custom' %}selected{% endif %}>Use Custom Domain...</option>
                    </select>
                    
                    <div id="custom_domain_container" class="custom-domain-container" style="display: none;">
                        <input type="text" id="custom_domain" name="custom_domain" placeholder="e.g., dev-author.company.com" value="{{ selected_opts.custom_domain }}">
                    </div>
                </div>
                
                <div class="option-group">
                    <label for="editor_action">Editor Configuration:</label>
                    <select name="editor_action" id="editor_action">
                        <option value="force_add" {% if selected_opts.editor_action == 'force_add' %}selected{% endif %}>Force add /editor.html</option>
                        <option value="keep" {% if selected_opts.editor_action == 'keep' %}selected{% endif %}>Preserve original layout behavior</option>
                        <option value="force_remove" {% if selected_opts.editor_action == 'force_remove' %}selected{% endif %}>Force remove /editor.html</option>
                    </select>
                </div>

                <div class="option-group" style="grid-column: span 2;">
                    <label>Migrated URL Path Text Replacement (Optional):</label>
                    <div class="replace-pair-grid">
                        <input type="text" name="find_text" placeholder="Find segment" value="{{ selected_opts.find_text }}">
                        <input type="text" name="migrated_replace" placeholder="Replace with" value="{{ selected_opts.migrated_replace }}">
                    </div>
                </div>
            </div>

            <div class="checkbox-group">
                <input type="checkbox" id="use_http" name="use_http" value="true" {% if selected_opts.use_http %}checked{% endif %}>
                <label for="use_http">Force HTTP protocol mapping instead of HTTPS</label>
            </div>
            <br>
            <input type="submit" class="btn-primary" value="Transform & Pair URLs">
        </form>
    </div>
    
    {% if image_data %}
    <div class="results-box">
        <div class="results-header">
            <h3>All Discovered Page Images (Total: {{ image_data|length }}):</h3>
            <button id="copy_all_btn" class="btn-copy-all" onclick="copyAllUrls()">Copy All Image Links</button>
        </div>
        <div class="result-group-block">
            <div class="result-group-title">Source Page Explored: <span style="font-family: monospace; color:#0056b3;">{{ scraped_target_url }}</span></div>
            {% for item in image_data %}
            <div class="result-item type-image">
                <div class="result-url">
                    <span class="url-badge badge-image">{{ item.type }}</span>
                    <a href="{{ item.url }}" target="_blank" class="result-url-link">{{ item.url }}</a>
                </div>
                <div class="actions-container">
                    <button class="btn-secondary" onclick="copyToClipboard('{{ item.url }}', this)">Copy</button>
                    <button class="btn-danger" onclick="deleteRow(this)">Delete</button>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    {% if detailed_groups %}
    <div class="results-box">
        <div class="results-header">
            <h3>Transformed & Paired Results:</h3>
            <div class="results-controls">
                <div class="toggle-container">
                    <input type="checkbox" id="auto_delete_toggle" name="auto_delete_toggle">
                    <label for="auto_delete_toggle">Auto-Delete on Copy</label>
                </div>
                <button id="copy_all_btn" class="btn-copy-all" onclick="copyAllUrls()">Copy All Generated Links</button>
            </div>
        </div>
        
        {% for group in detailed_groups %}
            <div class="result-group-block">
                <div class="result-group-title">URL Batch Pair #{{ loop.index }}</div>
                
                <div class="result-item type-original">
                    <div class="result-url">
                        <span class="url-badge badge-original">Original</span>
                        <a href="{{ group.original }}" target="_blank" class="result-url-link">{{ group.original }}</a>
                    </div>
                    <div class="actions-container">
                        <button class="btn-secondary" onclick="copyToClipboard('{{ group.original }}', this)">Copy</button>
                        <button class="btn-danger" onclick="deleteRow(this)">Delete</button>
                    </div>
                </div>

                <div class="result-item type-migrated">
                    <div class="result-url">
                        <span class="url-badge badge-migrated">Migrated</span>
                        <a href="{{ group.migrated }}" target="_blank" class="result-url-link">{{ group.migrated }}</a>
                    </div>
                    <div class="actions-container">
                        <button class="btn-secondary" onclick="copyToClipboard('{{ group.migrated }}', this)">Copy</button>
                        <button class="btn-danger" onclick="deleteRow(this)">Delete</button>
                    </div>
                </div>

                {% if group.legacy %}
                <div class="result-item type-legacy">
                    <div class="result-url">
                        <span class="url-badge badge-legacy">Legacy</span>
                        <a href="{{ group.legacy }}" target="_blank" class="result-url-link">{{ group.legacy }}</a>
                    </div>
                    <div class="actions-container">
                        <button class="btn-secondary" onclick="copyToClipboard('{{ group.legacy }}', this)">Copy</button>
                        <button class="btn-danger" onclick="deleteRow(this)">Delete</button>
                    </div>
                </div>
                {% endif %}
            </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
"""

def transform_migrated_url(input_str, env, custom_domain, editor_action, use_http, find_text, replace_text):
    if not input_str: return ""
    input_str = input_str.strip()
    target_domain = custom_domain.replace("http://", "").replace("https://", "").strip("/") if (env == "custom" and custom_domain) else DOMAINS.get(env, DOMAINS["qa"])
    scheme = "http" if use_http or env == "local" else "https"
    
    if input_str.startswith("http://") or input_str.startswith("https://"):
        parsed = urlparse(input_str)
        if env == "custom" and not custom_domain:
            target_domain = parsed.netloc
            scheme = parsed.scheme
        path = parsed.path
    else:
        path = input_str if input_str.startswith("/") else f"/{input_str}"

    if find_text and (find_text in path):
        path = path.replace(find_text, replace_text)

    is_editor = path.startswith("/editor.html")
    clean_path = path.replace("/editor.html", "", 1) if is_editor else path

    if editor_action == "force_add":
        path = f"/editor.html{clean_path}"
    elif editor_action == "force_remove":
        path = clean_path
    else:
        path = f"/editor.html{clean_path}" if is_editor else clean_path

    if not path.endswith(".html"):
        path = f"{path}.html"
    return urlunparse((scheme, target_domain, path, '', '', ''))

def format_legacy_url(input_str, env, custom_domain, use_http):
    if not input_str: return ""
    input_str = input_str.strip()
    if input_str.startswith("http://") or input_str.startswith("https://"):
        return input_str
    target_domain = custom_domain.replace("http://", "").replace("https://", "").strip("/") if (env == "custom" and custom_domain) else DOMAINS.get(env, DOMAINS["qa"])
    scheme = "http" if use_http or env == "local" else "https"
    path = input_str if input_str.startswith("/") else f"/{input_str}"
    if not path.endswith(".html"):
        path = f"{path}.html"
    return urlunparse((scheme, target_domain, path, '', '', ''))

@app.route('/', methods=['GET', 'POST'])
def home():
    detailed_groups = []
    image_data = []
    scraped_target_url = ""
    error_msg = ""
    
    selected_opts = {
        "env": "qa", "custom_domain": "", "editor_action": "force_add",
        "use_http": False, "find_text": "", "migrated_replace": ""
    }
    
    total_processed = load_cached_stats()
    
    if request.method == 'POST':
        action_type = request.form.get('action_type', 'transform_urls')
        
        # --- NEW DEEP INSPECTOR LOGIC ---
        if action_type == 'extract_images':
            scraped_target_url = request.form.get('scrape_url', '').strip()
            if scraped_target_url:
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    response = requests.get(scraped_target_url, headers=headers, timeout=12)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        seen_urls = set()
                        
                        def register_url(raw_url, label):
                            if not raw_url: return
                            raw_url = raw_url.strip()
                            # Clean wrapper punctuation sometimes found in data-attributes or CSS strings
                            raw_url = raw_url.strip("'\"() ")
                            if not raw_url or raw_url.startswith("data:image"): return
                            
                            full_url = urljoin(scraped_target_url, raw_url)
                            if full_url not in seen_urls:
                                seen_urls.add(full_url)
                                image_data.append({"url": full_url, "type": label})

                        # 1. Look through standard elements & common custom data/lazy-load targets
                        for el in soup.find_all(True):  # Checks every DOM node
                            # Extract common image sources
                            if el.name == 'img':
                                register_url(el.get('src'), "Img Src")
                            
                            # Extract Responsive Srcsets
                            if el.get('srcset'):
                                # Srcset formats can look like: "image-320w.jpg 320w, image-640w.jpg 640w"
                                parts = el.get('srcset').split(',')
                                for part in parts:
                                    chunks = part.strip().split(' ')
                                    if chunks: register_url(chunks[0], "Srcset Asset")
                            
                            # Extract Lazy Load / Authoring Framework Data Attributes
                            for attr, val in list(el.attrs.items()):
                                if attr.startswith('data-src') or attr in ['data-lazy', 'data-original', 'data-fallback']:
                                    if isinstance(val, list): val = " ".join(val)
                                    register_url(val, f"Lazy Load ({attr})")

                            # 2. Extract CSS inline background images
                            style_str = el.get('style')
                            if style_str and 'background' in style_str:
                                match = re.search(r'url\(([^)]+)\)', style_str)
                                if match:
                                    register_url(match.group(1), "CSS Background")
                                    
                        # 3. Handle <source> nodes directly (used within <picture> tags)
                        for source in soup.find_all('source'):
                            register_url(source.get('src'), "Source Attr")

                    else:
                        error_msg = f"Failed to retrieve target workspace page. Status code: {response.status_code}"
                except Exception as e:
                    error_msg = f"Inspection failed: {str(e)}"

        # --- CORE BATCH MIGRATION ACTIONS ---
        elif action_type == 'transform_urls':
            raw_input = request.form.get('url_input', '')
            legacy_input = request.form.get('legacy_input', '')
            env = request.form.get('env', 'qa')
            custom_domain = request.form.get('custom_domain', '')
            editor_action = request.form.get('editor_action', 'force_add')
            use_http = request.form.get('use_http') == 'true'
            find_text = request.form.get('find_text', '').strip()
            migrated_replace = request.form.get('migrated_replace', '').strip()
            
            selected_opts = {
                "env": env, "custom_domain": custom_domain, "editor_action": editor_action,
                "use_http": use_http, "find_text": find_text, "migrated_replace": migrated_replace
            }
            
            orig_lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
            legacy_lines = [line.strip() for line in legacy_input.split('\n') if line.strip()]
            max_length = max(len(orig_lines), len(legacy_lines))
            
            new_items_count = 0
            for i in range(max_length):
                orig_url = orig_lines[i] if i < len(orig_lines) else ""
                raw_legacy = legacy_lines[i] if i < len(legacy_lines) else ""
                
                migrated_url = ""
                if orig_url:
                    migrated_url = transform_migrated_url(
                        orig_url, env, custom_domain, editor_action, use_http, find_text, migrated_replace
                    )
                legacy_url = ""
                if raw_legacy:
                    legacy_url = format_legacy_url(raw_legacy, env, custom_domain, use_http)
                
                if orig_url or legacy_url:
                    new_items_count += 1
                    detailed_groups.append({
                        "original": orig_url, "migrated": migrated_url, "legacy": legacy_url
                    })
            if new_items_count > 0:
                total_processed = update_cached_stats(new_items_count)
                
    total_minutes_saved = int(total_processed * 1.5)
    hours_saved = total_minutes_saved // 60
    mins_saved = total_minutes_saved % 60
            
    return render_template_string(
        HTML_TEMPLATE, 
        detailed_groups=detailed_groups, 
        image_data=image_data,
        scraped_target_url=scraped_target_url,
        error_msg=error_msg,
        selected_opts=selected_opts,
        total_processed=total_processed,
        hours_saved=hours_saved,
        mins_saved=mins_saved
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)