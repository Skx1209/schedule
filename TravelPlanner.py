import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# 设置页面配置
st.set_page_config(
    page_title="小红书旅行规划器",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义小红书风格CSS
st.markdown("""
<style>
    /* 小红书主色调：红、粉、白 */
    .main {
        background-color: #fef9f9;
    }
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
    h1, h2, h3 {
        color: #333333;
    }
    .card {
        background-color: white;
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #f0e6e6;
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

# ================== 产品经理设计说明（侧边栏说明） ==================
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

# ================== 模拟城市景点数据库（小红书风格热门数据） ==================
# 每个景点包含：名称、类别、游玩时长(h)、纬度、经度、评分、简短描述
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

# 美食补充建议（按城市简单示例）
FOOD_TIPS = {
    "北京": ["烤鸭推荐：四季民福", "老北京炸酱面", "豆汁焦圈（慎选）", "铜锅涮肉"],
    "上海": ["小笼包（莱莱小笼）", "本帮红烧肉", "葱油拌面", "蝴蝶酥"],
    "成都": ["火锅（蜀九香）", "钵钵鸡", "蛋烘糕", "甜水面"],
}

# ================== 辅助函数 ==================
def filter_attractions(city, interests):
    """根据兴趣筛选景点，返回景点列表（按评分排序）"""
    attractions = CITY_ATTRACTIONS.get(city, [])
    if not interests:  # 未选兴趣则全部返回
        filtered = attractions
    else:
        filtered = [a for a in attractions if a["category"] in interests]
    # 如果筛选后为空，则返回全部景点
    if not filtered:
        filtered = attractions
    # 按评分排序
    filtered.sort(key=lambda x: x["rating"], reverse=True)
    return filtered

def generate_daily_schedule(attractions, days, pace="标准", start_date=None):
    """
    生成每日行程
    pace: "轻松" -> 每天2-3个景点, "标准"->3个, "紧凑"->4个
    返回每日行程列表，每个元素为list of attractions
    """
    if not attractions:
        return [[] for _ in range(days)]
    
    pace_map = {"轻松": 2, "标准": 3, "紧凑": 4}
    max_per_day = pace_map.get(pace, 3)
    
    # 确保有足够的景点，如果不足则重复或填充自由活动占位
    total_needed = days * max_per_day
    if len(attractions) < total_needed:
        # 重复高评分景点（模拟备选）
        extra_needed = total_needed - len(attractions)
        for i in range(extra_needed):
            attractions.append(attractions[i % len(attractions)].copy())
    
    # 打乱顺序避免每次都一样？为了稳定，按评分排序后顺序分配
    # 但是同一景点出现在多天，为了体验，允许但会标注
    schedule = []
    idx = 0
    for day in range(days):
        daily_attractions = []
        for _ in range(max_per_day):
            if idx < len(attractions):
                daily_attractions.append(attractions[idx])
                idx += 1
            else:
                # 如果不够，添加自由活动提示
                daily_attractions.append({
                    "name": "自由探索 / 小红书打卡", 
                    "category": "休闲", 
                    "hours": 2, 
                    "desc": "根据兴趣发现周边小众店铺或临时决定",
                    "rating": 3.5
                })
        schedule.append(daily_attractions)
    return schedule

def format_date(base_date, offset):
    """返回格式化的日期字符串"""
    if base_date:
        return (base_date + timedelta(days=offset)).strftime("%m/%d %a")
    else:
        return f"Day {offset+1}"

# ================== 主界面布局 ==================
st.title("✈️ 你的专属旅行计划书")
st.caption("根据偏好智能生成行程 | 一键生成小红书风格分享卡")

# 侧边栏参数配置
with st.sidebar:
    st.markdown("## 🗺️ 规划参数")
    city = st.selectbox("旅行目的地", options=list(CITY_ATTRACTIONS.keys()), index=0)
    start_date = st.date_input("出发日期", value=datetime.today(), help="用于生成每日日期")
    days = st.slider("旅行天数", min_value=1, max_value=5, value=3, help="1-5天短途游最佳")
    
    # 兴趣多选
    all_categories = set()
    for att in CITY_ATTRACTIONS.get(city, []):
        all_categories.add(att["category"])
    interest_options = list(all_categories)
    interests = st.multiselect("你的兴趣偏好 (多选)", options=interest_options, default=interest_options[:2] if interest_options else [])
    
    pace = st.select_slider("旅行节奏", options=["轻松", "标准", "紧凑"], value="标准", help="轻松: 每天2-3个点；紧凑: 4个点")
    
    st.markdown("---")
    st.markdown("💬 **产品经理笔记**")
    st.info("本demo展示核心规划逻辑 + 小红书风格UI，支持兴趣筛选、日程分配与视觉分享，实际可接入地图/天气API扩充。")
    
    generate_btn = st.button("✨ 生成专属行程 ✨", use_container_width=True)

# 初始化或生成行程
if "schedule" not in st.session_state or generate_btn:
    with st.spinner("正在为你规划最in路线..."):
        # 筛选景点
        filtered_att = filter_attractions(city, interests)
        # 生成每日行程
        schedule = generate_daily_schedule(filtered_att, days, pace, start_date)
        st.session_state.schedule = schedule
        st.session_state.city = city
        st.session_state.filtered_att = filtered_att
        st.session_state.start_date = start_date

# 显示行程
if "schedule" in st.session_state:
    schedule = st.session_state.schedule
    current_city = st.session_state.city
    current_start = st.session_state.start_date
    att_for_map = st.session_state.filtered_att
    
    # 主区域两列布局: 左:行程详情 右:地图与分享
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown(f"### 📍 {current_city} · {days}天{pace}行程")
        # 展示每日行程卡片
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
                # 每日美食小贴士
                food_list = FOOD_TIPS.get(current_city, ["当地特色小吃"])
                random_food = random.choice(food_list)
                st.markdown(f'<div style="background:#fff2e6; border-radius:12px; padding:6px 12px; margin-top:5px;">🍜 美食TIPS：{random_food}</div>', unsafe_allow_html=True)
                st.markdown("---")
    
    with col_right:
        st.markdown("### 🗺️ 行程地图速览")
        # 展示地图 (所有推荐景点位置)
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
        # 生成小红书风格的分享文案
        share_title = f"✨{current_city}{days}天{pace}旅行计划 | 跟着小红书不踩雷✨"
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
        
        # 附加旅行清单
        st.markdown("### 🎒 打包清单建议")
        checklist = ["身份证/护照", "充电宝+数据线", "相机/自拍杆", "舒适运动鞋", "防晒霜/雨伞"]
        st.markdown("\n".join([f"- {item}" for item in checklist]))
    
    # 底部信息：产品迭代思路
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("热门景点覆盖", f"{len(att_for_map)}个")
    with col_b:
        st.metric("行程总时长", f"{sum([a['hours'] for day in schedule for a in day if 'hours' in a]):.0f}小时")
    with col_c:
        st.metric("小红书同款推荐", "⭐ 4.8")
    
    st.markdown("""
    <footer>
        🚀 产品经理Demo | 数据模拟展示，实际可接入真实POI、天气、交通API | 设计符合Z世代审美与分享需求
    </footer>
    """, unsafe_allow_html=True)
else:
    st.info("👈 请在左侧选择目的地和偏好，然后点击「生成专属行程」")
