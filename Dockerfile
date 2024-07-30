FROM python:3.9

RUN apt -qq update && apt -qq install -y git wget ffmpeg

RUN pip install pyrogram
RUN pip install pytgcalls
RUN pip install ffmpeg-python
 
COPY . . 

RUN pip3 install -r requirements.txt 

CMD ["python3","main.py"]
