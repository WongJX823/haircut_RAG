"""
Streamlit web app — entry point.
Run: streamlit run app/main.py
"""

import os
import tempfile
import streamlit as st
from dotenv import load_dotenv
from vision.feature_extractor import extract_features
from rag.recommender import recommend

load_dotenv()

st.set_page_config(page_title="HaircutAI", page_icon="✂️", layout="centered")
st.title("✂️ HaircutAI — Personalised Haircut Recommender")
st.caption("Upload a clear front-facing photo to get a haircut recommendation based on your face shape and hair type.")

uploaded = st.file_uploader("Upload your photo", type=["jpg", "jpeg", "png"])

if uploaded:
    st.image(uploaded, caption="Your photo", width=300)

    if st.button("Analyse & Recommend"):
        with st.spinner("Analysing your face features..."):
            suffix = os.path.splitext(uploaded.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            try:
                features = extract_features(tmp_path)
            finally:
                os.unlink(tmp_path)

        st.subheader("Detected Features")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Face Shape", features.face_shape)
        col2.metric("Hair Type", features.hair_type)
        col3.metric("Hair Texture", features.hair_texture)
        col4.metric("Gender", features.gender)

        with st.spinner("Retrieving haircut knowledge and generating recommendation..."):
            result = recommend(features)

        st.subheader("Your Personalised Recommendation")
        st.write(result["recommendation"])

        with st.expander("Knowledge retrieved from database"):
            for i, chunk in enumerate(result["retrieved_context"], 1):
                st.markdown(f"**Chunk {i}:**")
                st.text(chunk)
