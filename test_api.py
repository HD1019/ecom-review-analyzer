"""
AI电商评论分析 API 测试脚本
"""
import json
import sys

import requests

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
BASE_URL = "http://localhost:8000"
API_PATH = "/api/v1/analyze-reviews"
TOKEN = "test123"  # 与启动服务时的 MY_API_SECRET 环境变量一致

# ---------------------------------------------------------------------------
# 模拟测试数据
# ---------------------------------------------------------------------------
PAYLOAD = {
    "product_name": "SoundCore Pro 真无线蓝牙耳机",
    "reviews": [
        "降噪效果惊艳，戴上以后整个世界都安静了，低频过滤特别棒",
        "音质还行，但连接稳定性太差了，地铁上断连三五次",
        "续航真的顶，充一次电用了一星期还有余量，出差必备",
        "耳塞材质偏硬，戴超过两小时就开始胀痛，希望能改进",
        "这个价格买到这个品质，性价比没话说，已经推荐给同事了",
        "颜值在线，磨砂充电仓手感很好，送女朋友被夸了好几天",
        "通话质量一般般，对方说声音有回音，不太适合商务电话",
        "触控操作很灵敏，就是偶尔会误触，希望加个防误触模式",
        "包装很精致，还送了收纳袋和不同尺寸的耳帽，细节满分",
        "蓝牙5.3确实快，开盖秒连，延迟也很低，打游戏没问题",
    ],
    "max_reviews": 10,
}

# ---------------------------------------------------------------------------
# 测试函数
# ---------------------------------------------------------------------------

def test_health_check():
    """测试健康检查接口"""
    print("=" * 60)
    print("1. 测试健康检查 GET /")
    print("=" * 60)
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"状态码: {resp.status_code}")
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except requests.RequestException as e:
        print(f"请求失败: {e}")
    print()


def test_auth_missing():
    """测试无 Token 时的 401 响应"""
    print("=" * 60)
    print("2. 测试鉴权 —— 不携带 Token（期望 401）")
    print("=" * 60)
    try:
        resp = requests.post(
            f"{BASE_URL}{API_PATH}",
            json={"reviews": ["test"]},
            timeout=5,
        )
        print(f"状态码: {resp.status_code}")
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except requests.RequestException as e:
        print(f"请求失败: {e}")
    print()


def test_analyze_reviews():
    """测试完整的评论分析接口"""
    print("=" * 60)
    print("3. 测试评论分析 POST /api/v1/analyze-reviews")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        print(f"请求地址: {BASE_URL}{API_PATH}")
        print(f"商品名称: {PAYLOAD['product_name']}")
        print(f"评论数量: {len(PAYLOAD['reviews'])}")
        print(f"max_reviews: {PAYLOAD['max_reviews']}")
        print("-" * 40)

        resp = requests.post(
            f"{BASE_URL}{API_PATH}",
            headers=headers,
            json=PAYLOAD,
            timeout=120,  # LLM 调用可能较慢
        )

        print(f"状态码: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            analysis = data.get("analysis", {})
            print(f"分析评论数: {data.get('analyzed_count')}/{data.get('total_count')}")

            print("\n【优点】")
            for s in analysis.get("strengths", []):
                print(f"  + {s}")

            print("\n【缺点】")
            for w in analysis.get("weaknesses", []):
                print(f"  - {w}")

            print(f"\n【改进建议】")
            print(f"  {analysis.get('improvement_suggestions', 'N/A')}")

            print(f"\n【用户画像】")
            print(f"  {analysis.get('user_profile', 'N/A')}")

            sd = analysis.get("sentiment_distribution", {})
            print(f"\n【情感分布】")
            print(f"  正面: {sd.get('positive', 0):.0%}  "
                  f"负面: {sd.get('negative', 0):.0%}  "
                  f"中性: {sd.get('neutral', 0):.0%}")

            print("\n" + "-" * 40)
            print("完整 JSON 响应:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"错误响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")

    except requests.Timeout:
        print("请求超时: LLM 调用超过 120 秒")
        sys.exit(1)
    except requests.ConnectionError:
        print(f"连接失败: 请确认服务已启动在 {BASE_URL}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"请求异常: {e}")
        sys.exit(1)

    print()


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_health_check()
    test_auth_missing()
    test_analyze_reviews()
    print("=" * 60)
    print("所有测试完成")
    print("=" * 60)
