# ui/layout.py
# Shared UI / layout helpers for Hire grounds (modern, clean, mint-teal palette)
import streamlit as st
import os
import base64

# Palette (from provided image)
DARK1 = "#051F20"
DARK2 = "#0B2B26"
DARK3 = "#163832"
DARK4 = "#235347"
MINT1 = "#8EB69B"
MINT2 = "#DAF1DE"
TEXT = "#EAF6F2"

# Path to the local background image (place your image here)
LOCAL_BG_PATH = os.path.join(os.path.dirname(__file__), "assets", "bg.jpg")

def _get_background_data_uri():
    """
    Returns a data:image/*;base64,... string for the local background image
    if it exists; otherwise returns None.
    """
    if not os.path.exists(LOCAL_BG_PATH):
        return None
    try:
        with open(LOCAL_BG_PATH, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        # Try to infer mime type from extension (jpg/jpeg/png)
        ext = os.path.splitext(LOCAL_BG_PATH)[1].lower()
        mime = "image/jpeg"
        if ext == ".png":
            mime = "image/png"
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None

def inject_css(darken_overlay_alpha=0.45):
    """
    Inject CSS for the global layout including a background image with a dark overlay
    to reduce brightness. darken_overlay_alpha is the opacity of the overlay (0.0-1.0).
    Also hides Streamlit's built-in left pages sidebar and the default MainMenu/footer.
    """
    bg_data_uri = _get_background_data_uri()
    # clamp alpha
    try:
        alpha = float(darken_overlay_alpha)
    except Exception:
        alpha = 0.45
    if alpha < 0.0:
        alpha = 0.0
    if alpha > 1.0:
        alpha = 1.0

    # CSS template with placeholders - we avoid f-string braces conflicts by replacing tokens
    css_tpl = """
    <style>
    :root {{
        --dark1: __DARK1__;
        --dark2: __DARK2__;
        --dark3: __DARK3__;
        --dark4: __DARK4__;
        --mint1: __MINT1__;
        --mint2: __MINT2__;
        --text: __TEXT__;
    }}
    html, body {{
        margin: 0;
        padding: 0;
        height: 100%;
        color: var(--text);
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }}
    /* Background: image + dark overlay (reduces brightness) */
    body::before {{
        content: "";
        position: fixed;
        inset: 0;
        z-index: -1;
        background-repeat: no-repeat;
        background-position: center;
        background-size: cover;
        filter: none;
        opacity: 1;
        background-color: var(--dark2);
        __BG_CSS__
    }}
    /* overlay to darken image further for readability */
    body::after {{
        content: "";
        position: fixed;
        inset: 0;
        z-index: 0;
        background: linear-gradient(rgba(0,0,0,__ALPHA__), rgba(0,0,0,__ALPHA__));
        pointer-events: none;
    }}

    /* HIDE Streamlit chrome: left pages sidebar, top menu and footer */
    /* Target common selectors used by Streamlit UI; keep important flag to override Streamlit */
    div[data-testid="stSidebar"], section[data-testid="stSidebar"], aside[aria-label="Sidebar"] {{
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
    }}
    /* hide the hamburger main menu and footer */
    #MainMenu {{ visibility: hidden !important; }}
    footer {{ visibility: hidden !important; height: 0 !important; padding: 0 !important; margin: 0 !important; }}

    /* header (your custom header style) - minimal and clean */
    .hg-header {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:12px;
        padding:14px 18px;
        border-radius:10px;
        background: rgba(255,255,255,0.02);
        margin: 18px;
        border: 1px solid rgba(255,255,255,0.03);
        z-index: 1;
    }}
    .hg-title {{
        font-size:20px;
        font-weight:700;
        color: var(--mint2);
        letter-spacing: 0.6px;
    }}
    .hg-sub {{
        font-size:12px;
        color: rgba(234,246,242,0.7);
    }}
    /* card */
    .hg-card {{
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.03);
        border-radius:12px;
        padding:18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        transition: transform .12s ease, box-shadow .12s ease;
    }}
    .hg-card:hover {{
        transform: translateY(-6px);
        box-shadow:0 18px 48px rgba(0,0,0,0.45);
    }}
    /* CTAs */
    .hg-cta {{
        display:inline-block;
        background: linear-gradient(90deg, var(--mint1), var(--mint2));
        color: #03201F;
        padding:9px 16px;
        border-radius:10px;
        font-weight:600;
        text-decoration:none;
    }}
    .hg-ghost {{
        display:inline-block;
        color: rgba(234,246,242,0.9);
        padding:8px 14px;
        border-radius:8px;
        border: 1px solid rgba(255,255,255,0.04);
        background: transparent;
        text-decoration:none;
    }}
    .muted-small {{
        color: rgba(234,246,242,0.66);
        font-size:0.9rem;
    }}
    .hg-stats {{
        display:flex;
        gap:12px;
        flex-wrap:wrap;
    }}
    .hg-stat {{
        background: rgba(255,255,255,0.02);
        padding:12px 14px;
        border-radius:10px;
        min-width:120px;
        text-align:center;
        border:1px solid rgba(255,255,255,0.03);
    }}
    .password-strength {{
        height:8px;
        border-radius:6px;
        background: linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));
        margin-top:6px;
    }}
    /* responsive */
    @media (max-width: 760px) {{
        .hg-header {{ padding:10px; margin:10px; }}
        .hg-title {{ font-size:18px; }}
    }}
    </style>
    """

    # If we have a background image data URI embed it, otherwise leave blank and rely on dark gradient color
    if bg_data_uri:
        bg_css = f'background-image: url("{bg_data_uri}");'
    else:
        bg_css = ""  # fallback uses background-color defined earlier

    css = (css_tpl.replace("__DARK1__", DARK1)
                 .replace("__DARK2__", DARK2)
                 .replace("__DARK3__", DARK3)
                 .replace("__DARK4__", DARK4)
                 .replace("__MINT1__", MINT1)
                 .replace("__MINT2__", MINT2)
                 .replace("__TEXT__", TEXT)
                 .replace("__BG_CSS__", bg_css)
                 .replace("__ALPHA__", str(alpha)))
    st.markdown(css, unsafe_allow_html=True)

def header(app_name="Hire grounds"):
    inject_css()
    # Clean header: centered title on left, simple nav on right (no profile)
    cols = st.columns([3,1])
    with cols[0]:
        st.markdown(f"""
            <div class="hg-header" role="banner">
                <div>
                    <div class="hg-title">{app_name}</div>
                    <div class="hg-sub">AI-assisted hiring · fair · fast</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        # Right-aligned nav buttons using unique keys to avoid duplicate widget IDs
        if st.button("Register", key="hdr_register"):
            st.switch_page("pages/1_Register.py")
        if st.button("Login", key="hdr_login"):
            st.switch_page("pages/2_Login.py")

def footer():
    # Minimal clean divider only (no extra text)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.04);'/>", unsafe_allow_html=True)