def status_page(*, title: str, message: str, ok: bool = True) -> str:
    accent = "#22d3ee" if ok else "#fb7185"
    accent_bg = "rgba(34,211,238,0.1)" if ok else "rgba(251,113,133,0.1)"
    accent_border = "rgba(34,211,238,0.35)" if ok else "rgba(251,113,133,0.35)"
    icon = "✓" if ok else "✕"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} — DisasterShield AI</title>
<style>
  body {{
    margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: #05070b; color: #cbd5e1;
    font-family: 'JetBrains Mono', ui-monospace, 'Courier New', monospace;
    padding: 24px; box-sizing: border-box;
  }}
  .card {{
    max-width: 420px; width: 100%; background: #0a0f16;
    border: 1px solid {accent_border}; border-radius: 8px; padding: 32px 28px; text-align: center;
  }}
  .icon {{
    width: 48px; height: 48px; border-radius: 999px; background: {accent_bg};
    border: 1px solid {accent_border}; color: {accent};
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 20px; font-size: 22px;
  }}
  .brand {{
    font-size: 10px; letter-spacing: 0.15em; text-transform: uppercase; color: #64748b; margin-bottom: 4px;
  }}
  h1 {{ font-size: 16px; color: #f1f5f9; margin: 0 0 10px; letter-spacing: 0.02em; }}
  p {{ font-size: 13px; line-height: 1.6; color: #94a3b8; margin: 0; }}
</style>
</head>
<body>
  <div class="card">
    <div class="icon">{icon}</div>
    <div class="brand">DisasterShield AI // Tactical Decision Node</div>
    <h1>{title}</h1>
    <p>{message}</p>
  </div>
</body>
</html>"""