import json
from io import BytesIO
from PIL import Image
import os

import boto3
from botocore import UNSIGNED #contact public s3 buckets anonymously
from botocore.client import Config #contact public s3 buckets anonymously

import streamlit as st

from resnet_model import Resnet_Model

@st.cache()
def load_model(path='../models/trained_model_resnet50.pt', device='cpu'):
    """Retrieves the trained model and maps it to the CPU by default, can also specify GPU here."""
    model = Resnet_Model(path_to_pretrained_model=path, map_location=device)
    return model

@st.cache()
def load_index_to_label_dict(path='index_to_class_label.json'):
    """Retrieves and formats the index to class label lookup dictionary needed to 
    make sense of the predictions. When loaded in, the keys are strings, this also
    processes those keys to integers."""
    with open(path, 'r') as f:
        index_to_class_label_dict = json.load(f)
    index_to_class_label_dict = {int(k): v for k, v in index_to_class_label_dict.items()}
    return index_to_class_label_dict

@st.cache()
def load_file_from_s3(key, bucket_name='bird-classification-bucket'):
    """Retrieves files anonymously from my public S3 bucket"""
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    s3_file_raw = s3.get_object(Bucket=bucket_name, Key=key)
    s3_file = s3_file_raw['Body'].read()
    return s3_file

@st.cache()
def load_all_image_files(path='all_image_files.json'):
    """Retrieves JSON document outining the S3 file structure"""
    with open(path, 'r') as f:
        return json.load(f)

@st.cache()
def load_list_of_images_available(all_image_files, image_files_dtype, bird_species):
    """Retrieves list of available images given the current selections"""
    species_dict = all_image_files.get(image_files_dtype)
    list_of_files = species_dict.get(bird_species)
    return list_of_files

@st.cache()
def predict(img, index_to_label_dict, model):
    """Transforming input image according to ImageNet paper
    The Resnet was initially trained on ImageNet dataset
    and because of the use of transfer learning, I froze all
    weights and only learned weights on the final layer.
    The weights of the first layer are still what was
    used in the ImageNet paper and we need to process
    the new images just like they did.
    
    This function transforms the image accordingly,
    puts it to the necessary device (cpu by default here),
    feeds the image through the model getting the output tensor,
    converts that output tensor to probabilities using Softmax,
    and then extracts and formats the top 3 predictions."""
    formatted_predictions = model.predict_proba(img, 3, index_to_label_dict)
    return formatted_predictions

if __name__ == '__main__':
    model = load_model()
    index_to_class_label_dict = load_index_to_label_dict()
    all_image_files = load_all_image_files()
    types_of_birds = sorted(list(all_image_files['test'].keys()))

    st.title('Welcome To Project Eagle Vision!')

    file = st.file_uploader('Upload An Image')
    dtype_file_structure_mapping = {
        'All Images': 'consolidated', 'Images Used To Train The Model': 'train', 
        'Images Used To Tune The Model': 'valid', 'Images The Model Has Never Seen': 'test'
        }

    if not file:
        dataset_type = st.sidebar.selectbox("Data Portion Type", list(dtype_file_structure_mapping.keys()))
        image_files_dtype = dtype_file_structure_mapping[dataset_type]

        bird_species = st.sidebar.selectbox("Bird Type", types_of_birds)
        available_images = load_list_of_images_available(all_image_files, image_files_dtype, bird_species)
        image_name = st.sidebar.selectbox("Image Name", available_images)
        if image_files_dtype == 'consolidated':
            s3_key_prefix = 'consolidated/consolidated'
        else:
            s3_key_prefix = image_files_dtype
        key_path = os.path.join(s3_key_prefix, bird_species, image_name)
        s3_file = load_file_from_s3(key=key_path)
        
        img = Image.open(BytesIO(s3_file))

    else:
        img = Image.open(file)

    prediction = predict(img, index_to_class_label_dict, model)
    st.image(img)
    for idx, p in enumerate(prediction, start=1):
        st.write(f"Top {idx} prediction: {p[0]}, Confidence level: {p[1]}")