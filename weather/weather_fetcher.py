# weather/weather_fetcher.py
import requests
import json
from datetime import datetime, timedelta
import traceback # 상세 오류 로깅용
import os # os 모듈 추가

# ✅ 기상청 API 키 설정
KMA_API_KEY = os.getenv("KMA_API_KEY")
if not KMA_API_KEY:
    # 이 부분은 애플리케이션의 전체적인 오류 처리 방식에 따라
    # print 문으로 대체하거나 로깅 처리, 또는 None을 반환 후 호출부에서 처리할 수도 있습니다.
    # 여기서는 Gemini API 키 처리 방식과 유사하게 ValueError를 발생시키겠습니다.
    # 다만, 이 모듈이 직접 실행될 때 (if __name__ == '__main__':)를 고려하여
    # 프로그램 시작 시점에 키가 없어도 바로 종료되지 않도록 함수 내에서 키 유무를 한 번 더 확인하거나,
    # 테스트 코드에서 별도로 안내할 수 있습니다.
    # 여기서는 함수 호출 시점에서 키가 있는지 확인하는 것으로 변경합니다.
    pass # 시작 시점에 바로 오류를 발생시키지 않도록 수정


# 미리 정의된 도시별 X,Y 좌표
CITY_COORDINATES = {
    "서울": {"nx": 60, "ny": 127},
    "부산": {"nx": 98, "ny": 76},
    "대구": {"nx": 89, "ny": 90},
    "인천": {"nx": 55, "ny": 124},
    "광주": {"nx": 58, "ny": 74},
    "대전": {"nx": 67, "ny": 100},
    "울산": {"nx": 102, "ny": 84},
    "수원": {"nx": 60, "ny": 121},
    "제주": {"nx": 52, "ny": 38},
    # 필요에 따라 다른 도시 추가
}

