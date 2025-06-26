import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import re
import math
import json

GROWTH_DAYS = 7
st.set_page_config("VVC Social Dashboard", layout="wide", initial_sidebar_state="expanded")

def parse_number(val):
    if pd.isna(val) or str(val).strip().lower() in ["", "none", "n/a"]:
        return 0.0
    val = str(val).replace(",", "").strip().upper()
    try:
        if val.endswith("K"):
            return float(val[:-1]) * 1000
        elif val.endswith("M"):
            return float(val[:-1]) * 1000000
        else:
            return float(val)
    except:
        return 0.0

def student_initials(name):
    if not name: return "👤"
    return "".join([n[0] for n in name.split() if n])[:2].upper()

def format_post_date(d):
    if not d or d in ['-', 'N/A', '']: return ""
    try:
        if "T" in d:
            dt = datetime.fromisoformat(d.replace("Z",""))
            return dt.strftime("%d %b %Y")
        elif len(d) >= 10: return d[:10]
        else: return d
    except: return d

def safe(val):
    if pd.isna(val) or str(val).strip().lower() in ["", "none", "n/a"]:
        return ""
    return str(val).strip()

def safe_int(val):
    try:
        if pd.isna(val) or str(val).strip().lower() in ["", "none", "n/a", ""]:
            return ""
        return int(float(val))
    except:
        return ""

def sanitize_html(text):
    s = str(text or "")
    s = re.sub(r"</?div[^>]*>", "", s)
    s = re.sub(r"```+", "", s)
    s = s.replace("\n", " ").replace("\r", " ")
    return s.strip()

def safe_int_from_row(row, key):
    val = row.get(key, 0)
    try:
        fval = float(val)
        if math.isnan(fval):
            return 0
        return int(fval)
    except Exception:
        return 0
    
def render_leaderboard_card(name, initials, metric_str, color, highlight, medal):
    st.markdown(
f"""
<div style="display:flex;align-items:center;gap:13px;padding:7px 9px 7px 0;margin-bottom:5px;{highlight}">
    {medal}
    <div style='width:34px;height:34px;border-radius:50%;background:linear-gradient(120deg,#fcb69f 70%,#90a7d0 100%);color:#fff;
    font-family:Pacifico,cursive;font-size:1.06em;font-weight:700;display:flex;align-items:center;justify-content:center;'>{initials}</div>
    <span style="font-weight:700;flex:1">{name}</span>
    <span style='font-weight:900;color:{color};font-size:1.1em;'>{metric_str}</span>
</div>
""",
        unsafe_allow_html=True
    )

# ---- Banner ----
st.markdown("""
<div style='
    width:100%;
    padding: 1.1em 2em 1.1em 1em;
    border-radius: 18px;
    margin-bottom: 1.3em;
    font-size: 2.8em;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(90deg,#fcb69f 10%,#a1c4fd 90%);
    color: #fff;
    text-shadow:0 2px 16px #e1306c33;
    box-shadow: 0 2px 12px #8881;
    display: flex;
    align-items: center;
    gap: 1.3em;
'>
     Viral Video Club - Bootcamp Social Media Dashboard
</div>
""", unsafe_allow_html=True)

# ---- Google Sheets ----
SHEET_ID = '1MvGIdmM9eW89vSIoMzlg6k8x6oXBr1XKfrCoLIBkzq0'
SHEET_NAME = 'History'
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)


client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# ---- Engagement Weekly Worksheet ----
try:
    sheet_weekly = client.open_by_key(SHEET_ID).worksheet("Engagement_Weekly")
    df_weekly = pd.DataFrame(sheet_weekly.get_all_records())
    df_weekly['Week'] = pd.to_datetime(df_weekly['Week'], errors='coerce')
except Exception as e:
    df_weekly = pd.DataFrame()
    st.warning("Couldn't load Engagement_Weekly worksheet. Make sure it exists in your Google Sheet.")
    # Immediately after you load df_weekly:
for col in ["Videos_Posted", "Zoom_Calls_Attended", "Discord_Feedback_Requested", "Course_Completed_Percent"]:
    if col in df_weekly.columns:
        df_weekly[col] = pd.to_numeric(df_weekly[col], errors="coerce")

@st.cache_data(ttl=300)
def load_data():
    return pd.DataFrame(sheet.get_all_records())
df = load_data()

# --- CLEAN ALL NUMERIC COLUMNS ---
numeric_cols = [col for col in df.columns if any(x in col.lower() for x in ["followers", "likes", "comments"])]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col].replace(["", " ", None, "none", "n/a", "N/A"], np.nan), errors="coerce")

df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.sort_values("Date").drop_duplicates(subset=["StudentID", "Date"], keep="last")

