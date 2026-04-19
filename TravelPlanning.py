import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import requests
from typing import List, Dict, Any, Tuple
import math

# ================== 百度地图API配置 ==================
# 方式1：直接填写你的AK（不推荐公开代码，仅个人测试）
# BAIDU_AK = "你的AK"

# 方式2：从 Streamlit secrets 读取（推荐）
# 在 .streamlit/secrets.toml 中写入：BAIDU_AK = "你的AK"
BAIDU_AK = st.secrets.get("BAIDU_AK", "")

# 兴趣类别 -> 百度地图检索关键词映射
CATEGORY_TO_KEYWORD = {
    "历史文化": "博物馆|古迹|遗址|故居",
    "自然风光": "公园|风景区|山|湖|湿地",
    "购物美食": "商业街|小吃|美食|夜市",
    "艺术创意": "艺术馆|创意园|画廊|艺术中心",
    "休闲娱乐": "游乐园|度假村|剧院|影城"
}

# ================== 辅助函数：百度坐标转WGS84（近似） ==================
def bd09_to_wgs84(lat: float, lng: float) -> Tuple[float, float]:
    """
    百度坐标系(bd09ll)转WGS84（供st.map使用）
    注意：这是一个近似算法，精度在几米到几十米。如需更精确，可使用第三方库如 coord-convert。
    """
    x_pi = math.pi * 3000.0 / 180.0
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * x_pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * x_pi)
    lng_wgs = z * math.cos(theta) + 0.0065
    lat_wgs = z * math.sin(theta) + 0.0060
    return lat_wgs, lng_wgs

def map_baidu_category_to_ours(baidu_type: str) -> str:
    """将百度POI的type字段映射到我们的五类兴趣"""
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
    return "休闲娱乐"  # 默认

def estimate_hours_by_category(category: str) -> float:
    """根据类别粗略估算游玩时长（小时）"""
    mapping = {
        "历史文化": 2.5,
        "自然风光": 2.0,
        "购物美食": 1.5,
        "艺术创意": 1.5,
        "休闲娱乐": 2.0
    }
    return mapping.get(category, 2.0)

