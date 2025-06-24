import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import plotly.express as px
import urllib.parse

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
    font-size: 2.2em;
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
    🚀 Viral Video Club - Bootcamp Social Media Dashboard
</div>
""", unsafe_allow_html=True)

# ---- Google Sheets ----
SHEET_ID = '1MvGIdmM9eW89vSIoMzlg6k8x6oXBr1XKfrCoLIBkzq0'
SHEET_NAME = 'History'
JSON_KEYFILE = '/Users/joshbatuigas/service-account.json'
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

@st.cache_data(ttl=300)
def load_data():
    return pd.DataFrame(sheet.get_all_records())
df = load_data()

df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.sort_values("Date").drop_duplicates(subset=["StudentID", "Date"], keep="last")

PLATFORMS = [
    {"label": "Instagram", "user": "IG_Username", "foll": "IG_Followers", "foll_last": "IG_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/instagram.svg", "brand": "#E1306C", "prefix": "IG"},
    {"label": "TikTok", "user": "TT_Username", "foll": "TT_Followers", "foll_last": "TT_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/tiktok.svg", "brand": "#ae9e9e", "display": "#232323", "prefix": "TT"},
    {"label": "YouTube", "user": "YT_Username", "foll": "YT_Followers", "foll_last": "YT_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/youtube.svg", "brand": "#FF0000", "prefix": "YT"},
    {"label": "Threads", "user": "TH_Username", "foll": "TH_Followers", "foll_last": "TH_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/threads.svg", "brand": "#a59f9f", "prefix": "TH"},
    {"label": "LinkedIn", "user": "LI_Username", "foll": "LI_Followers", "foll_last": "LI_Followers_Last", "emoji": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linkedin.svg", "brand": "#938E8E", "display": "#126BC4", "prefix": "LI"},
]

menu_tabs = st.tabs(["Dashboard", "Analytics"])

with menu_tabs[0]:
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        latest_date = df['Date'].max()
        curr_df = df[df['Date'] == latest_date].copy()
    else:
        curr_df = df.copy()

    lcol, ccol, rcol = st.columns([1.2, 2.2, 1.2], gap="large")

    # ---- LEFT: Student Search & Scrollable, Clickable List ----
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
        .scroll-list { max-height: 430px; overflow-y: auto; padding-right: 6px;}
        .scroll-list::-webkit-scrollbar {width:7px;background:#fff;}
        .scroll-list::-webkit-scrollbar-thumb {background:#fcb69f99;border-radius:8px;}
        .student-card {
            display: flex; align-items: center; gap: 15px;
            padding: 7px 10px; border-radius: 13px; margin-bottom: 4px;
            background: #fff; cursor: pointer; border: 1.5px solid transparent; transition: background .13s, border .13s;
        }
        .student-card.selected { background: #fcb69f33; border-color: #fa7a3a60;}
        .student-card:hover {
            background: #fae0d033;
            border-color: #fa7a3acc;
        }
        .student-initials {
            width: 41px; height: 41px; border-radius: 50%;
            background: linear-gradient(120deg,#fcb69f 70%,#90a7d0 100%);
            color: #fff; font-family: Pacifico, cursive; font-size: 1.19em; font-weight: bold;
            display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 6px #a1c4fd33;
        }
        .student-name {
            font-weight:700;
            color:#232323;
            font-size:1.07em;
            white-space:normal;        /* Allow wrapping */
            max-width:none;            /* No cutoff */
            overflow:visible;          /* No hiding */
            text-overflow:clip;        /* No ellipsis */
        }
        .student-btn-form {margin:0;}
        </style>
        <div class="scroll-list">
        """, unsafe_allow_html=True)
        student_html = ""
        for i, n in enumerate(student_names):
            initials = student_initials(n)
            selected = (n == st.session_state.selected_student)
            card_class = "student-card selected" if selected else "student-card"
            student_html += f"""
            <form action="#student_{i}" method="get" class="student-btn-form">
                <button name="student" value="{n}" type="submit" style="all:unset;width:100%;">
                    <div class="{card_class}" id="student_{i}">
                        <div class="student-initials">{initials}</div>
                        <span class="student-name">{n}</span>
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
    with ccol:
        st.markdown("#### Student Feed")
        selected_student = st.session_state.selected_student
        show_df = curr_df[curr_df['Name'] == selected_student] if selected_student in curr_df['Name'].values else curr_df.head(1)
        for _, row in show_df.iterrows():
            st.markdown(f"### {row['Name']}")
            main_platform = max(PLATFORMS, key=lambda p: parse_number(row.get(p['foll'], 0)))
            for plat in PLATFORMS:
                user_val = safe(row.get(plat["user"], ""))
                if not user_val:
                    continue  # hide if no username/account

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

                cap_trunc = (cap_val[:110] + "…") if cap_val and len(cap_val) > 110 else cap_val

                highlight = (
                    "box-shadow:0 8px 32px #e1306c15;"
                    if plat['label'] == main_platform['label'] and foll_val > 0 else ""
                )

                foll_display = f"{int(round(foll_val)):,}" if foll_val else ""
                growth_display = (
                    f"<span style='background:#ebfdc1;border-radius:8px;padding:.20em .7em;margin-left:.4em;font-weight:700;color:#2b8328;'>+{int(follower_growth):,}</span>" if follower_growth > 0 else
                    f"<span style='background:#fde1e1;border-radius:8px;padding:.20em .7em;margin-left:.4em;font-weight:700;color:#c81c1c;'>{int(follower_growth):,}</span>" if follower_growth < 0 else
                    ""
                )
                engagement_display = (
                    f"<span style='background:#ebfdc1;border-radius:8px;padding:.19em .6em;margin-left:.4em;font-weight:700;color:#7fa569;'>{engagement:.1f}%</span>" if engagement else ""
                )

                date_display = date_val if date_val else ""
                url_html = ""
                if url_val:
                    url_html = f'<a href="{url_val}" target="_blank" style="color:{plat["brand"]};font-weight:700;text-decoration:underline;">{cap_trunc or "View Post"}</a>'

                likes_display = f"{int(round(likes_val)):,}" if likes_val else ""
                comm_display = f"{int(round(comm_val)):,}" if comm_val else ""
                
                def sanitize_html(text):
                    return str(text).replace("```", "").lstrip()

                lines = []
                if date_display:
                    lines.append(f"<div style='color:#aaa;'>{date_display}</div>")
                if url_html:
                    lines.append(f"<div style='margin:.5em 0 .1em 0;font-size:1.09em;'>{url_html}</div>")
                stat_line = []
                if likes_display:
                    stat_line.append(f"👍 <b>{likes_display}</b>")
                if comm_display:
                    stat_line.append(f"💬 <b>{comm_display}</b>")
                if stat_line:
                    lines.append(f"<div style='color:#232323;font-size:1.15em;margin-top:.5em;'>{' &nbsp; '.join(stat_line)}</div>")

                info_lines = "\n".join(lines)
                st.markdown(
                f"""
                <div style="background:#fff;border-radius:22px;box-shadow:0 4px 16px #0001;{highlight}
                    border-top:8px solid {plat['brand']};margin-bottom:1.5em;padding:2em 2em 1.2em 2em;">
                    <div style='display:flex;align-items:center;gap:18px;margin-bottom:.6em;'>
                        <img src='{plat["emoji"]}' width=52 height=52 ...>
                        <span style="...">{plat['label']}</span>
                    </div>
                    <div style="color:#90a7d0;">
                        @{user_val}{f" • <b>{foll_display}</b> Followers" if foll_display else ""}
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
with menu_tabs[1]:
    st.title("Analytics")

    # ----- Student Filter -----
    all_students = sorted(df['Name'].dropna().unique())
    student_filter = st.selectbox(
        "Student (optional)",
        options=["All Students"] + all_students,
        key="analytics_student"
    )

    # Platform + metric selection
    platform_options = [p['label'] for p in PLATFORMS]
    selected_platform = st.selectbox("Platform", platform_options, key="analytics_platform")
    metric_options = ['Followers', 'Engagement', 'Follower Growth']
    selected_metric = st.selectbox("Metric", metric_options, key="analytics_metric")

    prefix = [p['prefix'] for p in PLATFORMS if p['label'] == selected_platform][0]
    foll_col = f"{prefix}_Followers"

    # --- Filter data by student if selected ---
    filtered_df = df.copy()
    if student_filter != "All Students":
        filtered_df = filtered_df[filtered_df['Name'] == student_filter]

    # Date range picker
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

    # --- Metric calculation ---
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
    else:  # Engagement
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

    # ---- 1. Time Series Line Chart: Followers Trend ----
    st.markdown("### Follower Trend Over Time")
    timeseries_df = plot_df.sort_values("Date")
    if not timeseries_df.empty and foll_col in timeseries_df.columns:
        # Pick top N students (or just the selected) to plot
        if student_filter == "All Students":
            top_students = display_df.sort_values(y_col, ascending=False).head(5)['Name']
        else:
            top_students = [student_filter]
        trend_df = timeseries_df[timeseries_df['Name'].isin(top_students)].copy()
        trend_df['Date'] = pd.to_datetime(trend_df['Date'])
        trend_df[foll_col] = trend_df[foll_col].apply(parse_number)
        import plotly.express as px
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

    # ---- 2. Bar Chart: Top 10 ----
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
    else:
        st.info("No data for selected date range or metric.")

    # ---- 3. Platform Mix: Pie Chart (current snapshot) ----
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

    # ---- 4. Data Table (optional, toggle) ----
    with st.expander("Show raw data table"):
        st.dataframe(display_df)