PLATFORMS = [
    {"label": "Instagram", "user": "IG_Username", "foll": "IG_Followers", "foll_last": "IG_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/instagram.svg", "brand": "linear-gradient(90deg,#fcb69f 10%,#a1c4fd 90%)", "prefix": "IG"},
    {"label": "TikTok", "user": "TT_Username", "foll": "TT_Followers", "foll_last": "TT_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/tiktok.svg", "brand": "#beaaaa", "display": "#232323", "prefix": "TT"},
    {"label": "YouTube", "user": "YT_Username", "foll": "YT_Followers", "foll_last": "YT_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/youtube.svg", "brand": "#f70000", "prefix": "YT"},
    {"label": "Threads", "user": "TH_Username", "foll": "TH_Followers", "foll_last": "TH_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/threads.svg", "brand": "#a59f9f", "prefix": "TH"},
    {"label": "LinkedIn", "user": "LI_Username", "foll": "LI_Followers", "foll_last": "LI_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linkedin.svg", "brand": "#1378b4", "display": "#126BC4", "prefix": "LI"},
]

menu_tabs = st.tabs(["Dashboard", "Analytics"])

# ---- QUICK STATS BANNER ----
if not df_weekly.empty:
    this_week = df_weekly[df_weekly['Week'] == df_weekly['Week'].max()]
    course_col = None
for possible in [
    "Course_Completed_Percent",
    "%_Course_Completed",
    "Course Completed Percent",
    "Course Completed",
    "Course Completed (%)"
]:
    if possible in df_weekly.columns:
        course_col = possible
        break

if not df_weekly.empty:
    this_week = df_weekly[df_weekly['Week'] == df_weekly['Week'].max()]
    videos = int(pd.to_numeric(this_week['Videos_Posted'], errors="coerce").sum()) if 'Videos_Posted' in this_week else 0
    feedback = int(pd.to_numeric(this_week['Discord_Feedback_Requested'], errors="coerce").sum()) if 'Discord_Feedback_Requested' in this_week else 0
    zooms = int(pd.to_numeric(this_week['Zoom_Calls_Attended'], errors="coerce").sum()) if 'Zoom_Calls_Attended' in this_week else 0
    if course_col and not this_week.empty:
        avg_course = pd.to_numeric(this_week[course_col], errors="coerce").mean()
    else:
        avg_course = 0


with menu_tabs[0]:
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        latest_date = df['Date'].max()
        curr_df = df[df['Date'] == latest_date].copy()
    else:
        curr_df = df.copy()

    lcol, ccol, rcol = st.columns([1.2, 2.2, 1.2], gap="large")

def get_primary_platform_emoji(name, curr_df, PLATFORMS):
    # Returns the emoji/icon for the platform where the student has the most followers
    if name not in curr_df['Name'].values:
        return ""
    row = curr_df[curr_df['Name'] == name]
    max_count = -1
    icon = ""
    for p in PLATFORMS:
        try:
            if p['foll'] in row:
                val = parse_number(row.iloc[0][p['foll']])
                if val > max_count:
                    max_count = val
                    icon = p['emoji']
        except Exception:
            continue
    return icon

