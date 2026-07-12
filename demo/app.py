import streamlit as st
import json

st.title("Video Captioning Agent — Track 2 Demo")
st.caption("AMD Hackathon Act II — reads pre-generated results.json from the Docker pipeline")

with open("results.json") as f:
    results = json.load(f)

task_ids = [r["task_id"] for r in results]
selected = st.selectbox("Select a clip", task_ids)

result = next(r for r in results if r["task_id"] == selected)
for style, caption in result["captions"].items():
    st.subheader(style.replace("_", " ").title())
    st.write(caption)
