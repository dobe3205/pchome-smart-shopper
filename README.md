#建立image
docker build -t myimage .   
#執行image
docker run -p 8000:8000 myimage
