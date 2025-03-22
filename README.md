# 註冊API Key
- 請至 https://aistudio.google.com/apikey 註冊gemini API Key
- 請至 https://developers.google.com/custom-search/v1/overview?hl=zh-tw 註冊Google Search API
- 請至 https://programmablesearchengine.google.com/controlpanel/overview?cx=e7c473574b00d4f11&hl=zh-tw 註冊Google CSE ID
- 完成後請至.env設定API Key 以及 LLM Name
# 建立image
docker build -t ragimage .   
# 執行image
docker run -p 8000:8000 ragimage
# 使用網站
開啟瀏覽器至http://localhost:8000/