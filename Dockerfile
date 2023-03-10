FROM python:3.8

COPY . /app

WORKDIR /app

#Install necessary packages from requirements.txt with no cache dir allowing for installation on machine with very little memory on board
RUN pip --no-cache-dir install -r requirements.txt
rm -rf mmdetection
git clone https://github.com/open-mmlab/mmdetection.git
%cd mmdetection
pip install -e .

pip install Pillow==7.0.0
pip install -U openmim
mim install mmcv-full

#Exposing the default streamlit port
EXPOSE 8501

#Running the streamlit app
ENTRYPOINT ["streamlit", "run", "--server.maxUploadSize=5"]
CMD ["src/Project Eagle Vision.py"]
