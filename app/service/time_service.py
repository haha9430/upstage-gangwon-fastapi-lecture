import requests
import json

class TimeService:
    def __init__(self):
        pass

    def get_current_time(self, timezone: str) -> str:
        url = f"https://worldtimeapi.org/api/timezone/{timezone}"
        #url = f"https://timeapi.io/api/Time/current/zone?timeZone={timezone}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            resp= requests.get(url, headers=headers, timeout=5)

            resp.raise_for_status()

            response = resp.json()

            timezone = response["timezone"]
            datetime = response["datetime"]
            utc_offset = response["utc_offset"]

            #timezone = response["timeZone"]
            #datetime = response["dateTime"]

            print(f"Timezone: {timezone}, datetime: {datetime}")

            return json.dumps({"timezone": timezone, "datetime": datetime, "utc_offset": utc_offset})
            #return json.dumps({"timezone": timezone, "datetime": datetime})

        except requests.exceptions.HTTPError:
            return json.dumps({"error": f"Timezone '{timezone}' not found."})

        except Exception as e:
            # 그 외 모든 에러 (연결 실패 등) 처리
            return json.dumps({"error": f"Failed to fetch time: {str(e)}"})