with lcol:
    st.markdown("#### Creators")
    search = st.text_input("Type to search…", key="sidebar_search")
    fdf = curr_df[curr_df['Name'].str.contains(search, case=False, na=False)] if search else curr_df
    student_names = [n for n in fdf['Name'].tolist() if str(n).strip()]
    master_student_names = [n for n in curr_df['Name'].tolist() if str(n).strip()]
    if not student_names:
        student_names = master_student_names[:1] if master_student_names else ["No students"]
        st.info("No students found.")

    if ('selected_student' not in st.session_state or
        st.session_state.selected_student not in student_names):
        st.session_state.selected_student = student_names[0]

    st.markdown("""
    <style>
    .student-scroll-list { max-height: 460px; overflow-y: auto; padding-right: 8px;}
    .student-scroll-list::-webkit-scrollbar {width:7px;background:#fff;}
    .student-scroll-list::-webkit-scrollbar-thumb {background:#fcb69f99;border-radius:8px;}
    .student-card2 {
        display: flex; align-items: center; gap: 12px;
        padding: 9px 12px; border-radius: 14px; margin-bottom: 5px;
        background: #f6f8fb; cursor: pointer; border: 1.5px solid transparent; transition: background .13s, border .13s;
        box-shadow: 0 1px 8px #a1c4fd0d;
    }
    .student-card2.selected { background: linear-gradient(90deg,#fcb69f33 60%,#a1c4fd13 100%); border-color: #fa7a3a60;}
    .student-card2:hover {
        background: #fae0d033;
        border-color: #fa7a3acc;
    }
    .student-initials2 {
        width: 43px; height: 43px; border-radius: 50%;
        background: linear-gradient(120deg,#fcb69f 65%,#90a7d0 100%);
        color: #fff; font-family: Pacifico, cursive; font-size: 1.21em; font-weight: bold;
        display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 7px #a1c4fd22;
        letter-spacing: 0.5px;
    }
    .student-meta {
        display: flex; flex-direction: column; flex:1; min-width:0;
    }
    .student-name2 {
        font-weight:700; color:#232323; font-size:1.13em; overflow:visible; text-overflow:ellipsis; white-space:nowrap; max-width:115px;
        letter-spacing: -0.5px;
    }
    .student-badges {
        margin-top: 1.5px;
        font-size:1.24em;
        display: flex; align-items: center; gap: 6px;
    }
    </style>
    <div class="student-scroll-list">
    """, unsafe_allow_html=True)

    student_html = ""
    for i, n in enumerate(student_names):
        initials = student_initials(n)
        selected = (n == st.session_state.selected_student)
        card_class = "student-card2 selected" if selected else "student-card2"
        # Platform icon for their main platform (emoji, no badge)
        icon_url = get_primary_platform_emoji(n, curr_df, PLATFORMS)
        primary_platform = f"<img src='{icon_url}' width='26' height='26' style='vertical-align:middle;margin-left:3px;border-radius:7px;'/>" if icon_url else ""

        student_html += f"""
        <form action="#student_{i}" method="get" class="student-btn-form">
            <button name="student" value="{n}" type="submit" style="all:unset;width:100%;">
                <div class="{card_class}" id="student_{i}">
                    <div class="student-initials2">{initials}</div>
                    <div class="student-meta">
                        <span class="student-name2">{n}</span>
                        <span class="student-badges">{primary_platform}</span>
                    </div>
                </div>
            </button>
        </form>
        """

    st.markdown(student_html + "</div>", unsafe_allow_html=True)
    query_params = st.query_params
    if "student" in query_params:
        clicked_name = urllib.parse.unquote(query_params["student"])
        if clicked_name in student_names:
            st.session_state.selected_student = clicked_name
        st.query_params.clear()


    # ---- CENTRE: Student Feed ----
    NO_PREVIEW_IMAGE = "https://i.imgur.com/sUFH1Aq.png"  # Your own placeholder image here

