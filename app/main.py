"""
Presentation layer — Streamlit UI only.
No business logic here. All processing goes through services/pipeline.py.
Run: python -m streamlit run app/main.py
"""

import streamlit as st
from dotenv import load_dotenv
from services.validator import validate_api_key
from services.pipeline import run_pipeline
from services.feedback import save_feedback
from services.style_images import find_style_images

load_dotenv()

st.set_page_config(page_title="HaircutAI", page_icon="✂️", layout="centered")
st.title("✂️ HaircutAI — Personalised Haircut Recommender")
st.caption("Get a personalised haircut recommendation based on your face shape and hair type.")

# Validate API key on startup
api_check = validate_api_key()
if not api_check.valid:
    st.error(f"⚠️ Configuration Error: {api_check.error}")
    st.stop()

# ── INPUTS ────────────────────────────────────────────────────────────────────
st.subheader("Provide Your Details")
st.caption("Fill in any combination below — a photo, a video, a written description, or several at once. We'll combine whatever you give us.")

result = None

image_uploaded = st.file_uploader(
    "📷 Upload a clear front-facing photo",
    type=["jpg", "jpeg", "png", "webp"],
    help="Max 5MB. Front-facing photo works best.",
)
if image_uploaded:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image_uploaded, caption="Your photo", width="stretch")

video_uploaded = st.file_uploader(
    "🎥 Upload a short face video",
    type=["mp4", "mov", "avi", "mkv", "webm"],
    help="Max 50MB. A short 3-5 second face video works best — we'll extract your clearest frame automatically.",
)
if video_uploaded:
    st.video(video_uploaded)

example = "I have a round face shape with curly, thick hair. I am male."
user_text = st.text_area(
    "✏️ Describe your face shape, hair type, hair texture, and gender",
    placeholder=example,
    height=120,
    max_chars=1000,
)
st.caption(f"Example: *{example}*")

has_input = bool(image_uploaded or video_uploaded or user_text)
if st.button("✂️ Analyse & Recommend", type="primary", width="stretch", disabled=not has_input):
    with st.status("Starting analysis...", expanded=True) as status:
        def show_step(message: str):
            status.update(label=message)
            st.write(message)

        result = run_pipeline(
            image_bytes=image_uploaded.getvalue() if image_uploaded else None,
            image_filename=image_uploaded.name if image_uploaded else None,
            video_bytes=video_uploaded.getvalue() if video_uploaded else None,
            video_filename=video_uploaded.name if video_uploaded else None,
            user_text=user_text or None,
            on_progress=show_step,
        )

        if result.success:
            status.update(label="✅ Done!", state="complete", expanded=False)
        else:
            status.update(label="❌ Analysis stopped", state="error", expanded=False)

    # Persist across reruns so results (and the feedback widget below)
    # survive widget interactions, which each trigger a full script rerun.
    st.session_state.result = result
    st.session_state.analysis_id = st.session_state.get("analysis_id", 0) + 1

result = st.session_state.get("result")

# ── RESULTS ──────────────────────────────────────────────────────────────────
if result is not None:
    if not result.success:
        st.error(f"❌ {result.error}")
        st.stop()

    st.divider()

    # Input sources badge
    labels = {"image": "📷 Image", "video": "🎥 Video", "text": "✏️ Text"}
    badge = " + ".join(labels[s] for s in result.input_sources)
    st.caption(f"Input method: {badge}")

    # Detected features
    st.subheader("Detected Features")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Face Shape",   result.features.face_shape)
    col2.metric("Hair Type",    result.features.hair_type)
    col3.metric("Hair Texture", result.features.hair_texture)
    col4.metric(
        "Gender", result.features.gender,
        delta=f"{result.features.gender_confidence:.0%} confidence",
        delta_color="off",
    )

    st.divider()

    # Recommendation
    st.subheader("Your personalised recommendation")
    rec = result.recommendation
    st.write(rec.summary)

    if rec.haircuts:
        # One card per recommended style, side by side with equal heights
        cols = st.columns(len(rec.haircuts))
        for col, cut in zip(cols, rec.haircuts):
            with col, st.container(border=True, height="stretch"):
                images = find_style_images(
                    cut.name, result.features.gender, result.features.gender_confidence, max_images=1
                )
                if images:
                    st.image(images[0]["path"], width="stretch")
                st.markdown(f"#### {cut.name}")
                st.write(cut.why_it_works)
                st.markdown(f"**:material/brush: Styling:** {cut.styling_tip}")
                st.markdown(f"**:material/schedule: Maintenance:** {cut.maintenance}")
    else:
        # Fallback when the model returned plain text: scan it for known
        # style names and show any matching reference photos.
        ref_images = find_style_images(rec.summary, result.features.gender, result.features.gender_confidence)
        if ref_images:
            st.subheader("Reference looks")
            cols = st.columns(len(ref_images))
            for col, img in zip(cols, ref_images):
                with col:
                    st.image(img["path"], caption=img["style"], width="stretch")

    if rec.style_to_avoid:
        st.warning(f"**Avoid: {rec.style_to_avoid}** — {rec.avoid_reason}", icon=":material/block:")

    st.divider()

    # Knowledge sources
    with st.expander("📚 Knowledge sources used"):
        st.caption(f"Query: `{result.query_used}`")
        for i, chunk in enumerate(result.retrieved_context, 1):
            st.markdown(f"**Source {i}:**")
            st.text(chunk)

    st.divider()

    # ── FEEDBACK ─────────────────────────────────────────────────────────────
    # Keys include analysis_id so the radio resets for each new analysis.
    analysis_id = st.session_state.get("analysis_id", 0)
    saved_key = f"feedback_saved_{analysis_id}"

    st.subheader("Feedback")
    satisfaction = st.radio(
        "Are you satisfied with the recommendation?",
        options=["😊 Yes", "😞 No"],
        index=None,
        horizontal=True,
        key=f"satisfaction_{analysis_id}",
    )
    if satisfaction is not None:
        if st.session_state.get(saved_key):
            st.success("Thank you for your feedback!")
        elif satisfaction == "😊 Yes":
            save_feedback(
                satisfied=True,
                features=result.features,
                input_sources=result.input_sources,
            )
            st.session_state[saved_key] = True
            st.success("Thank you for your feedback!")
        else:
            suggestion = st.text_area(
                "Sorry to hear that! What style would you have preferred? (optional)",
                key=f"suggestion_{analysis_id}",
                max_chars=500,
                height=100,
            )
            if st.button("📨 Send feedback", key=f"send_feedback_{analysis_id}"):
                save_feedback(
                    satisfied=False,
                    features=result.features,
                    input_sources=result.input_sources,
                    suggestion=suggestion,
                )
                st.session_state[saved_key] = True
                st.success("Thank you for your feedback!")
