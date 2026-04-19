import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import math

# ================== 页面配置 ==================
st.set_page_config(
    page_title="智能旅行规划器",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================== CSS ==================
st.markdown("""
<style>
    .main { background-color: #fef9f9; }
    .stButton > button {
        background-color: #ff5a5f;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #ff7b7f;
        color: white;
    }
    .css-1d391kg {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    h1, h2, h3 { color: #333333; }
    .day-title {
        font-size: 1.3rem;
        font-weight: bold;
        border-left: 5px solid #ff5a5f;
        padding-left: 12px;
        margin: 20px 0 10px 0;
    }
    .attraction-card {
        background: #fafafa;
        border-radius: 14px;
        padding: 10px 12px;
        margin: 8px 0;
    }
    .transport-tag {
        background: #eef2ff;
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 0.75rem;
        display: inline-block;
        margin: 5px 0;
    }
    .share-card {
        background: linear-gradient(135deg, #ffecd2, #fcb69f);
        padding: 1rem;
        border-radius: 20px;
        color: #5e2e2e;
    }
    footer {
        text-align: center;
        margin-top: 2rem;
        font-size: 0.8rem;
        color: #aaa;
    }
    .nav-item {
        padding: 8px 12px;
        margin: 5px 0;
        border-radius: 30px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ================== 景点数据库 ==================
CITY_ATTRACTIONS = {
    "北京": [
        {"name": "故宫博物院", "category": "历史文化", "hours": 3, "lat": 39.918, "lon": 116.397, "rating": 5, "desc": "明清皇家宫殿，红墙黄瓦超出片"},
        {"name": "颐和园", "category": "自然风光", "hours": 2.5, "lat": 39.999, "lon": 116.272, "rating": 4.8, "desc": "皇家园林，昆明湖泛舟"},
        {"name": "南锣鼓巷", "category": "购物美食", "hours": 1.5, "lat": 39.934, "lon": 116.403, "rating": 4.3, "desc": "老北京胡同+文艺小店"},
        {"name": "798艺术区", "category": "艺术创意", "hours": 2, "lat": 39.984, "lon": 116.495, "rating": 4.5, "desc": "工业风艺术社区，涂鸦墙"},
        {"name": "长城(慕田峪)", "category": "自然风光", "hours": 4, "lat": 40.435, "lon": 116.564, "rating": 5, "desc": "雄伟长城，人少景美"},
        {"name": "天坛公园", "category": "历史文化", "hours": 2, "lat": 39.882, "lon": 116.406, "rating": 4.7, "desc": "祈年殿经典机位"},
        {"name": "三里屯", "category": "购物美食", "hours": 2, "lat": 39.934, "lon": 116.455, "rating": 4.4, "desc": "潮流地标，太古里"},
    ],
    "上海": [
        {"name": "外滩", "category": "历史文化", "hours": 1.5, "lat": 31.242, "lon": 121.489, "rating": 4.9, "desc": "万国建筑+陆家嘴夜景"},
        {"name": "迪士尼乐园", "category": "休闲娱乐", "hours": 8, "lat": 31.143, "lon": 121.665, "rating": 5, "desc": "童话世界，烟花秀"},
        {"name": "豫园&城隍庙", "category": "历史文化", "hours": 2, "lat": 31.229, "lon": 121.487, "rating": 4.5, "desc": "江南园林+老街小吃"},
        {"name": "新天地", "category": "艺术创意", "hours": 2, "lat": 31.221, "lon": 121.473, "rating": 4.4, "desc": "石库门改造，时尚餐厅"},
        {"name": "武康路", "category": "艺术创意", "hours": 1.5, "lat": 31.213, "lon": 121.448, "rating": 4.6, "desc": "网红打卡一条街"},
        {"name": "东方明珠", "category": "休闲娱乐", "hours": 1.5, "lat": 31.242, "lon": 121.495, "rating": 4.3, "desc": "城市地标透明观景台"},
    ],
    "成都": [
        {"name": "大熊猫繁育基地", "category": "自然风光", "hours": 3, "lat": 30.732, "lon": 104.143, "rating": 5, "desc": "看滚滚卖萌"},
        {"name": "宽窄巷子", "category": "购物美食", "hours": 2, "lat": 30.663, "lon": 104.056, "rating": 4.5, "desc": "青砖古巷，盖碗茶"},
        {"name": "锦里古街", "category": "购物美食", "hours": 1.5, "lat": 30.646, "lon": 104.044, "rating": 4.4, "desc": "红灯笼夜景，小吃天堂"},
        {"name": "都江堰", "category": "历史文化", "hours": 3, "lat": 31.002, "lon": 103.617, "rating": 4.8, "desc": "古代水利工程"},
        {"name": "人民公园鹤鸣茶社", "category": "休闲娱乐", "hours": 1.5, "lat": 30.658, "lon": 104.058, "rating": 4.2, "desc": "体验巴适生活"},
    ]
}

FOOD_TIPS = {
    "北京": ["烤鸭（四季民福）", "老北京炸酱面", "铜锅涮肉", "豆汁焦圈"],
    "上海": ["小笼包（莱莱小笼）", "本帮红烧肉", "葱油拌面", "蝴蝶酥"],
    "成都": ["火锅（蜀九香）", "钵钵鸡", "蛋烘糕", "甜水面"],
}

# 城市交通模拟数据（地铁线路关键词）
CITY_TRANSIT = {
    "北京": {"subway": "地铁1/2/4号线", "bus": "公交5路/82路", "typical_cost": "打车起步价13元"},
    "上海": {"subway": "地铁2/10号线", "bus": "公交33路/576路", "typical_cost": "打车起步价14元"},
    "成都": {"subway": "地铁2/3/4号线", "bus": "公交58路/82路", "typical_cost": "打车起步价8元"},
}

# ================== 辅助函数 ==================
def haversine(lat1, lon1, lat2, lon2):
    """计算两点距离（公里）"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_transport_between(att1, att2, city):
    """返回两个景点之间的交通建议"""
    if att1.get("lat") is None or att2.get("lat") is None:
        return "🚶 步行约10分钟（附近区域）"
    dist = haversine(att1["lat"], att1["lon"], att2["lat"], att2["lon"])
    transit_info = CITY_TRANSIT.get(city, {})
    if dist < 1.5:
        return "🚶 步行约{}分钟".format(int(dist * 12))
    elif dist < 5:
        return f"🚲 共享单车 / 公交2-3站 · 约{int(dist*3)}分钟"
    elif dist < 12:
        subway = transit_info.get("subway", "地铁")
        return f"🚇 {subway} 约{int(dist*2)}分钟"
    else:
        cost = transit_info.get("typical_cost", "打车")
        return f"🚕 打车约{int(dist*2)}分钟 · {cost}"

def filter_attractions(city, interests):
    attractions = CITY_ATTRACTIONS.get(city, [])
    if interests:
        filtered = [a for a in attractions if a["category"] in interests]
    else:
        filtered = attractions.copy()
    if not filtered:
        filtered = attractions.copy()
    filtered.sort(key=lambda x: x["rating"], reverse=True)
    return filtered

def generate_daily_schedule(attractions, days, pace):
    pace_map = {"轻松": 2, "标准": 3, "紧凑": 4}
    max_per_day = pace_map.get(pace, 3)
    schedule = []
    idx = 0
    # 复制一份避免修改原数据
    pool = attractions.copy()
    for day in range(days):
        daily = []
        for _ in range(max_per_day):
            if idx < len(pool):
                daily.append(pool[idx])
                idx += 1
            else:
                daily.append({"name": "自由探索", "category": "休闲", "hours": 2, "desc": "随性发现周边小店", "rating": 3.5, "lat": None, "lon": None})
        schedule.append(daily)
    return schedule

def format_date(base_date, offset):
    if base_date:
        return (base_date + timedelta(days=offset)).strftime("%m/%d %a")
    return f"Day {offset+1}"

# ================== 侧边栏导航 ==================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1150/1150639.png", width=60)
    st.title("红书行囊")
    st.caption("📕 你的旅行灵感伙伴")
    st.markdown("---")
    
    # 导航菜单
    nav_option = st.radio(
        "📌 导航栏",
        ["🏠 规划行程", "❤️ 收藏夹", "📢 社区灵感", "👤 我的"],
        index=0,
        label_visibility="collapsed"
    )
    if nav_option == "🏠 规划行程":
        st.success("当前在行程规划器")
    elif nav_option == "❤️ 收藏夹":
        st.info("收藏功能开发中，可保存心仪行程")
    elif nav_option == "📢 社区灵感":
        st.info("查看热门笔记灵感（示例）")
    else:
        st.info("个人中心：管理你的旅行计划")

# ================== 主界面：规划行程模块 ==================
if nav_option == "🏠 规划行程":
    st.title("✈️ 一键生成你的旅行手账")
    st.caption("基于兴趣和节奏，自动规划每日行程 + 景点间交通指引")
    
    # 参数配置区（不再放在侧边栏）
    with st.expander("🗺️ 规划参数设置", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            city = st.selectbox("目的地", options=list(CITY_ATTRACTIONS.keys()), index=0)
            days = st.slider("旅行天数", 1, 5, 3)
            pace = st.select_slider("旅行节奏", options=["轻松", "标准", "紧凑"], value="标准")
        with col2:
            start_date = st.date_input("出发日期", value=datetime.today())
            # 动态获取兴趣分类
            all_cats = set()
            for att in CITY_ATTRACTIONS.get(city, []):
                all_cats.add(att["category"])
            interests = st.multiselect("兴趣偏好", options=list(all_cats), default=list(all_cats)[:2] if all_cats else [])
        
        generate_btn = st.button("✨ 生成专属行程 ✨", use_container_width=True, type="primary")
    
    # 初始化session状态
    if "schedule" not in st.session_state or generate_btn:
        with st.spinner("正在规划最适合你的路线..."):
            filtered = filter_attractions(city, interests)
            schedule = generate_daily_schedule(filtered, days, pace)
            st.session_state.schedule = schedule
            st.session_state.city = city
            st.session_state.filtered_att = filtered
            st.session_state.start_date = start_date
            st.session_state.pace = pace
    
    # 展示行程
    if "schedule" in st.session_state:
        schedule = st.session_state.schedule
        current_city = st.session_state.city
        current_start = st.session_state.start_date
        att_list = st.session_state.filtered_att
        
        # 两列布局：左行程，右地图+分享
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown(f"### 📍 {current_city} · {days}天 {st.session_state.pace}行程")
            for day_idx, day_attractions in enumerate(schedule):
                date_str = format_date(current_start, day_idx)
                st.markdown(f'<div class="day-title">🌟 第{day_idx+1}天 · {date_str}</div>', unsafe_allow_html=True)
                
                for i, att in enumerate(day_attractions):
                    # 景点卡片
                    with st.container():
                        col_a, col_b = st.columns([4, 1])
                        with col_a:
                            st.markdown(f"""
                            <div class="attraction-card">
                                <b>🏷️ {att['name']}</b> ⭐ {att.get('rating', '4.0')}<br>
                                📂 {att['category']} · ⏱️ {att.get('hours', 2)}小时<br>
                                <small>{att.get('desc', '')}</small>
                            </div>
                            """, unsafe_allow_html=True)
                        with col_b:
                            st.caption(["🌅 上午", "☀️ 中午", "🌇 下午", "🌙 晚上"][i % 4])
                    
                    # 景点之间的交通指引（除了当天最后一个景点）
                    if i < len(day_attractions) - 1:
                        next_att = day_attractions[i+1]
                        transport = get_transport_between(att, next_att, current_city)
                        st.markdown(f'<div class="transport-tag">🚗 → {transport}</div>', unsafe_allow_html=True)
                
                # 每日美食彩蛋
                food_item = random.choice(FOOD_TIPS.get(current_city, ["当地美食"]))
                st.markdown(f'<div style="background:#fff2e6; border-radius:12px; padding:6px 12px; margin:10px 0;">🍜 今日美食推荐：{food_item}</div>', unsafe_allow_html=True)
                st.markdown("---")
        
        with col_right:
            st.markdown("### 🗺️ 景点地图")
            if att_list:
                map_df = pd.DataFrame([{"lat": a["lat"], "lon": a["lon"], "name": a["name"]} for a in att_list if a.get("lat")])
                if not map_df.empty:
                    st.map(map_df, use_container_width=True)
                    st.caption("📍 筛选出的热门景点位置")
                else:
                    st.info("部分景点坐标缺失")
            else:
                st.info("暂无景点数据")
            
            st.markdown("---")
            st.markdown("### 📕 小红书分享卡")
            share_title = f"✨{current_city}{days}天{st.session_state.pace}行程 | 红书行囊✨"
            share_content = f"🗓️ 行程速览：\n"
            for idx, day in enumerate(schedule):
                names = " → ".join([a["name"][:6] for a in day[:3]])
                share_content += f"Day{idx+1}: {names}\n"
            share_content += f"\n🍜 地道美食：{random.choice(FOOD_TIPS.get(current_city, ['当地小吃']))}\n"
            share_content += "#旅行攻略 #小众打卡地 #小红书旅行"
            
            with st.expander("📸 点击生成分享卡片", expanded=True):
                st.markdown(f"""
                <div class="share-card">
                    <h4>📖 {share_title}</h4>
                    <p style="font-size:0.9rem;">{share_content}</p>
                    <div style="display:flex; justify-content:space-between;">
                        <span>❤️ 收藏 1.2w</span>
                        <span>💬 45</span>
                        <span>✈️ 一键复制</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("📋 复制文案", key="copy"):
                    st.success("文案已复制（演示）", icon="✅")
            
            st.markdown("### 🎒 打包清单")
            st.markdown("- 身份证/护照\n- 充电宝+相机\n- 舒适运动鞋\n- 防晒/雨伞")
    
    # 底部指标
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("覆盖景点", f"{len(att_list)}个")
    with col_b:
        total_hours = sum([a.get('hours',0) for day in schedule for a in day])
        st.metric("游览时长", f"{total_hours:.0f}小时")
    with col_c:
        st.metric("小红书热度", "🔥 4.8")

else:
    # 其他导航模块的占位（演示）
    st.info(f"✨ 当前模块：「{nav_option}」 正在建设中，核心功能请查看「规划行程」")
    st.image("https://cdn-icons-png.flaticon.com/512/1046/1046784.png", width=200)
    st.caption("后续可接入用户收藏、社区笔记推荐等功能")
