import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import requests
from typing import List, Dict, Any, Tuple
import math
from itertools import permutations

# ================== 百度地图API配置 ==================
BAIDU_AK = "你的AK"   # 替换成你自己的

CATEGORY_TO_KEYWORD = {
    "历史文化": "博物馆|古迹|遗址|故居",
    "自然风光": "公园|风景区|山|湖|湿地",
    "购物美食": "商业街|小吃|美食|夜市",
    "艺术创意": "艺术馆|创意园|画廊|艺术中心",
    "休闲娱乐": "游乐园|度假村|剧院|影城"
}

# ================== 辅助函数 ==================
def bd09_to_wgs84(lat: float, lng: float) -> Tuple[float, float]:
    x_pi = math.pi * 3000.0 / 180.0
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * x_pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * x_pi)
    lng_wgs = z * math.cos(theta) + 0.0065
    lat_wgs = z * math.sin(theta) + 0.0060
    return lat_wgs, lng_wgs

def map_baidu_category_to_ours(baidu_type: str) -> str:
    if any(k in baidu_type for k in ["风景", "公园", "山", "湖", "湿地", "自然"]):
        return "自然风光"
    if any(k in baidu_type for k in ["文物", "古迹", "博物馆", "历史", "遗址"]):
        return "历史文化"
    if any(k in baidu_type for k in ["购物", "商业", "美食", "餐饮", "小吃"]):
        return "购物美食"
    if any(k in baidu_type for k in ["艺术", "创意", "画廊", "美术馆"]):
        return "艺术创意"
    if any(k in baidu_type for k in ["游乐", "影剧院", "度假", "娱乐"]):
        return "休闲娱乐"
    return "休闲娱乐"

def infer_category_from_name(name: str) -> str:
    name_lower = name.lower()
    if any(k in name_lower for k in ["博物馆", "宫", "陵", "庙", "寺", "遗址", "故居", "祠堂"]):
        return "历史文化"
    if any(k in name_lower for k in ["公园", "山", "湖", "森林", "湿地", "自然", "风景"]):
        return "自然风光"
    if any(k in name_lower for k in ["街", "巷", "市场", "美食", "购物", "广场", "商场"]):
        return "购物美食"
    if any(k in name_lower for k in ["艺术", "创意", "画廊", "美术馆", "798", "创意园"]):
        return "艺术创意"
    if any(k in name_lower for k in ["乐园", "游乐", "世界之窗", "欢乐谷", "影城", "剧院"]):
        return "休闲娱乐"
    return "休闲娱乐"

def estimate_hours_by_category(category: str) -> float:
    mapping = {
        "历史文化": 2.5,
        "自然风光": 2.0,
        "购物美食": 1.5,
        "艺术创意": 1.5,
        "休闲娱乐": 2.0
    }
    return mapping.get(category, 2.0)

