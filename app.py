from flask import Flask, request, render_template_string, jsonify
from urllib.parse import urlparse, urlunparse

app = Flask(__name__)

# Predefined environments mapping
DOMAINS = {
    "qa": "qa-author.honeywellaerospace.com",
    "stage": "stage-author.honeywellaerospace.com",
    "prod": "author.honeywellaerospace.com",
    "local": "localhost:4502",
    "custom": ""  # Handled dynamically via text input
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Advanced AEM URL Transformer</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; max-width: 800px; color: #333; background-color: #fcfcfc; }
        h2 { color: #222; border-bottom: 2px solid #007bff; padding-bottom: 8px; }
        textarea { width: 100%; height: 140px; margin-bottom: 15px; font-family: monospace; padding: 12px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; resize: vertical; }
        .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; background: #f1f3f5; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef; }
        .option-group { display: flex; flex-direction: column; }
        .option-group label { font-weight: bold; margin-bottom: 6px; font-size: 14px; }
        select { padding: 8px; border: 1px solid #ccc; border-radius: 4px; background-color: white; font-size: 14px; }
        .custom-domain-container { margin-top: 10px; }
        .custom-domain-container input { padding: 8px; width: 100%; font-family: monospace; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .checkbox-group { display: flex; align-items: center; gap: 10px; margin-top: 15px; font-size: 14px; }
        .checkbox-group input { width: 16px; height: 16px; cursor: pointer; }
        
        /* Buttons styling */
        .btn-primary { padding: 12px 28px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: 600; transition: background 0.2s; }
        .btn-primary:hover { background-color: #0056b3; }
        .btn-secondary { padding: 6px 12px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; margin-left: 10px; min-width: 65px; transition: background 0.2s; }
        .btn-secondary:hover { background-color: #5a6268; }
        .btn-copy-all { padding: 6px 14px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 600; transition: background 0.2s; }
        .btn-copy-all:hover { background-color: #218838; }
        
        /* Results Layout */
        .results-box { margin-top: 35px; border-top: 1px solid #dee2e6; padding-top: 20px; }
        .results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .results-header h3 { margin: 0; color: #333; }
        .result-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 12px; background-color: #f8f9fa; border-left: 5px solid #007bff; border-top: 1px solid #e9ecef; border-right: 1px solid #e9ecef; border-bottom: 1px solid #e9ecef; border-radius: 0 4px 4px 0; font-family: monospace; font-size: 14px; }
        .result-url { word-break: break-all; flex-grow: 1; }
        .result-url a { color: #0056b3; text-decoration: none; }
        .result-url a:hover { text-decoration: underline; }
    </style>
    <script>
        function toggleCustomInput() {
            var envSelect = document.getElementById("env");
            var customContainer = document.getElementById("custom_domain_container");
            if (envSelect.value === "custom") {
                customContainer.style.display = "block";
                document.getElementById("custom_domain").required = true;
            } else {
                customContainer.style.display = "none";
                document.getElementById("custom_domain").required = false;
            }
        }

        function copyToClipboard(text, button) {
            navigator.clipboard.writeText(text).then(function() {
                var originalText = button.innerText;
                button.innerText = "Copied!";
                button.style.backgroundColor = "#28a745";
                setTimeout(function() {
                    button.innerText = originalText;
                    button.style.backgroundColor = "";
                }, 1500);
            }, function(err) {
                console.error('Could not copy text: ', err);
            });
        }

        function copyAllUrls() {
            var links = document.querySelectorAll('.result-url-link');
            var urls = [];
            links.forEach(function(link) {
                urls.push(link.href);
            });
            
            var joinString = urls.join('\\n');
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
    <h2>Advanced AEM URL Transformer</h2>
    <form method="POST" action="/">
        <label for="url_input"><strong>Paste paths or URLs (one per line):</strong></label>
        <textarea name="url_input" id="url_input" placeholder="/content/aerobt/...\nhttp://10.24.122.43:4502/editor.html/..."></textarea>
        
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
                    <input type="text" id="custom_domain" name="custom_domain" placeholder="e.g., dev-author.company.com or 12.34.56.78:4502" value="{{ selected_opts.custom_domain }}">
                </div>
            </div>
            
            <div class="option-group">
                <label for="editor_action">Editor Path (/editor.html):</label>
                <select name="editor_action" id="editor_action">
                    <option value="keep" {% if selected_opts.editor_action == 'keep' %}selected{% endif %}>Preserve original behavior</option>
                    <option value="force_add" {% if selected_opts.editor_action == 'force_add' %}selected{% endif %}>Force add /editor.html</option>
                    <option value="force_remove" {% if selected_opts.editor_action == 'force_remove' %}selected{% endif %}>Force remove /editor.html</option>
                </select>
            </div>
        </div>

        <div class="checkbox-group">
            <input type="checkbox" id="use_http" name="use_http" value="true" {% if selected_opts.use_http %}checked{% endif %}>
            <label for="use_http">Use HTTP protocol instead of HTTPS</label>
        </div>
        <br>
        <input type="submit" class="btn-primary" value="Transform URLs">
    </form>
    
    {% if results %}
    <div class="results-box">
        <div class="results-header">
            <h3>Transformed Results:</h3>
            {% if results|length > 1 %}
                <button id="copy_all_btn" class="btn-copy-all" onclick="copyAllUrls()">Copy All Links</button>
            {% endif %}
        </div>
        
        {% for item in results %}
            <div class="result-item">
                <div class="result-url">
                    <a href="{{ item }}" target="_blank" class="result-url-link">{{ item }}</a>
                </div>
                <button class="btn-secondary" onclick="copyToClipboard('{{ item }}', this)">Copy</button>
            </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
"""

def transform_single_url(input_str, env, custom_domain, editor_action, use_http):
    if not input_str:
        return ""
    
    input_str = input_str.strip()
    
    # Process target domain choice
    if env == "custom" and custom_domain:
        # Sanitize common input errors like pasting full protocols into the field
        target_domain = custom_domain.replace("http://", "").replace("https://", "").strip("/")
    else:
        target_domain = DOMAINS.get(env, DOMAINS["qa"])
        
    # Determine fallback protocol scheme
    scheme = "http" if use_http or env == "local" else "https"
    
    # Isolate root path string
    if input_str.startswith("http://") or input_str.startswith("https://"):
        parsed = urlparse(input_str)
        path = parsed.path
    else:
        path = input_str if input_str.startswith("/") else f"/{input_str}"

    # Handle /editor.html structural state
    is_editor = path.startswith("/editor.html")
    if is_editor:
        clean_path = path.replace("/editor.html", "", 1)
    else:
        clean_path = path

    if editor_action == "force_add":
        path = f"/editor.html{clean_path}"
    elif editor_action == "force_remove":
        path = clean_path
    else:
        path = f"/editor.html{clean_path}" if is_editor else clean_path

    # Standardize content extension layout
    if not path.endswith(".html"):
        path = f"{path}.html"
        
    return urlunparse((scheme, target_domain, path, '', '', ''))

@app.route('/', methods=['GET', 'POST'])
def home():
    results = []
    selected_opts = {"env": "qa", "custom_domain": "", "editor_action": "keep", "use_http": False}
    
    if request.method == 'POST':
        raw_input = request.form.get('url_input', '')
        env = request.form.get('env', 'qa')
        custom_domain = request.form.get('custom_domain', '')
        editor_action = request.form.get('editor_action', 'keep')
        use_http = request.form.get('use_http') == 'true'
        
        selected_opts = {
            "env": env, 
            "custom_domain": custom_domain, 
            "editor_action": editor_action, 
            "use_http": use_http
        }
        
        # Batch separation via newline layout
        lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
        for line in lines:
            transformed = transform_single_url(line, env, custom_domain, editor_action, use_http)
            results.append(transformed)
            
    return render_template_string(HTML_TEMPLATE, results=results, selected_opts=selected_opts)

if __name__ == '__main__':
    app.run(debug=True, port=5000)