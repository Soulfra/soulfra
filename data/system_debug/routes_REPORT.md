# System Debug Report: routes

**Generated:** 2026-01-11 17:11:22

## Overview

- **Total Nodes:** 1556
- **Total Edges:** 2615
- **Isolated Nodes:** 1139 (potential dead code)

## Node Types

| Type | Count |
|------|-------|
| import | 735 |
| function | 420 |
| route | 401 |


## Edge Types

| Type | Count |
|------|-------|
| calls | 2615 |


## Hub Nodes (Most Connected)

These are the most critical parts of your system:

| Node | Connections |
|------|-------------|
| function_jsonify | 457 |
| function_flash | 253 |
| function_redirect | 220 |
| function_url_for | 209 |
| function_get_db | 187 |
| function_render_template | 165 |
| function_str | 150 |
| function_len | 134 |
| function_dict | 95 |
| function_print | 73 |


## ⚠️ Isolated Nodes (Potential Dead Code)

These nodes have no connections. Consider removing:

- **flask.Flask** (import)
- **flask.render_template** (import)
- **flask.render_template_string** (import)
- **flask.request** (import)
- **flask.redirect** (import)
- **flask.url_for** (import)
- **flask.flash** (import)
- **flask.session** (import)
- **flask.Response** (import)
- **flask.jsonify** (import)
- **flask.g** (import)
- **flask.send_file** (import)
- **flask.send_from_directory** (import)
- **flask.abort** (import)
- **flask_cors.CORS** (import)
- **datetime.datetime** (import)
- **os** (import)
- **sys** (import)
- **json** (import)
- **sqlite3** (import)

... and 1119 more


## Next Steps

1. **Review hub nodes** - These are critical, test thoroughly
2. **Investigate isolated nodes** - Dead code or missing connections?
3. **Look for unexpected edges** - Coupling you didn't know about
4. **Compare domain graphs** - Are your brands too similar?