# ================== 核心API调用：获取真实景点 ==================
@st.cache_data(ttl=86400)  # 缓存一天
def fetch_attractions_by_city(city: str, categories: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    调用百度地图地点检索API，根据城市和兴趣类别获取景点列表。
    返回格式与模拟数据一致。
    如果AK无效或请求失败，返回空列表，由调用方降级到模拟数据。
    """
    if not BAIDU_AK:
        st.warning("未配置百度地图AK（BAIDU_AK），将使用内置模拟数据。请在secrets中设置或直接赋值。")
        return []
    
    # 构建检索词
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
        "scope": 2  # 返回详细信息
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
            
            category = map_baidu_category_to_ours(item.get("type", ""))
            # 模拟评分：因为没有真实评分，根据热度或随机生成，确保用户有选择依据
            # 实际项目中可接入大众点评或高德评分
            fake_rating = round(4.0 + (hash(item["name"]) % 20) / 20, 1)
            if fake_rating > 5.0:
                fake_rating = 5.0
            
            results.append({
                "name": item.get("name", "未知景点"),
                "category": category,
                "hours": estimate_hours_by_category(category),
                "lat": lat_wgs,
                "lon": lng_wgs,
                "rating": fake_rating,
                "desc": item.get("address", "")[:60]  # 地址作为简短描述
            })
        return results
    except Exception as e:
        st.error(f"请求百度API失败：{e}")
        return []

# ================== 模拟数据（降级方案） ==================
# 原有模拟景点库（保留作为fallback）
CITY_ATTRACTIONS = {
    "北京": [
        {"name": "故宫博物院", "category": "历史文化", "hours": 3, "lat": 39.918, "lon": 116.397, "rating": 5, "desc": "明清两代皇家宫殿，世界文化遗产，红墙黄瓦超出片"},
        {"name": "颐和园", "category": "自然风光", "hours": 2.5, "lat": 39.999, "lon": 116.272, "rating": 4.8, "desc": "皇家园林，昆明湖+万寿山，泛舟赏景"},
        {"name": "南锣鼓巷", "category": "购物美食", "hours": 1.5, "lat": 39.934, "lon": 116.403, "rating": 4.3, "desc": "老北京胡同+文艺小店+地道小吃"},
        {"name": "798艺术区", "category": "艺术创意", "hours": 2, "lat": 39.984, "lon": 116.495, "rating": 4.5, "desc": "工业风艺术社区，展览&涂鸦墙，拍照圣地"},
        {"name": "长城(慕田峪)", "category": "自然风光", "hours": 4, "lat": 40.435, "lon": 116.564, "rating": 5, "desc": "雄伟长城，人少景美，缆车上下"},
        {"name": "天坛公园", "category": "历史文化", "hours": 2, "lat": 39.882, "lon": 116.406, "rating": 4.7, "desc": "明清祭天场所，祈年殿经典机位"},
        {"name": "三里屯", "category": "购物美食", "hours": 2, "lat": 39.934, "lon": 116.455, "rating": 4.4, "desc": "潮流地标，太古里逛街+餐厅酒吧"},
    ],
    "上海": [
        {"name": "外滩", "category": "历史文化", "hours": 1.5, "lat": 31.242, "lon": 121.489, "rating": 4.9, "desc": "万国建筑群+陆家嘴夜景，绝美黄浦江畔"},
        {"name": "迪士尼乐园", "category": "休闲娱乐", "hours": 8, "lat": 31.143, "lon": 121.665, "rating": 5, "desc": "童话世界，烟花秀必看"},
        {"name": "豫园&城隍庙", "category": "历史文化", "hours": 2, "lat": 31.229, "lon": 121.487, "rating": 4.5, "desc": "江南园林+老街小吃"},
        {"name": "新天地", "category": "艺术创意", "hours": 2, "lat": 31.221, "lon": 121.473, "rating": 4.4, "desc": "石库门改造，时尚餐厅&画廊"},
        {"name": "武康路", "category": "艺术创意", "hours": 1.5, "lat": 31.213, "lon": 121.448, "rating": 4.6, "desc": "网红打卡一条街，老洋房+咖啡店"},
        {"name": "东方明珠", "category": "休闲娱乐", "hours": 1.5, "lat": 31.242, "lon": 121.495, "rating": 4.3, "desc": "城市地标，透明观景台"},
    ],
    "成都": [
        {"name": "大熊猫繁育基地", "category": "自然风光", "hours": 3, "lat": 30.732, "lon": 104.143, "rating": 5, "desc": "看滚滚卖萌，月亮产房必去"},
        {"name": "宽窄巷子", "category": "购物美食", "hours": 2, "lat": 30.663, "lon": 104.056, "rating": 4.5, "desc": "青砖古巷，盖碗茶+川剧变脸"},
        {"name": "锦里古街", "category": "购物美食", "hours": 1.5, "lat": 30.646, "lon": 104.044, "rating": 4.4, "desc": "红灯笼夜景，成都小吃天堂"},
        {"name": "都江堰", "category": "历史文化", "hours": 3, "lat": 31.002, "lon": 103.617, "rating": 4.8, "desc": "古代水利工程，风景壮丽"},
        {"name": "人民公园鹤鸣茶社", "category": "休闲娱乐", "hours": 1.5, "lat": 30.658, "lon": 104.058, "rating": 4.2, "desc": "体验地道巴适生活，嗑瓜子掏耳朵"},
    ]
}

# 模拟美食推荐（降级用）
FOOD_TIPS = {
    "北京": ["烤鸭推荐：四季民福", "老北京炸酱面", "豆汁焦圈（慎选）", "铜锅涮肉"],
    "上海": ["小笼包（莱莱小笼）", "本帮红烧肉", "葱油拌面", "蝴蝶酥"],
    "成都": ["火锅（蜀九香）", "钵钵鸡", "蛋烘糕", "甜水面"],
}

def filter_attractions_sim(city, interests):
    """模拟数据筛选（原逻辑）"""
    attractions = CITY_ATTRACTIONS.get(city, [])
    if not interests:
        filtered = attractions
    else:
        filtered = [a for a in attractions if a["category"] in interests]
    if not filtered:
        filtered = attractions
    filtered.sort(key=lambda x: x["rating"], reverse=True)
    return filtered

# ================== 行程生成逻辑（与原一致） ==================
def generate_daily_schedule(attractions, days, pace="标准", start_date=None):
    pace_map = {"轻松": 2, "标准": 3, "紧凑": 4}
    max_per_day = pace_map.get(pace, 3)
    
    # 如果景点不足，则重复高评分景点
    total_needed = days * max_per_day
    attractions_copy = attractions.copy()
    if len(attractions_copy) < total_needed:
        extra_needed = total_needed - len(attractions_copy)
        for i in range(extra_needed):
            attractions_copy.append(attractions_copy[i % len(attractions_copy)].copy())
    
    schedule = []
    idx = 0
    for day in range(days):
        daily = []
        for _ in range(max_per_day):
            if idx < len(attractions_copy):
                daily.append(attractions_copy[idx])
                idx += 1
            else:
                daily.append({
                    "name": "自由探索 / 小红书打卡", 
                    "category": "休闲", 
                    "hours": 2, 
                    "desc": "根据兴趣发现周边小众店铺或临时决定",
                    "rating": 3.5
                })
        schedule.append(daily)
    return schedule

def format_date(base_date, offset):
    if base_date:
        return (base_date + timedelta(days=offset)).strftime("%m/%d %a")
    else:
        return f"Day {offset+1}"

# ================== Streamlit 页面配置 ==================
st.set_page_config(
    page_title="小红书旅行规划器",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 小红书风格CSS（同上，略作保留）
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
    .stButton > button:hover { background-color: #ff7b7f; }
    .css-1d391kg {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .day-title {
        font-size: 1.3rem;
        font-weight: bold;
        border-left: 5px solid #ff5a5f;
        padding-left: 12px;
        margin: 15px 0 10px 0;
    }
    .attraction-item {
        margin: 8px 0;
        padding: 8px;
        background: #fafafa;
        border-radius: 12px;
    }
    .share-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
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
</style>
""", unsafe_allow_html=True)