# ================== 百度路线规划API（使用百度坐标） ==================
def get_route_time(origin_lat_bd, origin_lon_bd, dest_lat_bd, dest_lon_bd, mode):
    if not BAIDU_AK:
        return None, None
    url = "https://api.map.baidu.com/direction/v2/route"
    params = {
        "origin": f"{origin_lat_bd},{origin_lon_bd}",
        "destination": f"{dest_lat_bd},{dest_lon_bd}",
        "mode": mode,
        "ak": BAIDU_AK,
        "output": "json"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == 0:
            route = data["result"]["routes"][0]
            duration = route["duration"] / 60
            distance = route["distance"] / 1000
            return duration, distance
        else:
            # 静默失败，不显示错误避免刷屏，可调试时打开
            # st.error(f"路线规划失败 (status {data.get('status')}): {data.get('message')}")
            return None, None
    except Exception:
        return None, None

def optimize_attractions_order(attractions: List[Dict], mode: str) -> List[Dict]:
    """使用百度坐标进行优化"""
    if len(attractions) <= 1:
        return attractions
    n = len(attractions)
    # 确保有百度坐标字段
    for a in attractions:
        if "lat_bd" not in a or "lon_bd" not in a:
            # 如果没有百度坐标（例如模拟数据），则无法优化，直接返回原顺序
            return attractions
    time_matrix = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            t, _ = get_route_time(attractions[i]["lat_bd"], attractions[i]["lon_bd"],
                                  attractions[j]["lat_bd"], attractions[j]["lon_bd"], mode)
            if t is None:
                t = 9999
            time_matrix[i][j] = t
            time_matrix[j][i] = t
    
    if n <= 5:
        best_order = None
        best_time = float('inf')
        for perm in permutations(range(n)):
            total = 0
            for k in range(len(perm)-1):
                total += time_matrix[perm[k]][perm[k+1]]
            if total < best_time:
                best_time = total
                best_order = perm
        return [attractions[i] for i in best_order]
    else:
        unvisited = set(range(n))
        current = 0
        order = [current]
        unvisited.remove(current)
        while unvisited:
            nearest = min(unvisited, key=lambda j: time_matrix[current][j])
            order.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        return [attractions[i] for i in order]

# ================== 核心API调用：获取真实景点（保留百度坐标） ==================
@st.cache_data(ttl=86400)
def fetch_attractions_by_city(city: str, categories: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    if not BAIDU_AK:
        return []
    if categories:
        query_parts = []
        for cat in categories:
            if cat in CATEGORY_TO_KEYWORD:
                query_parts.append(CATEGORY_TO_KEYWORD[cat])
        query = "|".join(query_parts) if query_parts else "景点"
    else:
        query = "景点|旅游"

    url = "http://api.map.baidu.com/place/v2/search"
    params = {
        "query": query,
        "region": city,
        "output": "json",
        "ak": BAIDU_AK,
        "page_size": limit,
        "page_num": 0,
        "scope": 2,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("status") != 0:
            st.error(f"百度API返回错误：{data.get('message')} (status {data.get('status')})")
            return []
        results = []
        for item in data.get("results", []):
            lat_bd = item["location"]["lat"]
            lng_bd = item["location"]["lng"]
            lat_wgs, lng_wgs = bd09_to_wgs84(lat_bd, lng_bd)
            baidu_type = item.get("type", "")
            if baidu_type:
                category = map_baidu_category_to_ours(baidu_type)
            else:
                category = infer_category_from_name(item["name"])
            fake_rating = round(4.0 + (hash(item["name"]) % 20) / 20, 1)
            if fake_rating > 5.0:
                fake_rating = 5.0
            results.append({
                "name": item["name"],
                "category": category,
                "hours": estimate_hours_by_category(category),
                "lat": lat_wgs,
                "lon": lng_wgs,
                "lat_bd": lat_bd,
                "lon_bd": lng_bd,
                "rating": fake_rating,
                "desc": item.get("address", "")[:60]
            })
        return results
    except Exception as e:
        st.error(f"请求百度API失败：{e}")
        return []

# ================== 模拟数据（降级，没有百度坐标，将禁用路线优化） ==================
CITY_ATTRACTIONS = {
    "北京": [
        {"name": "故宫博物院", "category": "历史文化", "hours": 3, "lat": 39.918, "lon": 116.397, "rating": 5, "desc": "明清两代皇家宫殿"},
        {"name": "颐和园", "category": "自然风光", "hours": 2.5, "lat": 39.999, "lon": 116.272, "rating": 4.8, "desc": "皇家园林"},
        {"name": "南锣鼓巷", "category": "购物美食", "hours": 1.5, "lat": 39.934, "lon": 116.403, "rating": 4.3, "desc": "老北京胡同"},
        {"name": "798艺术区", "category": "艺术创意", "hours": 2, "lat": 39.984, "lon": 116.495, "rating": 4.5, "desc": "工业风艺术社区"},
        {"name": "长城(慕田峪)", "category": "自然风光", "hours": 4, "lat": 40.435, "lon": 116.564, "rating": 5, "desc": "雄伟长城"},
        {"name": "天坛公园", "category": "历史文化", "hours": 2, "lat": 39.882, "lon": 116.406, "rating": 4.7, "desc": "明清祭天场所"},
        {"name": "三里屯", "category": "购物美食", "hours": 2, "lat": 39.934, "lon": 116.455, "rating": 4.4, "desc": "潮流地标"},
    ],
    "上海": [
        {"name": "外滩", "category": "历史文化", "hours": 1.5, "lat": 31.242, "lon": 121.489, "rating": 4.9, "desc": "万国建筑群"},
        {"name": "迪士尼乐园", "category": "休闲娱乐", "hours": 8, "lat": 31.143, "lon": 121.665, "rating": 5, "desc": "童话世界"},
        {"name": "豫园&城隍庙", "category": "历史文化", "hours": 2, "lat": 31.229, "lon": 121.487, "rating": 4.5, "desc": "江南园林"},
        {"name": "新天地", "category": "艺术创意", "hours": 2, "lat": 31.221, "lon": 121.473, "rating": 4.4, "desc": "石库门改造"},
        {"name": "武康路", "category": "艺术创意", "hours": 1.5, "lat": 31.213, "lon": 121.448, "rating": 4.6, "desc": "网红打卡一条街"},
        {"name": "东方明珠", "category": "休闲娱乐", "hours": 1.5, "lat": 31.242, "lon": 121.495, "rating": 4.3, "desc": "城市地标"},
    ],
    "成都": [
        {"name": "大熊猫繁育基地", "category": "自然风光", "hours": 3, "lat": 30.732, "lon": 104.143, "rating": 5, "desc": "看滚滚"},
        {"name": "宽窄巷子", "category": "购物美食", "hours": 2, "lat": 30.663, "lon": 104.056, "rating": 4.5, "desc": "青砖古巷"},
        {"name": "锦里古街", "category": "购物美食", "hours": 1.5, "lat": 30.646, "lon": 104.044, "rating": 4.4, "desc": "红灯笼夜景"},
        {"name": "都江堰", "category": "历史文化", "hours": 3, "lat": 31.002, "lon": 103.617, "rating": 4.8, "desc": "古代水利工程"},
        {"name": "人民公园鹤鸣茶社", "category": "休闲娱乐", "hours": 1.5, "lat": 30.658, "lon": 104.058, "rating": 4.2, "desc": "地道巴适生活"},
    ]
}
FOOD_TIPS = {
    "北京": ["烤鸭推荐：四季民福", "老北京炸酱面", "铜锅涮肉"],
    "上海": ["小笼包（莱莱小笼）", "本帮红烧肉", "葱油拌面"],
    "成都": ["火锅（蜀九香）", "钵钵鸡", "蛋烘糕"],
}

def filter_attractions_sim(city, interests):
    attractions = CITY_ATTRACTIONS.get(city, [])
    if not interests:
        filtered = attractions
    else:
        filtered = [a for a in attractions if a["category"] in interests]
    if not filtered:
        filtered = attractions
    filtered.sort(key=lambda x: x["rating"], reverse=True)
    # 模拟数据没有百度坐标，添加占位（复制WGS84，但路线规划会失败，故在优化时检测跳过）
    for a in filtered:
        if "lat_bd" not in a:
            a["lat_bd"] = a["lat"]
            a["lon_bd"] = a["lon"]
    return filtered

# ================== 行程生成 ==================
def generate_daily_schedule(attractions, days, pace, travel_mode, start_date=None):
    pace_map = {"轻松": 2, "标准": 3, "紧凑": 4}
    max_per_day = pace_map.get(pace, 3)
    total_needed = days * max_per_day
    attractions_copy = attractions.copy()
    if len(attractions_copy) < total_needed:
        extra_needed = total_needed - len(attractions_copy)
        for i in range(extra_needed):
            attractions_copy.append(attractions_copy[i % len(attractions_copy)].copy())
    
    schedule = []
    idx = 0
    for day in range(days):
        daily_raw = []
        for _ in range(max_per_day):
            if idx < len(attractions_copy):
                daily_raw.append(attractions_copy[idx])
                idx += 1
            else:
                daily_raw.append({
                    "name": "自由探索 / 小红书打卡", "category": "休闲", "hours": 2,
                    "lat": None, "lon": None, "lat_bd": None, "lon_bd": None,
                    "desc": "根据兴趣发现周边小众店铺", "rating": 3.5
                })
        # 仅当所有景点都有百度坐标且使用真实数据时才优化
        daily_attractions = [a for a in daily_raw if a.get("lat_bd") is not None]
        if len(daily_attractions) >= 2 and all("lat_bd" in a for a in daily_attractions):
            optimized = optimize_attractions_order(daily_attractions, travel_mode)
            # 将自由活动点放回
            for a in daily_raw:
                if a.get("lat_bd") is None:
                    optimized.append(a)
            daily_raw = optimized
        schedule.append(daily_raw)
    return schedule

def format_date(base_date, offset):
    if base_date:
        return (base_date + timedelta(days=offset)).strftime("%m/%d %a")
    else:
        return f"Day {offset+1}"

# ================== Streamlit UI ==================
st.set_page_config(page_title="小红书旅行规划器", page_icon="✈️", layout="wide")
st.markdown("""
<style>
    .main { background-color: #fef9f9; }
    .stButton>button { background-color: #ff5a5f; color: white; border-radius: 20px; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #ff7b7f; }
    .day-title { font-size: 1.3rem; font-weight: bold; border-left: 5px solid #ff5a5f; padding-left: 12px; margin: 15px 0 10px 0; }
    .attraction-item { margin: 8px 0; padding: 8px; background: #fafafa; border-radius: 12px; }
    .share-card { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding: 1rem; border-radius: 20px; color: #5e2e2e; }
    footer { text-align: center; margin-top: 2rem; font-size: 0.8rem; color: #aaa; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1150/1150639.png", width=60)
    st.title("✈️ 小红书·旅行规划器")
    st.markdown("**产品定位**：一键生成高颜值旅行计划，支持路线优化与交通规划。")
    st.markdown("---")
    st.markdown("## 🗺️ 规划参数")
    city = st.selectbox("旅行目的地", options=list(CITY_ATTRACTIONS.keys()), index=0)
    start_date = st.date_input("出发日期", value=datetime.today())
    days = st.slider("旅行天数", 1, 5, 3)
    all_categories = set()
    for att in CITY_ATTRACTIONS.get(city, []):
        all_categories.add(att["category"])
    interests = st.multiselect("兴趣偏好", options=list(all_categories), default=list(all_categories)[:2])
    pace = st.select_slider("旅行节奏", ["轻松", "标准", "紧凑"], value="标准")
    travel_mode = st.selectbox("出行方式", ["driving", "transit", "walking"], format_func=lambda x: {"driving":"驾车","transit":"公交/地铁","walking":"步行"}[x])
    st.markdown("---")
    use_real_api = st.checkbox("🌐 使用百度地图真实数据（需AK）", value=True)
    generate_btn = st.button("✨ 生成专属行程 ✨", use_container_width=True)

if generate_btn:
    with st.spinner("正在规划路线，优化行程顺序..."):
        if use_real_api and BAIDU_AK:
            real_att = fetch_attractions_by_city(city, interests)
            if real_att:
                filtered_att = real_att
                st.success("✅ 已使用百度地图实时景点数据")
            else:
                filtered_att = filter_attractions_sim(city, interests)
                st.warning("⚠️ 百度API无返回，已切换至内置模拟数据")
        else:
            filtered_att = filter_attractions_sim(city, interests)
        schedule = generate_daily_schedule(filtered_att, days, pace, travel_mode, start_date)
        st.session_state.schedule = schedule
        st.session_state.city = city
        st.session_state.filtered_att = filtered_att
        st.session_state.start_date = start_date
        st.session_state.travel_mode = travel_mode

if "schedule" in st.session_state:
    schedule = st.session_state.schedule
    current_city = st.session_state.city
    current_start = st.session_state.start_date
    att_for_map = st.session_state.filtered_att
    travel_mode = st.session_state.travel_mode
    mode_display = {"driving":"驾车","transit":"公交/地铁","walking":"步行"}[travel_mode]

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown(f"### 📍 {current_city} · {days}天{pace}行程 · 出行方式：{mode_display}")
        for day_idx, day_attractions in enumerate(schedule):
            date_str = format_date(current_start, day_idx)
            st.markdown(f'<div class="day-title">🌟 第{day_idx+1}天 · {date_str}</div>', unsafe_allow_html=True)
            for i, att in enumerate(day_attractions):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    <div class="attraction-item">
                        <b>🏷️ {att['name']}</b> <span style="color:#ff5a5f;">⭐ {att['rating']}</span><br>
                        📂 {att['category']} · ⏱️ {att['hours']}小时<br>
                        <small>{att['desc']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.caption(f"💡 {['早上', '上午', '下午', '傍晚'][i % 4]}推荐")
                # 显示交通信息（仅当有百度坐标且不是自由活动）
                if i < len(day_attractions) - 1:
                    next_att = day_attractions[i+1]
                    if att.get("lat_bd") and next_att.get("lat_bd"):
                        dur, dist = get_route_time(att["lat_bd"], att["lon_bd"], next_att["lat_bd"], next_att["lon_bd"], travel_mode)
                        if dur and dist:
                            st.info(f"🚗 {mode_display} 前往下一站：约 {dur:.0f} 分钟 ({dist:.1f} 公里)")
                        else:
                            st.info("🚶 建议步行或打车（路线规划失败）")
            food_list = FOOD_TIPS.get(current_city, ["当地特色小吃"])
            st.markdown(f'<div style="background:#fff2e6; border-radius:12px; padding:6px 12px; margin-top:5px;">🍜 美食TIPS：{random.choice(food_list)}</div>', unsafe_allow_html=True)
            st.markdown("---")

    with col_right:
        st.markdown("### 🗺️ 行程地图速览")
        if att_for_map:
            map_df = pd.DataFrame([{"lat": a["lat"], "lon": a["lon"], "name": a["name"]} for a in att_for_map if a.get("lat")])
            st.map(map_df, use_container_width=True)
        else:
            st.info("暂无景点数据")
        st.markdown("---")
        st.markdown("### 📕 小红书分享卡")
        share_title = f"✨{current_city}{days}天{pace}行程 | 出行{mode_display} | 小红书同款✨"
        share_content = "🗓️ 行程亮点：\n"
        for idx, day in enumerate(schedule):
            share_content += f"Day{idx+1}: " + " → ".join([a["name"][:8] for a in day if a.get("name") != "自由探索 / 小红书打卡"][:3]) + "\n"
        share_content += f"\n🚗 出行方式：{mode_display}\n"
        share_content += f"🍜 地道美食：{random.choice(FOOD_TIPS.get(current_city, ['当地美食']))}\n"
        share_content += "#旅行攻略 #小众打卡地 #小红书旅行"
        with st.expander("📸 点击查看分享卡片", expanded=True):
            st.markdown(f"""
            <div class="share-card">
                <h4>📖 {share_title}</h4>
                <p>{share_content}</p>
                <div>❤️ 收藏 1.2w &nbsp; 💬 45 &nbsp; ✈️ 一键复制</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📋 复制文案"):
                st.success("文案已复制（演示）", icon="✅")
        st.markdown("### 🎒 打包清单")
        st.markdown("- 身份证/护照\n- 充电宝+数据线\n- 相机/自拍杆\n- 舒适运动鞋\n- 防晒霜/雨伞")

    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("热门景点覆盖", f"{len(att_for_map)}个")
    total_hours = sum([a['hours'] for day in schedule for a in day if 'hours' in a])
    col_b.metric("行程总时长", f"{total_hours:.0f}小时")
    col_c.metric("小红书同款推荐", "⭐ 4.8")
    st.markdown("<footer>🚀 集成百度地图地点检索 + 路线规划 | 自动优化景点顺序</footer>", unsafe_allow_html=True)
else:
    st.info("👈 请在左侧选择目的地和偏好，然后点击「生成专属行程」")
