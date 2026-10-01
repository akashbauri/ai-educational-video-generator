import streamlit as st

from services.llm_service import (
    generate_scene_plan,
)

from services.image_service import (
    generate_scene_image,
)

from services.tts_service import (
    generate_voice,
)

from services.subtitle_service import (
    create_srt,
)

from services.video_service import (
    build_video,
)

from utils.duration import (
    allocate_scene_durations,
)

from utils.file_utils import (
    make_job_dir,
)


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Educational Video Generator",
    page_icon="🎓",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "🎓 AI Educational Video Generator"
)

st.write(
    """
Turn educational text into an educational video
with AI-generated scenes, narration, animation,
subtitles and MP4 rendering.
"""
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Video Settings"
    )

    language = st.selectbox(
        "Language",
        [
            "English",
            "Hindi",
            "Bengali",
        ],
    )

    education_level = st.selectbox(
        "Education Level",
        [
            "Class 5",
            "Class 8",
            "Class 10",
            "Class 12",
            "College",
            "General",
        ],
    )

    duration = st.slider(
        "Target Video Duration",
        min_value=60,
        max_value=180,
        value=120,
        step=10,
    )

    visual_mode = st.selectbox(
        "Visual Mode",
        [
            "Smart Automatic",
            "AI Images",
            "Animation Only",
        ],
    )


# ============================================================
# INPUT
# ============================================================

educational_text = st.text_area(
    "📚 Enter Educational Content",

    height=330,

    placeholder="""
Example:

Photosynthesis is the process by which
green plants make their food using sunlight,
carbon dioxide and water.

Paste your complete educational material here.
""",
)


# ============================================================
# GENERATE BUTTON
# ============================================================

generate_button = st.button(
    "🚀 Generate Educational Video",
    type="primary",
    use_container_width=True,
)


if generate_button:

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    if len(
        educational_text.strip()
    ) < 80:

        st.error(
            "Please enter at least 80 characters "
            "of educational content."
        )

        st.stop()

    # --------------------------------------------------------
    # CREATE TEMP JOB DIRECTORY
    # --------------------------------------------------------

    job_dir = make_job_dir()

    progress = st.progress(
        0
    )

    status = st.empty()

    try:

        # ====================================================
        # STEP 1
        # QWEN SCENE PLANNING
        # ====================================================

        status.info(
            "🧠 Step 1/6 — Qwen is understanding "
            "the educational content..."
        )

        plan = generate_scene_plan(
            educational_text=educational_text,
            language=language,
            education_level=education_level,
            target_seconds=duration,
        )

        progress.progress(
            15
        )

        # ----------------------------------------------------
        # SHOW PLAN
        # ----------------------------------------------------

        with st.expander(
            "🧠 View AI Scene Plan",
            expanded=False,
        ):

            st.json(
                plan
            )

        scenes = plan[
            "scenes"
        ]

        # ====================================================
        # DURATION ALLOCATION
        # ====================================================

        durations = (
            allocate_scene_durations(
                scenes,
                duration,
            )
        )

        # ====================================================
        # ARRAYS
        # ====================================================

        image_files = []

        audio_files = []

        animations = []

        # ====================================================
        # SCENE PROCESSING
        # ====================================================

        total_scenes = len(
            scenes
        )

        for index, (
            scene,
            scene_duration,
        ) in enumerate(
            zip(
                scenes,
                durations,
            ),
            start=1,
        ):

            # ------------------------------------------------
            # IMAGE
            # ------------------------------------------------

            status.info(
                f"🎨 Step 2/6 — Creating visual "
                f"{index}/{total_scenes}..."
            )

            image_path = (
                job_dir
                / f"scene_{index:02d}.png"
            )

            if visual_mode == "Animation Only":

                image_prompt = (
                    "Clean educational background "
                    "illustration related to the lesson."
                )

            else:

                image_prompt = (
                    scene.get(
                        "image_prompt",
                        "",
                    )
                    or scene.get(
                        "narration",
                        "",
                    )
                )

            image_path, ai_image_used = (
                generate_scene_image(
                    prompt=image_prompt,
                    on_screen_text=scene.get(
                        "on_screen_text",
                        "",
                    ),
                    scene_title=plan[
                        "title"
                    ],
                    output_path=image_path,
                )
            )

            image_files.append(
                image_path
            )

            # ------------------------------------------------
            # TTS
            # ------------------------------------------------

            status.info(
                f"🗣️ Step 3/6 — Creating narration "
                f"{index}/{total_scenes}..."
            )

            audio_path = (
                job_dir
                / f"scene_{index:02d}.mp3"
            )

            generate_voice(
                text=scene[
                    "narration"
                ],
                language=language,
                output_path=audio_path,
            )

            audio_files.append(
                audio_path
            )

            animations.append(
                scene.get(
                    "animation",
                    "zoom",
                )
            )

            progress_value = (
                15
                + int(
                    45
                    * index
                    / total_scenes
                )
            )

            progress.progress(
                progress_value
            )

        # ====================================================
        # STEP 4
        # SUBTITLES
        # ====================================================

        status.info(
            "📝 Step 4/6 — Creating subtitles..."
        )

        subtitle_path = (
            job_dir
            / "subtitles.srt"
        )

        create_srt(
            scenes=scenes,
            durations=durations,
            output_path=subtitle_path,
        )

        progress.progress(
            70
        )

        # ====================================================
        # STEP 5
        # VIDEO RENDERING
        # ====================================================

        status.info(
            "🎬 Step 5/6 — Rendering animated scenes..."
        )

        final_video = build_video(
            image_files=image_files,
            audio_files=audio_files,
            durations=durations,
            animations=animations,
            subtitle_path=subtitle_path,
            work_dir=job_dir,
        )

        progress.progress(
            95
        )

        # ====================================================
        # STEP 6
        # COMPLETE
        # ====================================================

        status.info(
            "✅ Step 6/6 — Finalizing MP4..."
        )

        video_bytes = (
            final_video.read_bytes()
        )

        progress.progress(
            100
        )

        status.success(
            "🎉 Educational video generated!"
        )

        # ====================================================
        # VIDEO PREVIEW
        # ====================================================

        st.subheader(
            f"🎬 {plan['title']}"
        )

        st.video(
            video_bytes
        )

        # ====================================================
        # DOWNLOAD
        # ====================================================

        st.download_button(
            label="⬇️ Download MP4",
            data=video_bytes,
            file_name=(
                "educational_video.mp4"
            ),
            mime="video/mp4",
            use_container_width=True,
        )

        # ====================================================
        # SUBTITLE PREVIEW
        # ====================================================

        with st.expander(
            "📝 View Generated Subtitles"
        ):

            st.code(
                subtitle_path.read_text(
                    encoding="utf-8"
                )
            )

        # ====================================================
        # SUCCESS INFORMATION
        # ====================================================

        st.success(
            f"""
Video completed.

Scenes: {len(scenes)}

Target duration: {duration} seconds

Language: {language}

Education level: {education_level}
"""
        )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as exc:

        progress.empty()

        status.error(
            "❌ Video generation stopped."
        )

        st.error(
            "Something went wrong while generating "
            "the educational video."
        )

        st.exception(
            exc
        )

        st.warning(
            """
The application does not intentionally switch
to a paid AI provider.

If this error mentions Hugging Face inference,
model access or quota, check your HF_TOKEN,
model access and remaining free inference allowance.
"""
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Educational Video Generator — "
    "GitHub + Streamlit Cloud"
)