# ================== 侧边栏 ==================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1150/1150639.png", width=60)
    st.title("✈️ 小红书·旅行规划器")
    st.markdown("**产品定位**：为小红书年轻用户打造的一键生成高颜值旅行计划工具，结合社区打卡热点，让旅行规划像发笔记一样简单有趣。")
    st.markdown("---")
    st.markdown("### 🎯 用户需求")
    st.markdown("- 快速获取符合兴趣的行程安排\n- 景点推荐兼顾热门与小众\n- 行程可视化且便于分享")
    st.markdown("---")
    st.markdown("### 💡 亮点功能")
    st.markdown("✅ 兴趣偏好筛选（历史文化/自然/艺术等）\n✅ 智能每日行程分配\n✅ 小红书风格分享卡片\n✅ 景点地图直观展示")
    st.markdown("---")
    st.markdown("## 🗺️ 规划参数")
    city = st.selectbox("旅行目的地", options=list(CITY_ATTACTIONS.keys()), index=0)
    start_date = st.date_input("出发日期", value=datetime.today(), help="用于生成每日日期")
    days = st.slider("旅行天数", min_value=1, max_value=5, value=3)
    
    # 动态获取兴趣类别（从模拟数据或真实API均可，这里沿用模拟数据的类别集合）
    all_categories = set()
    for att in CITY_ATTACTIONS.get(city, []):
        all_categories.add(att["category"])
    interest_options = list(all_categories)
    interests = st.multiselect("你的兴趣偏好 (多选)", options=interest_options, default=interest_options[:2] if interest_options else [])
    
    pace = st.select_slider("旅行节奏", options=["轻松", "标准", "紧凑"], value="标准")
    
    st.markdown("---")
    st.markdown("💬 **产品经理笔记**")
    st.info("本工具优先调用百度地图真实POI数据（需配置AK），若失败则使用内置模拟数据。")
    
    use_real_api = st.checkbox("🌐 使用百度地图真实数据（需配置AK）", value=True)
    generate_btn = st.button("✨ 生成专属行程 ✨", use_container_width=True)

# ================== 核心逻辑：获取景点数据 ==================
if generate_btn:
    with st.spinner("正在为你规划最in路线..."):
        if use_real_api and BAIDU_AK:
            # 尝试获取真实数据
            interests_tuple = tuple(interests)
            real_attractions = fetch_attractions_by_city(city, list(interests_tuple))
            if real_attractions:
                filtered_att = real_attractions
                st.success("✅ 已使用百度地图实时景点数据")
            else:
                # 降级到模拟数据
                filtered_att = filter_attractions_sim(city, interests)
                st.warning("⚠️ 百度API无返回，已切换至内置模拟数据")
        else:
            if use_real_api and not BAIDU_AK:
                st.info("未配置百度AK，使用模拟数据。如需真实数据，请在代码中设置BAIDU_AK。")
            filtered_att = filter_attractions_sim(city, interests)
        
        # 生成行程
        schedule = generate_daily_schedule(filtered_att, days, pace, start_date)
        st.session_state.schedule = schedule
        st.session_state.city = city
        st.session_state.filtered_att = filtered_att
        st.session_state.start_date = start_date
        st.session_state.use_real = use_real_api and BAIDU_AK and real_attractions if 'real_attractions' in locals() else False

