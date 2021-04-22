import datetime
import re
import requests

# See: How to create tzinfo when I have UTC offset? https://stackoverflow.com/a/28270767
from dateutil import tz

# TODO: Implement inserts in DB, see: https://hakibenita.com/fast-load-data-python-postgresql

now = datetime.datetime.now(tz=tz.tzlocal()).strftime("%Y-%m-%d %H:%M:%S.%f%z")

url = "http://localhost:8000/hol_caracola"
get_request = requests.request("GET", url)
regex_compiled = re.compile("hola", re.MULTILINE)
regex_match = regex_compiled.search(get_request.text) != None

print(
    f"""time={now} web_url={url} http_status={get_request.status_code} resp_time={get_request.elapsed.total_seconds()} regex_match={regex_match}\n{get_request.text}"""
)