with ccol:
    st.markdown("#### Student Feed")
    selected_student = st.session_state.selected_student
    show_df = curr_df[curr_df['Name'] == selected_student] if selected_student in curr_df['Name'].values else curr_df.head(1)
    for _, row in show_df.iterrows():
        st.markdown(f"### {row['Name']}")

        # MINI STATS BAR (as before)
        student_stats = (0, 0, 0, 0)
        if not df_weekly.empty:
            latest_week = df_weekly['Week'].max()
            week_data = df_weekly[(df_weekly['Week'] == latest_week) & (df_weekly['Name'] == row['Name'])]
            if not week_data.empty:
                stats_row = week_data.iloc[0]
                videos = safe_int_from_row(stats_row, "Videos_Posted")
                feedback = safe_int_from_row(stats_row, "Discord_Feedback_Requested")
                zooms = safe_int_from_row(stats_row, "Zoom_Calls_Attended")
                course_val = stats_row.get("%_Course_Completed", 0)
                try:
                    course = float(course_val) if not pd.isna(course_val) else 0
                except Exception:
                    course = 0
                student_stats = (videos, feedback, zooms, course)
        st.markdown(f"""
        <div style='background:linear-gradient(90deg,#f6f8fb,#fff);border-radius:14px;padding:7px 22px 7px 18px;margin:3px 0 17px 0;display:flex;gap:2em;font-weight:600;font-size:1.06em;box-shadow:0 1px 6px #a1c4fd10;align-items:center;'>
            <span>📹 {videos}</span>
            <span>💬 {feedback}</span>
            <span>🧑‍💻 {zooms}</span>
            <span>🎓 {course:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
        main_platform = max(PLATFORMS, key=lambda p: parse_number(row.get(p['foll'], 0)))

        for plat in PLATFORMS:
            user_val = safe(row.get(plat["user"], ""))
            if not user_val:
                continue

            foll_val = parse_number(row.get(plat["foll"], 0))
            prefix = plat["prefix"]
            student_rows = df[(df['Name'] == row['Name']) & (~df[f"{prefix}_Followers"].isna())].copy()
            student_rows = student_rows.sort_values("Date")
            latest_foll = follower_growth = engagement = likes_val = comm_val = 0
            date_val = cap_val = url_val = ""
            if len(student_rows) > 0:
                latest_row = student_rows.iloc[-1]
                latest_foll = parse_number(latest_row.get(f"{prefix}_Followers", 0))
                prev_rows = student_rows[student_rows["Date"] <= latest_row["Date"] - pd.Timedelta(days=GROWTH_DAYS)]
                if len(prev_rows) > 0:
                    prev_foll = parse_number(prev_rows.iloc[-1].get(f"{prefix}_Followers", 0))
                else:
                    prev_foll = parse_number(student_rows.iloc[0].get(f"{prefix}_Followers", 0))
                follower_growth = latest_foll - prev_foll

                likes_val = parse_number(latest_row.get(f"{prefix}_LaPostLikes", 0))
                engagement = (likes_val / latest_foll * 100) if latest_foll else 0

                date_val = safe(format_post_date(latest_row.get(f"{prefix}_LaPostDate", "")))
                cap_val = safe(latest_row.get(f"{prefix}_LaPostCaption", ""))
                url_val = safe(latest_row.get(f"{prefix}_LaPostURL", ""))
                comm_val = parse_number(latest_row.get(f"{prefix}_LaPostComments", 0))
                preview_url = safe(latest_row.get(f"{prefix}_LaPostPreview", "")) if f"{prefix}_LaPostPreview" in latest_row else ""
            else:
                preview_url = ""

            cap_trunc = (cap_val[:110] + "…") if cap_val and len(cap_val) > 110 else cap_val
            cap_trunc = sanitize_html(cap_trunc)
            cap_val = sanitize_html(cap_val)
            date_display = sanitize_html(date_val)
            url_val = sanitize_html(url_val)
            preview_url = sanitize_html(preview_url)

            likes_display = f"{int(round(likes_val)):,}" if likes_val else ""
            comm_display = f"{int(round(comm_val)):,}" if comm_val else ""
            foll_display = f"{int(round(foll_val)):,}" if foll_val else ""
            growth_display = (
                f"<span style='background:#ebfdc1;border-radius:8px;padding:.20em .7em;margin-left:.4em;font-weight:700;color:#2b8328;'>+{int(follower_growth):,}</span>" if follower_growth > 0 else
                f"<span style='background:#fde1e1;border-radius:8px;padding:.20em .7em;margin-left:.4em;font-weight:700;color:#c81c1c;'>{int(follower_growth):,}</span>" if follower_growth < 0 else
                ""
            )
            engagement_display = (
                f"<span style='background:#ebfdc1;border-radius:8px;padding:.19em .6em;margin-left:.4em;font-weight:700;color:#7fa569;'>{engagement:.1f}%</span>" if engagement else ""
            )

            # Card highlight logic unchanged
            is_new = False
            is_trending = False
            try:
                post_date = pd.to_datetime(date_val)
                is_new = post_date > (pd.Timestamp.now() - pd.Timedelta(days=7))
            except Exception:
                is_new = False
            is_trending = (follower_growth and follower_growth > 30) or (engagement and engagement > 10)
            badge_html = ""
            if is_new:
                badge_html += " <span style='font-size:1.3em;' title='New this week'>🆕</span>"
            if is_trending:
                badge_html += " <span style='font-size:1.3em;' title='Trending!'>🔥</span>"
            if engagement > 20:
                badge_html += " <span style='font-size:1.2em;'>💯</span>"
            if follower_growth > 50:
                badge_html += " <span style='font-size:1.2em;'>🚀</span>"

            highlight = (
                "box-shadow:0 8px 32px #e1306c15;"
                if plat['label'] == main_platform['label'] and foll_val > 0 else ""
            )
            if engagement and engagement > 10:
                highlight += "box-shadow:0 0 12px #fa7a3a44;"

            card_has_content = (
                (cap_trunc and cap_trunc.strip() != "") or
                url_val or likes_display or comm_display or date_display
            )
            if not card_has_content:
                continue

            lines = []

            # --- Robust image preview logic ---
            display_url = preview_url if (preview_url and preview_url.startswith("http")) else NO_PREVIEW_IMAGE

            if display_url and display_url != NO_PREVIEW_IMAGE:
                if url_val:
                    lines.append(
                        f"<a href='{url_val}' target='_blank'>"
                        f"<img src='{display_url}' width='120' style='border-radius:12px;box-shadow:0 1px 8px #0002;margin:2px 0 10px 0;max-width:170px;object-fit:cover;display:block;' alt='Post preview'/>"
                        f"</a>"
                    )
                else:
                    lines.append(
                        f"<img src='{display_url}' width='120' style='border-radius:12px;box-shadow:0 1px 8px #0002;margin:2px 0 10px 0;max-width:170px;object-fit:cover;display:block;' alt='Post preview'/>"
                    )
            else:
                lines.append(
                    f"<img src='{NO_PREVIEW_IMAGE}' width='120' style='border-radius:12px;box-shadow:0 1px 8px #0002;margin:2px 0 10px 0;max-width:170px;object-fit:cover;display:block;opacity:0.45;' alt='No preview available'/>"
                )
                if url_val:
                    lines.append(
                        f"<div style='font-size:1.08em;margin-bottom:3px;'>"
                        f"<a href='{url_val}' target='_blank' style='color:{plat['brand']};font-weight:600;text-decoration:underline;'>View Post</a>"
                        f"</div>"
                    )

            # --- LinkedIn SPECIAL: add username, followers, connections ---
            if plat["label"] == "LinkedIn":
                li_username = safe(latest_row.get("LI_Username", ""))
                li_followers = safe(latest_row.get("LI_Followers", ""))
                li_connections = safe(latest_row.get("LI_Connections", ""))
                lines.append(
                    f"<div style='margin-bottom:2px;font-size:1.05em;'><b>Username:</b> {li_username} &nbsp; | &nbsp; <b>Followers:</b> {li_followers} &nbsp; | &nbsp; <b>Connections:</b> {li_connections}</div>"
                )
            # --- YouTube SPECIAL: add username, followers, channel title, channel views ---
            if plat["label"] == "YouTube":
                yt_username = safe(latest_row.get("YT_Username", ""))
                yt_followers = safe(latest_row.get("YT_Followers", ""))
                yt_channel_title = safe(latest_row.get("YT_ChannelTitle", ""))
                yt_channel_views = safe(latest_row.get("YT_ChannelViews", ""))
                lines.append(
                    f"<div style='margin-bottom:2px;font-size:1.05em;'><b>Username:</b> {yt_username} &nbsp; | &nbsp; <b>Followers:</b> {yt_followers} &nbsp; | &nbsp; <b>Channel:</b> {yt_channel_title} &nbsp; | &nbsp; <b>Views:</b> {yt_channel_views}</div>"
                )

            # --- Caption as clickable or colored ---
            if cap_trunc:
                if url_val:
                    lines.append(
                        f"<div style='font-size:1.09em;'>"
                        f"<a href='{url_val}' target='_blank' style='color:{plat['brand']};font-weight:700;text-decoration:underline;'>{cap_trunc}</a>"
                        f"</div>"
                    )
                else:
                    lines.append(
                        f"<div style='font-size:1.09em;color:{plat['brand']};font-weight:700;text-decoration:underline;'>{cap_trunc}</div>"
                    )

            # --- Date, likes, comments (single line) ---
            stat_line = []
            if date_display:
                stat_line.append(f"<span style='color:#aaa;'>{date_display}</span>")
            if likes_display:
                stat_line.append(f"👍 <b>{likes_display}</b>")
            if comm_display:
                stat_line.append(f"💬 <b>{comm_display}</b>")
            if stat_line:
                lines.append(
                    f"<div style='color:#232323;font-size:1.06em;margin-top:2px;'>{' &nbsp; '.join(stat_line)}</div>"
                )

            info_lines = "\n".join(lines)

            st.markdown(
f"""
<div style="background:#fff;border-radius:22px;box-shadow:0 4px 16px #0001;{highlight}
    border-top:8px solid {plat['brand']};margin-bottom:1.5em;padding:2em 2em 1.2em 2em;">
    <div style='display:flex;align-items:center;gap:18px;margin-bottom:.6em;'>
        <img src='{plat["emoji"]}' width=52 height=52 style='border-radius:17px;background:{plat["brand"]};padding:6px;box-shadow:0 2px 14px {plat["brand"]}22;'>
        <span style="font-size:1.22em;font-weight:700;color:{plat['brand']};margin-bottom:.15em;">{plat['label']}{badge_html}</span>
    </div>
    <div style="color:#90a7d0;">
        @{user_val}{f" &nbsp; • &nbsp; <b>{foll_display}</b> Followers" if foll_display else ""}
        {growth_display}{engagement_display}
    </div>
    {info_lines}
</div>
""",
                unsafe_allow_html=True
            )


    # ---- RIGHT: Leaderboard ----
    with rcol:
        st.markdown("#### Leaderboard")
        plat_options = [p['label'] for p in PLATFORMS]
        metric_options = ['Followers', 'Engagement', 'Follower Growth']
        lb_plat = st.selectbox("Platform", plat_options, index=0, key="lbplat_selectbox_leaderboard")
        lb_metric = st.selectbox("Metric", metric_options, index=0, key="lbmet_selectbox_leaderboard")
        prefix = [p['prefix'] for p in PLATFORMS if p['label'] == lb_plat][0]
        plat = next(p for p in PLATFORMS if p['label'] == lb_plat)
        color = plat['brand']
        foll_col = f"{prefix}_Followers"

        if 'Date' in df.columns and not df.empty:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            date_vals = df['Date'].dropna()
            if not date_vals.empty:
                min_date = date_vals.min()
                max_date = date_vals.max()
                lb_date_range = st.date_input(
                    "Leaderboard date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="lb_date_range"
                )
                if isinstance(lb_date_range, tuple):
                    lb_start_date, lb_end_date = lb_date_range
                else:
                    lb_start_date = lb_end_date = lb_date_range
                lb_mask = (df['Date'] >= pd.to_datetime(lb_start_date)) & (df['Date'] <= pd.to_datetime(lb_end_date))
                plot_df_lb = df[lb_mask].copy()
            else:
                st.warning("No available dates in the data for leaderboard.")
                plot_df_lb = df.copy()
        else:
            plot_df_lb = df.copy()

        if lb_metric == "Followers":
            latest = plot_df_lb.sort_values("Date").groupby("StudentID").last().reset_index()
            latest[foll_col] = latest[foll_col].apply(parse_number)
            y_col = foll_col
            display_df = latest.sort_values(y_col, ascending=False).head(10)
            values = display_df[y_col]
        elif lb_metric == "Follower Growth":
            grp = plot_df_lb.sort_values("Date").groupby("StudentID")
            first = grp.first().reset_index()
            last = grp.last().reset_index()
            growth_df = last[["StudentID", "Name", foll_col]].copy()
            growth_df = growth_df.rename(columns={foll_col: "Followers_End"})
            growth_df["Followers_Start"] = first.set_index("StudentID")[foll_col].values
            growth_df["Followers_End"] = growth_df["Followers_End"].apply(parse_number)
            growth_df["Followers_Start"] = growth_df["Followers_Start"].apply(parse_number)
            growth_df["Growth"] = growth_df["Followers_End"] - growth_df["Followers_Start"]
            display_df = growth_df.sort_values("Growth", ascending=False).head(10)
            values = display_df["Growth"]
        else:  # Engagement
            likes_col = f"{prefix}_LaPostLikes"
            latest = plot_df_lb.sort_values("Date").groupby("StudentID").last().reset_index()
            latest[likes_col] = latest[likes_col].apply(parse_number)
            latest[foll_col] = latest[foll_col].apply(parse_number)
            latest['eng'] = latest.apply(
                lambda r: float(r.get(likes_col, 0)) / float(r.get(foll_col, 1)) if float(r.get(foll_col, 1)) else 0,
                axis=1
            )
            latest['eng'] = latest['eng'] * 100
            display_df = latest.sort_values('eng', ascending=False).head(10)
            values = display_df['eng']

        st.markdown('<div style="margin-top:.7em;">', unsafe_allow_html=True)
        for rank, (_, r) in enumerate(display_df.iterrows()):
            initials = student_initials(r['Name'])
            highlight = (
                "background:linear-gradient(97deg,#fcb69f33 60%,#a1c4fd13 100%);border-radius:13px;"
                if r['Name'] == st.session_state.selected_student else ""
            )
            val = values.iloc[rank]
            if lb_metric in ["Followers", "Follower Growth"]:
                metric_str = f"{int(round(val)):,}" if val else "0"
            else:
                metric_str = f"{val:.1f}%"
            if rank == 0:
                medal = '<span style="font-size:1.15em;color:#e1b400;margin-right:3px;">🥇</span>'
            elif rank == 1:
                medal = '<span style="font-size:1.15em;color:#bbb;margin-right:3px;">🥈</span>'
            elif rank == 2:
                medal = '<span style="font-size:1.15em;color:#cd7f32;margin-right:3px;">🥉</span>'
            else:
                medal = f'<span style="width:18px;display:inline-block;">{rank+1}</span>'
            render_leaderboard_card(
                name=r['Name'],
                initials=initials,
                metric_str=metric_str,
                color=color,
                highlight=highlight,
                medal=medal
            )
    
# --- ANALYTICS TAB ---
with menu_tabs[1]:
    st.title("Analytics")
    all_students = sorted(df['Name'].dropna().unique())
    student_filter = st.selectbox(
        "Student (optional)",
        options=["All Students"] + all_students,
        key="analytics_student"
    )
    platform_options = [p['label'] for p in PLATFORMS]
    selected_platform = st.selectbox("Platform", platform_options, key="analytics_platform")
    metric_options = ['Followers', 'Engagement', 'Follower Growth']
    selected_metric = st.selectbox("Metric", metric_options, key="analytics_metric")
    prefix = [p['prefix'] for p in PLATFORMS if p['label'] == selected_platform][0]
    foll_col = f"{prefix}_Followers"

    filtered_df = df.copy()
    if student_filter != "All Students":
        filtered_df = filtered_df[filtered_df['Name'] == student_filter]
    heatmap_student = st.selectbox("Show heatmap for student", ["All Students"] + all_students, key="heatmap_student")
    if heatmap_student == "All Students":
        heatmap_df = df.copy()
    else:
        heatmap_df = df[df['Name'] == heatmap_student].copy()

    # Make sure Date is datetime
    heatmap_df['Date'] = pd.to_datetime(heatmap_df['Date'], errors='coerce')
    heatmap_df = heatmap_df.dropna(subset=['Date'])

    # Count posts per day
    post_counts = heatmap_df.groupby(heatmap_df['Date'].dt.date).size().reset_index(name='Posts')

    # Create a full calendar for the period
    if not post_counts.empty:
        date_range = pd.date_range(post_counts['Date'].min(), post_counts['Date'].max(), freq="D")
        calendar_df = pd.DataFrame({'Date': date_range})
        calendar_df['Date'] = pd.to_datetime(calendar_df['Date'])
        calendar_df['Posts'] = calendar_df['Date'].dt.date.map(dict(zip(post_counts['Date'], post_counts['Posts']))).fillna(0)
        calendar_df['Posts'] = calendar_df['Posts'].astype(int)
        calendar_df['dow'] = calendar_df['Date'].dt.weekday  # 0 = Monday
        calendar_df['week'] = calendar_df['Date'].dt.isocalendar().week
        calendar_df['year'] = calendar_df['Date'].dt.isocalendar().year

        # Pivot to weeks x days grid
        pivot = calendar_df.pivot(index='week', columns='dow', values='Posts').fillna(0)

        # Build heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
                y=[f"Week {w}" for w in pivot.index],
                colorscale="YlGnBu",
                showscale=True,
                hovertemplate="Week %{y}, %{x}: %{z} posts<extra></extra>"
            )
        )
        fig.update_layout(
            title=f"Content Consistency Heatmap: {heatmap_student}",
            xaxis_title="Day of Week",
            yaxis_title="Week",
            yaxis_autorange="reversed",
            height=320,
            margin=dict(l=40, r=20, t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No post data to show heatmap for this student.")
    if 'Date' in filtered_df.columns and not filtered_df.empty:
        filtered_df['Date'] = pd.to_datetime(filtered_df['Date'], errors='coerce')
        date_vals = filtered_df['Date'].dropna()
        if not date_vals.empty:
            min_date = date_vals.min()
            max_date = date_vals.max()
            date_range = st.date_input(
                "Select date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            if isinstance(date_range, tuple):
                start_date, end_date = date_range
            else:
                start_date = end_date = date_range
            mask = (filtered_df['Date'] >= pd.to_datetime(start_date)) & (filtered_df['Date'] <= pd.to_datetime(end_date))
            plot_df = filtered_df[mask].copy()
        else:
            st.warning("No available dates in the data.")
            plot_df = filtered_df.copy()
            start_date = end_date = None
    else:
        st.warning("No 'Date' column in your data.")
        plot_df = filtered_df.copy()
        start_date = end_date = None

    if selected_metric == "Followers":
        latest = plot_df.sort_values("Date").groupby("StudentID").last().reset_index()
        latest[foll_col] = latest[foll_col].apply(parse_number)
        y_col = foll_col
        title_metric = "Followers"
        display_df = latest
    elif selected_metric == "Follower Growth":
        grp = plot_df.sort_values("Date").groupby("StudentID")
        first = grp.first().reset_index()
        last = grp.last().reset_index()
        growth_df = last[["StudentID", "Name", foll_col]].copy()
        growth_df = growth_df.rename(columns={foll_col: "Followers_End"})
        growth_df["Followers_Start"] = first.set_index("StudentID")[foll_col].values
        growth_df["Followers_End"] = growth_df["Followers_End"].apply(parse_number)
        growth_df["Followers_Start"] = growth_df["Followers_Start"].apply(parse_number)
        growth_df["Growth"] = growth_df["Followers_End"] - growth_df["Followers_Start"]
        display_df = growth_df.copy()
        y_col = "Growth"
        title_metric = "Follower Growth"
    else:
        likes_col = f"{prefix}_LaPostLikes"
        latest = plot_df.sort_values("Date").groupby("StudentID").last().reset_index()
        latest[likes_col] = latest[likes_col].apply(parse_number)
        latest[foll_col] = latest[foll_col].apply(parse_number)
        latest['eng'] = latest.apply(
            lambda r: float(r.get(likes_col, 0)) / float(r.get(foll_col, 1)) if float(r.get(foll_col, 1)) else 0,
            axis=1
        )
        latest['eng'] = latest['eng'] * 100
        display_df = latest
        y_col = "eng"
        title_metric = "Engagement (%)"

    st.markdown("### Follower Trend Over Time")
    timeseries_df = plot_df.sort_values("Date")
    if not timeseries_df.empty and foll_col in timeseries_df.columns:
        if student_filter == "All Students":
            top_students = display_df.sort_values(y_col, ascending=False).head(5)['Name']
        else:
            top_students = [student_filter]
        trend_df = timeseries_df[timeseries_df['Name'].isin(top_students)].copy()
        trend_df['Date'] = pd.to_datetime(trend_df['Date'])
        trend_df[foll_col] = trend_df[foll_col].apply(parse_number)
        fig = px.line(
            trend_df,
            x="Date",
            y=foll_col,
            color="Name",
            title=f"Follower Trend for {'Top 5' if student_filter=='All Students' else student_filter} on {selected_platform}",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No time series data for this metric.")

    st.markdown("### Top 10 (Bar Chart)")
    if not display_df.empty:
        plot_name = "Name" if "Name" in display_df.columns else "StudentID"
        fig = px.bar(
            display_df.sort_values(y_col, ascending=False).head(10),
            x=plot_name, y=y_col, color=y_col, color_continuous_scale="bluered",
            title=f"Top 10 {selected_platform} {title_metric} ({start_date} to {end_date})",
            labels={"y": title_metric, "x": "Student"}
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        csv = display_df.to_csv(index=False).encode()
        st.download_button("⬇️ Download This Table as CSV", csv, file_name="analytics_export.csv", mime="text/csv")
    else:
        st.info("No data for selected date range or metric.")

    st.markdown("### Platform Mix Snapshot")
    curr_snapshot = plot_df.sort_values("Date").groupby("StudentID").last().reset_index()
    pie_data = []
    for plat in PLATFORMS:
        col = f"{plat['prefix']}_Followers"
        if col in curr_snapshot.columns:
            total = curr_snapshot[col].apply(parse_number).sum()
            pie_data.append({"platform": plat['label'], "followers": total})
    pie_df = pd.DataFrame(pie_data)
    if not pie_df.empty:
        fig = px.pie(pie_df, names="platform", values="followers",
                     title=f"Platform Share (by Followers, current snapshot)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No platform mix data.")

    with st.expander("📊 Show raw data table"):
        st.dataframe(display_df)

    st.header("Weekly Engagement Metrics")
    if df_weekly.empty:
        st.info("No weekly engagement data found.")
    else:
        all_students = sorted(df_weekly['Name'].dropna().unique())
        eng_student_filter = st.selectbox(
            "Engagement: Student (optional)",
            options=["All Students"] + all_students,
            key="engagement_student"
        )
        plot_df = df_weekly.copy()
        if eng_student_filter != "All Students":
            plot_df = plot_df[plot_df['Name'] == eng_student_filter]
    
        metrics = [
            ("Videos Posted", "Videos_Posted"),
            ("Zoom Calls Attended", "Zoom_Calls_Attended"),
            ("Discord Feedback Requested", "Discord_Feedback_Requested"),
            ("% Course Completed", "Course_Completed_Percent")
        ]
    
        for title, col in metrics:
            if col not in plot_df.columns:
                st.warning(f"Column `{col}` not found in Engagement_Weekly.")
                continue
            st.markdown(f"#### {title} per Week")
            if plot_df.empty:
                st.info(f"No data for {title}")
                continue
            fig = px.bar(
                plot_df,
                x="Week",
                y=col,
                color="Name" if eng_student_filter == "All Students" else None,
                title=f"{title} Each Week"
            )
            st.plotly_chart(fig, use_container_width=True)
            with st.expander(f"📊 Show data for {title}"):
                st.dataframe(plot_df[["Name", "Week", col]])
            csv = plot_df[["Name", "Week", col]].to_csv(index=False).encode()
            st.download_button(f"⬇️ Download {title} Data as CSV", csv, file_name=f"{col}_weekly_export.csv", mime="text/csv")
st.markdown("""
    <hr style="margin-top:3em;margin-bottom:0;border:none;border-top:1.5px solid #fcb69f33;">
    <div style='text-align:center;color:#90a7d0;font-size:1.09em;margin-top:.6em;margin-bottom:0.3em;'>
        
    </div>
    """, unsafe_allow_html=True)

