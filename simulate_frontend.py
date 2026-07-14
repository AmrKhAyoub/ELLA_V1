import time

import requests

URL = "http://127.0.0.1:8000/api/update-location/"

# تحديد الإحداثيات
# L1: الكرملين، موسكو
L1 = {"latitude": 55.751667, "longitude": 37.617778}
# L2: مكان مختلف (برج إيفل، باريس)
L2 = {"latitude": 48.858844, "longitude": 2.294350}
# L3: نفس L2 تماماً (لم يتغير الموقع)
L3 = {"latitude": 48.858844, "longitude": 2.294350}
# L4: مكان مختلف (الكولوسيوم، روما)
L4 = {"latitude": 41.890251, "longitude": 12.492373}
# L5: مكان مختلف (الكولوسيوم، روما)
L5 = {"latitude": None, "longitude": None}

locations = [L1, L2, L3, L4, L5]

print("Starting simulation...\n")

for index, loc in enumerate(locations):
    print(f"[{time.strftime('%X')}] Sending L{index + 1} -> {loc}...")

    # إرسال الطلب للباك إند
    response = requests.post(URL, json=loc)
    print(f"Backend Response: {response.status_code} - {response.json()}")

    # الانتظار لمدة 60 ثانية قبل إرسال الموقع التالي (ما عدا الطلب الأخير)
    if index < len(locations) - 1:
        print("Waiting for 30 seconds before next update...\n")
        time.sleep(30)

print("\nSimulation Finished!")