# ================== 展示行程 ==================
if "schedule" in st.session_state:
    schedule = st.session_state.schedule
    current_city = st.session_state.city
    current_start = st.session_state.start_date
    att_for_map = st.session_state.filtered_att
    used_real = st.session_state.get("use_real", False)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        if used_real:
            st.success("🌟 当前行程基于百度地图真实POI生成")
        st.markdown(f"### 📍 {current_city} · {days}天{pace}行程")
        for day_idx, day_attractions in enumerate(schedule):
            date_str = format_date(current_start, day_idx)
            with st.container():
                st.markdown(f'<div class="day-title">🌟 第{day_idx+1}天 · {date_str}</div>', unsafe_allow_html=True)
                for att in day_attractions:
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
                        st.caption(f"💡 {['早上', '上午', '下午', '傍晚'][day_idx % 4]}推荐")
                # 美食建议（降级使用模拟，可后续扩展真实美食API）
                food_list = FOOD_TIPS.get(current_city, ["当地特色小吃"])
                random_food = random.choice(food_list)
                st.markdown(f'<div style="background:#fff2e6; border-radius:12px; padding:6px 12px; margin-top:5px;">🍜 美食TIPS：{random_food}</div>', unsafe_allow_html=True)
                st.markdown("---")
    
    with col_right:
        st.markdown("### 🗺️ 行程地图速览")
        if att_for_map:
            map_df = pd.DataFrame([
                {"lat": att["lat"], "lon": att["lon"], "name": att["name"]} 
                for att in att_for_map
            ])
            st.map(map_df, use_container_width=True)
            st.caption("📍 标注为你筛选出的热门景点")
        else:
            st.info("暂无景点数据，请调整筛选条件")
        
        st.markdown("---")
        st.markdown("### 📕 小红书分享卡")
        share_title = f"✨{current_city}{days}天{pace}行程 | 跟着小红书不踩雷✨"
        share_content = f"🗓️ 行程亮点：\n"
        for idx, day in enumerate(schedule):
            share_content += f"Day{idx+1}: " + " → ".join([a["name"][:8] for a in day[:3]]) + "\n"
        share_content += f"\n🍜 地道美食：{random.choice(FOOD_TIPS.get(current_city, ['当地美食']))}\n"
        share_content += "#旅行攻略 #小众打卡地 #小红书旅行"
        
        with st.expander("📸 点击查看分享卡片", expanded=True):
            st.markdown(f"""
            <div class="share-card">
                <h4 style="margin:0;">📖 {share_title}</h4>
                <p style="font-size:0.9rem;">{share_content}</p>
                <div style="display:flex; justify-content:space-between; margin-top:10px;">
                    <span>❤️ 收藏 1.2w</span>
                    <span>💬 45</span>
                    <span>✈️ 一键复制</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📋 复制行程文案", key="copy_btn"):
                st.success("文案已复制到剪贴板（演示效果）", icon="✅")
        
        st.markdown("### 🎒 打包清单建议")
        checklist = ["身份证/护照", "充电宝+数据线", "相机/自拍杆", "舒适运动鞋", "防晒霜/雨伞"]
        st.markdown("\n".join([f"- {item}" for item in checklist]))
    
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("热门景点覆盖", f"{len(att_for_map)}个")
    with col_b:
        total_hours = sum([a['hours'] for day in schedule for a in day if 'hours' in a])
        st.metric("行程总时长", f"{total_hours:.0f}小时")
    with col_c:
        st.metric("小红书同款推荐", "⭐ 4.8")
    
    st.markdown("""
    <footer>
        🚀 产品迭代 | 数据来源：百度地图POI（需AK） + 本地模拟降级 | 符合Z世代审美与分享需求
    </footer>
    """, unsafe_allow_html=True)
else:
    st.info("👈 请在左侧选择目的地和偏好，然后点击「生成专属行程」")
