@@ -1,220 +0,0 @@
# weather/weather_fetcher.py
import requests
import json
from datetime import datetime, timedelta
import traceback # 상세 오류 로깅용

# 미리 정의된 도시별 X,Y 좌표
# 출처: 기상청 API 가이드 문서 또는 관련 좌표 파일 참고 (아래는 예시 좌표)
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

def get_kma_ultra_srt_fcst_data(service_key, city_name):
    """
    기상청 초단기 예보 API를 사용하여 특정 도시의 날씨 정보를 가져옵니다.
    미리 정의된 도시의 X,Y 좌표를 사용합니다.

    :param service_key: 기상청 API 서비스 키 (URL 인코딩되지 않은 원본 키)
    :param city_name: 날씨 정보를 조회할 도시 이름 (CITY_COORDINATES에 정의된 이름)
    :return: 날씨 정보 딕셔너리 또는 에러 메시지 문자열
    """
    if not service_key:
        return {"error": "API 서비스 키가 제공되지 않았습니다."}
    if not city_name:
        return {"error": "도시 이름이 제공되지 않았습니다."}

    coords = CITY_COORDINATES.get(city_name)
    if not coords:
        return {"error": f"'{city_name}'에 대한 미리 정의된 X,Y 좌표를 찾을 수 없습니다. 지원되는 도시: {', '.join(CITY_COORDINATES.keys())}"}

    now = datetime.now()
    
    # API 데이터 발표 주기를 고려하여 좀 더 보수적으로 base_time 설정
    # 예: 현재 시간보다 2시간 전의 정시를 기준으로 데이터를 요청하고,
    # 해당 시간의 30분 발표 자료를 가정. (API 스펙에 따라 이 시간은 조절 가능)
    base_datetime_candidate = now - timedelta(hours=2) # 2시간 전으로 설정
    base_date_str = base_datetime_candidate.strftime("%Y%m%d")
    # 기상청 초단기 예보는 보통 매시 30분에 데이터를 생성하여 40~45분 이후에 API로 제공.
    # 여기서는 'HH30' 형태로 base_time을 사용한다고 가정.
    base_time_str = base_datetime_candidate.strftime("%H30")

    endpoint = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
    params = {
        "serviceKey": service_key,
        "numOfRows": "60", # 예보 항목이 충분히 포함될 수 있도록 설정 (1시간 예보당 약 10개 항목)
        "pageNo": "1",
        "dataType": "JSON",
        "base_date": base_date_str,
        "base_time": base_time_str,
        "nx": str(coords["nx"]),
        "ny": str(coords["ny"])
    }
    
    response = None # response 변수 초기화
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        # --- 디버깅을 위한 응답 내용 출력 (필요시 주석 해제) ---
        # print(f"Request URL: {response.url}") 
        # print(f"Status Code: {response.status_code}")
        # print(f"Response Text (first 500 chars): {response.text[:500]}")
        # --- 디버깅 끝 ---
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        data = response.json()

        if data.get("response", {}).get("header", {}).get("resultCode") != "00":
            header = data.get("response", {}).get("header", {})
            error_msg = header.get("resultMsg", "API에서 오류 응답")
            result_code = header.get("resultCode", "N/A")

            if "SERVICE KEY IS NOT REGISTERED" in error_msg.upper():
                return {"error": "등록되지 않은 서비스 키입니다. 공공데이터포털에서 키 상태를 확인하세요."}
            elif result_code == "03": # NO_DATA
                 return {"error": f"데이터 없음: 기준시간({base_date_str} {base_time_str})에 해당하는 자료가 API 서버에 없습니다."}
            # 더 많은 resultCode에 대한 구체적인 처리를 추가할 수 있습니다.
            # 예: "LIMITED NUMBER OF SERVICE REQUESTS EXCEEDS" 등
            return {"error": f"API 오류 ({result_code}): {error_msg}"}

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        if not items:
            return {"error": f"수신된 예보 항목이 없습니다. (기준시간: {base_date_str} {base_time_str})"}

        weather_info = {
            "city": f"{city_name} (기준: {base_date_str} {base_time_str[:2]}:{base_time_str[2:]})",
            "temperature": "N/A", # T1H (기온)
            "humidity": "N/A",    # REH (습도)
            "sky_condition": "N/A", # SKY (하늘상태)
            "precipitation_form": "N/A", # PTY (강수형태)
            "precipitation_1h": "N/A", # RN1 (1시간 강수량)
            "wind_speed": "N/A",  # WSD (풍속)
            "forecast_time": "N/A" # 예보 시각 (가장 빠른 예보 시각)
        }
        
        # API 응답의 fcstTime은 보통 base_time 이후 1시간 간격으로 여러개가 옴 (HH00 형태)
        # 그 중 base_time 이후의 가장 이른 시간의 예보를 선택
        available_fcst_times = sorted(list(set(item.get("fcstTime") for item in items if item.get("fcstTime"))))

        if not available_fcst_times:
            return {"error": f"API 응답에 유효한 예보 시각(fcstTime) 정보가 없습니다. (기준: {base_date_str} {base_time_str})"}

        base_dt_obj = datetime.strptime(base_date_str + base_time_str, "%Y%m%d%H%M")
        target_fcst_time_found = None

        for fcst_hhmm_str in available_fcst_times: # 예: '2000', '2100' 등
            # fcst_hhmm_str을 datetime 객체로 만들기 위해 날짜 정보가 필요
            # 예보시각(fcst_hhmm_str의 시간)이 base_time의 시간보다 작으면 다음날짜일 수 있음
            current_fcst_date_obj = datetime.strptime(base_date_str, "%Y%m%d")
            if int(fcst_hhmm_str[:2]) < base_dt_obj.hour:
                current_fcst_date_obj += timedelta(days=1)
            
            fcst_dt_obj = current_fcst_date_obj.replace(hour=int(fcst_hhmm_str[:2]), minute=int(fcst_hhmm_str[2:]))

            if fcst_dt_obj > base_dt_obj: # 기준 시간 이후의 예보 중에서
                target_fcst_time_found = fcst_hhmm_str # 가장 먼저 나오는 것을 선택
                break 
        
        if not target_fcst_time_found:
            # 이 오류 메시지는 이미지 에서 보인 것과 유사
            return {"error": f"기준 시간({base_date_str} {base_time_str}) 이후의 유효한 예보 데이터를 API 응답({available_fcst_times})에서 찾을 수 없습니다."}

        weather_info["forecast_time"] = f"{target_fcst_time_found[:2]}:{target_fcst_time_found[2:]} 예보"

        sky_condition_map = {"1": "맑음", "3": "구름많음", "4": "흐림"} # SKY 코드
        pty_condition_map = { # PTY 코드
            "0": "없음", "1": "비", "2": "비/눈", "3": "눈", 
            "5": "빗방울", "6": "빗방울눈날림", "7": "눈날림"
        }

        found_data_for_target_time_at_all = False
        for item in items:
            if item.get("fcstTime") == target_fcst_time_found:
                found_data_for_target_time_at_all = True # 해당 시각 데이터가 하나라도 있으면 True
                category = item.get("category")
                fcst_val = item.get("fcstValue")

                if category == "T1H": # 기온
                    weather_info["temperature"] = f"{fcst_val}°C"
                elif category == "REH": # 습도
                    weather_info["humidity"] = f"{fcst_val}%"
                elif category == "SKY": # 하늘상태
                    weather_info["sky_condition"] = sky_condition_map.get(fcst_val, fcst_val)
                elif category == "PTY": # 강수형태
                    weather_info["precipitation_form"] = pty_condition_map.get(fcst_val, fcst_val)
                elif category == "RN1": # 1시간 강수량
                    if fcst_val == "강수없음":
                         weather_info["precipitation_1h"] = "강수없음"
                    else:
                        try:
                            # 숫자로 변환 가능한지 확인 후 mm 단위 추가 (소수점 가능성 고려)
                            val_as_float = float(fcst_val)
                            if val_as_float == 0: # API가 "0" 또는 "0.0"을 줄 수도 있음
                                weather_info["precipitation_1h"] = "0 mm" # 또는 "강수없음"
                            else:
                                weather_info["precipitation_1h"] = f"{fcst_val} mm"
                        except ValueError:
                             weather_info["precipitation_1h"] = fcst_val # 변환 실패 시 원본 값 사용 (예: "1.0mm 미만")
                elif category == "WSD": # 풍속
                    weather_info["wind_speed"] = f"{fcst_val} m/s"
        
        if not found_data_for_target_time_at_all:
             return {"error": f"{target_fcst_time_found[:2]}:{target_fcst_time_found[2:]} 시각의 세부 예보 항목을 찾을 수 없습니다."}

        return weather_info

    except requests.exceptions.Timeout:
        return {"error": "날씨 정보 요청 시간 초과"}
    except requests.exceptions.HTTPError as http_err:
        err_text = str(http_err)
        if hasattr(http_err.response, 'text') and http_err.response.text:
            err_text = http_err.response.text[:200] # 응답 앞부분만 표시
        return {"error": f"HTTP 오류 ({http_err.response.status_code if http_err.response else 'N/A'}): {err_text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"날씨 정보 요청 중 오류 발생: {e}"}
    except json.JSONDecodeError:
        error_response_text = "응답 내용 확인 불가 (response 객체 없음)"
        if response is not None and hasattr(response, 'text'):
            error_response_text = response.text[:500]
        return {"error": f"날씨 응답 데이터 파싱 오류 (JSON 형식 아님). 수신된 내용: {error_response_text}"}
    except Exception as e:
        tb_str = traceback.format_exc()
        return {"error": f"날씨 정보 처리 중 알 수 없는 오류: {str(e)}\nTraceback:\n{tb_str}"}

if __name__ == '__main__':
    # 테스트 시에는 아래 YOUR_KMA_SERVICE_KEY에 실제 발급받은 키를 넣어주세요.
    # URL 인코딩되지 않은 원본 키를 사용해야 합니다.
    TEST_KMA_API_KEY = "YOUR_KMA_SERVICE_KEY" 
    
    print("기상청 API fetcher 테스트")
    print("="*30)
    if TEST_KMA_API_KEY == "YOUR_KMA_SERVICE_KEY" or not TEST_KMA_API_KEY:
        print("weather_fetcher.py를 테스트하려면 TEST_KMA_API_KEY를")
        print("실제 기상청 API 서비스 키로 변경한 후 실행해주세요.")
    else:
        # 테스트할 도시 목록
        cities_to_test = ["서울", "부산", "없는도시"] 
        
        for test_city in cities_to_test:
            print(f"\n--- '{test_city}' 초단기 예보 정보 요청 ---")
            weather = get_kma_ultra_srt_fcst_data(TEST_KMA_API_KEY, test_city)
            Add commentMore actions
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