# def get_kma_ultra_srt_fcst_data(service_key, city_name): # 기존 함수 정의
def get_kma_ultra_srt_fcst_data(city_name): # 수정된 함수 정의 (service_key 매개변수 제거)
    """
    기상청 초단기 예보 API를 사용하여 특정 도시의 날씨 정보를 가져옵니다.
    미리 정의된 도시의 X,Y 좌표를 사용하며, KMA_API_KEY 환경 변수에서 API 키를 읽어옵니다.

    :param city_name: 날씨 정보를 조회할 도시 이름 (CITY_COORDINATES에 정의된 이름)
    :return: 날씨 정보 딕셔너리 또는 에러 메시지 딕셔너리
    """
    # 함수 내에서 환경 변수에서 API 키를 다시 로드하고 확인
    current_kma_api_key = os.getenv("KMA_API_KEY")
    if not current_kma_api_key:
        return {"error": "KMA_API_KEY 환경변수가 설정되지 않았습니다. 확인 후 다시 시도해주세요."}
    if not city_name:
        return {"error": "도시 이름이 제공되지 않았습니다."}

    coords = CITY_COORDINATES.get(city_name)
    if not coords:
        return {"error": f"'{city_name}'에 대한 미리 정의된 X,Y 좌표를 찾을 수 없습니다. 지원되는 도시: {', '.join(CITY_COORDINATES.keys())}"}

    now = datetime.now()
    base_datetime_candidate = now - timedelta(hours=2)
    base_date_str = base_datetime_candidate.strftime("%Y%m%d")
    base_time_str = base_datetime_candidate.strftime("%H30")

    endpoint = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
    params = {
        "serviceKey": current_kma_api_key, # 환경 변수에서 읽은 키 사용
        "numOfRows": "60",
        "pageNo": "1",
        "dataType": "JSON",
        "base_date": base_date_str,
        "base_time": base_time_str,
        "nx": str(coords["nx"]),
        "ny": str(coords["ny"])
    }

    response = None
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("response", {}).get("header", {}).get("resultCode") != "00":
            header = data.get("response", {}).get("header", {})
            error_msg = header.get("resultMsg", "API에서 오류 응답")
            result_code = header.get("resultCode", "N/A")

            if "SERVICE KEY IS NOT REGISTERED" in error_msg.upper() or result_code == "10": # SERVICE_KEY_IS_NOT_REGISTERED_ERROR
                return {"error": "등록되지 않은 서비스 키이거나 서비스 키가 올바르지 않습니다. KMA_API_KEY 환경변수를 확인하세요."}
            elif result_code == "03": # NO_DATA
                 return {"error": f"데이터 없음: 기준시간({base_date_str} {base_time_str})에 해당하는 자료가 API 서버에 없습니다."}
            return {"error": f"API 오류 ({result_code}): {error_msg}"}

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

        if not items:
            return {"error": f"수신된 예보 항목이 없습니다. (기준시간: {base_date_str} {base_time_str})"}

        weather_info = {
            "city": f"{city_name} (기준: {base_date_str} {base_time_str[:2]}:{base_time_str[2:]})",
            "temperature": "N/A",
            "humidity": "N/A",
            "sky_condition": "N/A",
            "precipitation_form": "N/A",
            "precipitation_1h": "N/A",
            "wind_speed": "N/A",
            "forecast_time": "N/A"
        }

        available_fcst_times = sorted(list(set(item.get("fcstTime") for item in items if item.get("fcstTime"))))

        if not available_fcst_times:
            return {"error": f"API 응답에 유효한 예보 시각(fcstTime) 정보가 없습니다. (기준: {base_date_str} {base_time_str})"}

        base_dt_obj = datetime.strptime(base_date_str + base_time_str, "%Y%m%d%H%M")
        target_fcst_time_found = None

        for fcst_hhmm_str in available_fcst_times:
            current_fcst_date_obj = datetime.strptime(base_date_str, "%Y%m%d")
            if int(fcst_hhmm_str[:2]) < base_dt_obj.hour:
                current_fcst_date_obj += timedelta(days=1)
            fcst_dt_obj = current_fcst_date_obj.replace(hour=int(fcst_hhmm_str[:2]), minute=int(fcst_hhmm_str[2:]))
            if fcst_dt_obj > base_dt_obj:
                target_fcst_time_found = fcst_hhmm_str
                break

        if not target_fcst_time_found:
            return {"error": f"기준 시간({base_date_str} {base_time_str}) 이후의 유효한 예보 데이터를 API 응답({available_fcst_times})에서 찾을 수 없습니다."}

        weather_info["forecast_time"] = f"{target_fcst_time_found[:2]}:{target_fcst_time_found[2:]} 예보"
        sky_condition_map = {"1": "맑음", "3": "구름많음", "4": "흐림"}
        pty_condition_map = {"0": "없음", "1": "비", "2": "비/눈", "3": "눈", "5": "빗방울", "6": "빗방울눈날림", "7": "눈날림"}

        found_data_for_target_time_at_all = False
        for item in items:
            if item.get("fcstTime") == target_fcst_time_found:
                found_data_for_target_time_at_all = True
                category = item.get("category")
                fcst_val = item.get("fcstValue")
                if category == "T1H": weather_info["temperature"] = f"{fcst_val}°C"
                elif category == "REH": weather_info["humidity"] = f"{fcst_val}%"
                elif category == "SKY": weather_info["sky_condition"] = sky_condition_map.get(fcst_val, fcst_val)
                elif category == "PTY": weather_info["precipitation_form"] = pty_condition_map.get(fcst_val, fcst_val)
                elif category == "RN1":
                    if fcst_val == "강수없음": weather_info["precipitation_1h"] = "강수없음"
                    else:
                        try:
                            val_as_float = float(fcst_val)
                            weather_info["precipitation_1h"] = f"{fcst_val} mm" if val_as_float != 0 else "0 mm"
                        except ValueError: weather_info["precipitation_1h"] = fcst_val
                elif category == "WSD": weather_info["wind_speed"] = f"{fcst_val} m/s"

        if not found_data_for_target_time_at_all:
             return {"error": f"{target_fcst_time_found[:2]}:{target_fcst_time_found[2:]} 시각의 세부 예보 항목을 찾을 수 없습니다."}

        return weather_info

    except requests.exceptions.Timeout:
        return {"error": "날씨 정보 요청 시간 초과"}
    except requests.exceptions.HTTPError as http_err:
        err_text = str(http_err)
        if hasattr(http_err.response, 'text') and http_err.response.text: err_text = http_err.response.text[:200]
        return {"error": f"HTTP 오류 ({http_err.response.status_code if http_err.response else 'N/A'}): {err_text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"날씨 정보 요청 중 오류 발생: {e}"}
    except json.JSONDecodeError:
        error_response_text = "응답 내용 확인 불가 (response 객체 없음)"
        if response is not None and hasattr(response, 'text'): error_response_text = response.text[:500]
        return {"error": f"날씨 응답 데이터 파싱 오류 (JSON 형식 아님). 수신된 내용: {error_response_text}"}
    except Exception as e:
        tb_str = traceback.format_exc()
        return {"error": f"날씨 정보 처리 중 알 수 없는 오류: {str(e)}\nTraceback:\n{tb_str}"}

if __name__ == '__main__':
    print("기상청 API fetcher 테스트")
    print("="*30)

    # 테스트 전에 KMA_API_KEY 환경 변수가 설정되었는지 확인
    kma_key_for_test = os.getenv("KMA_API_KEY")
    if not kma_key_for_test:
        print("🛑 테스트를 진행하려면 KMA_API_KEY 환경 변수를 설정해주세요.")
        print("   예: export KMA_API_KEY=\"YOUR_KMA_SERVICE_KEY\" (Linux/macOS)")
        print("   예: set KMA_API_KEY=YOUR_KMA_SERVICE_KEY (Windows CMD)")
    else:
        cities_to_test = ["서울", "부산", "없는도시"]
        for test_city in cities_to_test:
            print(f"\n--- '{test_city}' 초단기 예보 정보 요청 ---")
            # get_kma_ultra_srt_fcst_data 함수 호출 시 더 이상 API 키를 전달하지 않음
            weather = get_kma_ultra_srt_fcst_data(test_city)
            if "error" in weather:
                print(f"오류 발생: {weather['error']}")
            else:
                print(f"도시: {weather.get('city', test_city)}")
                print(f"예보 시각: {weather.get('forecast_time', 'N/A')}")
                print(f"  하늘 상태: {weather.get('sky_condition', 'N/A')}")
                print(f"  강수 형태: {weather.get('precipitation_form', 'N/A')}")
                print(f"  기온: {weather.get('temperature', 'N/A')}")
                print(f"  습도: {weather.get('humidity', 'N/A')}")
                print(f"  1시간 강수량: {weather.get('precipitation_1h', 'N/A')}")
                print(f"  풍속: {weather.get('wind_speed', 'N/A')}")