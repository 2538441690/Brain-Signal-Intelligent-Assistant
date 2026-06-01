#工具封装、注册、调用与中间件日志/异常处理
'''
关键实现：

agent_tools.py 中使用 @tool 装饰器定义工具（如 rag_summarize、fetch_external_data 等）。
'''

# 动态提示词切换（Function Calling + 多轮对话上下文管理）
'''
关键实现：

agent_tools.py 中定义工具 fill_context_for_report，调用后通过 monitor_tool 设置 runtime.context["report"] = True。
'''
import httpx
import os
from utils.logger_handler import logger
from langchain_core.tools import tool

from rag.rag_service import RagSummarizeService
import random
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
from dotenv import load_dotenv

load_dotenv()

AMAP_KEY = os.getenv("AMAP_WEBSERVICE_KEY")
if not AMAP_KEY:
    logger.warning("未设置高德地图 API Key，地图工具将不可用")

rag = RagSummarizeService()

user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010",]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
             "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12", ]

external_data = {}

@tool(description="搜索高德地图上的兴趣点（POI），例如餐厅、酒店、景点等。参数：keyword（搜索关键词，必填），city（城市名，可选）。返回地点列表。")
def amap_poi_search(keyword: str, city: str = "") -> str:
    """高德地图 POI 搜索"""
    if not AMAP_KEY:
        return "高德地图服务未配置 API Key，无法使用。"
    url = "https://restapi.amap.com/v5/place/text"
    params = {
        "key": AMAP_KEY,
        "keywords": keyword,
        "region": city,
        "city_limit": True,
        "page": 1,
        "offset": 10
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "1":
                pois = data.get("pois", [])
                if not pois:
                    return f"未找到与 '{keyword}' 相关的地点。"
                results = []
                for i, poi in enumerate(pois[:10], 1):
                    name = poi.get("name", "未知")
                    address = poi.get("address", "无地址")
                    results.append(f"{i}. {name}\n   地址: {address}")
                return "\n\n".join(results)
            else:
                return f"搜索失败: {data.get('info', '未知错误')}"
    except Exception as e:
        logger.error(f"高德 POI 搜索异常: {e}")
        return f"搜索出错: {e}"

@tool(description="规划步行路线。参数：origin（起点，格式'经度,纬度'），destination（终点，格式'经度,纬度'）。返回路线距离和预估时间。")
def amap_walking_route(origin: str, destination: str) -> str:
    """高德步行路线规划"""
    if not AMAP_KEY:
        return "高德地图服务未配置 API Key。"
    url = "https://restapi.amap.com/v3/direction/walking"
    params = {
        "key": AMAP_KEY,
        "origin": origin,
        "destination": destination
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "1":
                path = data.get("route", {}).get("paths", [])[0]
                distance = float(path.get("distance", 0)) / 1000
                duration = int(path.get("duration", 0)) // 60
                return f"步行路线规划成功：距离约 {distance:.2f} 公里，预计用时 {duration} 分钟。"
            else:
                return f"规划失败: {data.get('info', '未知错误')}"
    except Exception as e:
        logger.error(f"高德步行路线规划异常: {e}")
        return f"规划出错: {e}"

@tool(description="规划驾车路线。参数：origin, destination，可选 waypoints（途经点，多个用;分隔）。返回距离、时间、过路费等信息。")
def amap_driving_route(origin: str, destination: str, waypoints: str = "") -> str:
    if not AMAP_KEY:
        return "高德地图服务未配置 API Key。"
    url = "https://restapi.amap.com/v3/direction/driving"
    params = {
        "key": AMAP_KEY,
        "origin": origin,
        "destination": destination,
        "strategy": 10,
        "extensions": "base"
    }
    if waypoints:
        params["waypoints"] = waypoints
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "1":
                path = data.get("route", {}).get("paths", [])[0]
                distance = float(path.get("distance", 0)) / 1000
                duration = int(path.get("duration", 0)) // 60
                tolls = path.get("tolls", 0)
                return f"驾车路线：距离 {distance:.2f} 公里，预计 {duration} 分钟，过路费 {tolls} 元。"
            else:
                return f"规划失败: {data.get('info', '未知错误')}"
    except Exception as e:
        return f"出错: {e}"

#RAG向量总结服务
@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)

# #天气工具
# @tool(description="获取指定城市的天气，以消息字符串的形式返回")
# def get_weather(city: str) -> str:
#     return f"城市{city}天气为晴天，气温26摄氏度，空气湿度50%，南风1级，AQI21，最近6小时降雨概率极低"

# #用户定位
# @tool(description="获取用户所在城市的名称，以纯字符串形式返回")
# def get_user_location() -> str:
#     return random.choice(["深圳", "合肥", "杭州"])


@tool(description="获取被试的ID，以纯字符串形式返回")
def get_subject_id() -> str:
    return random.choice(user_ids)


@tool(description="获取当前月份，以纯字符串形式返回")
def get_current_month() -> str:
    return random.choice(month_arr)

@tool(description="获取指定被试、指定实验范式的脑电信号解码准确率，返回百分比")
def get_decoding_accuracy(subject_id: str, paradigm: str) -> str:
    # 从数据库或API查询真实准确率
    return f"被试{subject_id}在{paradigm}任务中解码准确率为87.5%"

@tool(description="获取当前脑电采集设备的信号质量指标（阻抗、采样率、工频干扰等）")
def get_signal_quality() -> str:
    return "信号质量良好：平均阻抗5kΩ，采样率1000Hz，工频干扰抑制成功"

@tool(description="查询脑信号解码模型中可用的特征提取算法列表")
def list_available_features() -> str:
    return "CSP, FBCSP, Riemannian Geometry, Deep ConvNet, EEGNet"

@tool(description="运行在线脑信号解码（模拟或真实），返回解码类别及置信度")
def run_realtime_decoding() -> str:
    # 调用后端解码服务
    return "解码结果：想象右手运动，置信度0.92"


def generate_external_data():
    """
    {
        "user_id": {
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            ...
        },
        "user_id": {
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            ...
        },
        "user_id": {
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            "month" : {"特征": xxx, "效率": xxx, ...}
            ...
        },
        ...
    }
    :return:
    """
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")
        #取csv文件
        with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                arr: list[str] = line.strip().split(",")

                user_id: str = arr[0].replace('"', "")
                feature: str = arr[1].replace('"', "")
                efficiency: str = arr[2].replace('"', "")
                consumables: str = arr[3].replace('"', "")
                comparison: str = arr[4].replace('"', "")
                time: str = arr[5].replace('"', "")

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "特征": feature,
                    "效率": efficiency,
                    "耗材": consumables,
                    "对比": comparison,
                }

#从外部数据csv文件中抽取
@tool(description="从外部系统中获取指定用户在指定月份的使用记录，以纯字符串形式返回， 如果未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"[fetch_external_data]未能检索到用户：{user_id}在{month}的使用记录数据")
        return ""


# if __name__ =='__main__':
#    print(fetch_external_data("1001","2025-01"))

@tool(description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"