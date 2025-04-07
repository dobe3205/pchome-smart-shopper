# 環境版本
FROM python:3.12.7

# docker工作路徑
WORKDIR /code

# 需求檔案
COPY requirements.txt /code/
COPY ./app /code/app
COPY ./package /code/package

ENV PYTHONPATH=/code
# 安裝套件指令
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 8000
# 執行
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]