import streamlit as st

from services.llm_service import generate_scene_plan
from services.visual_decision_service import decide_visual
from services.image_service import generate_scene_image
from services.tts_service import generate_voice
from services.subtitle_service import create_srt
from services.video_service import build_video
from services.animation_service import create_animation_video

from utils.file_utils import make_job_dir


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Educational Video Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    .feature-card {
        padding: 18px;
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-bottom: 12px;
    }

    .visual-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        background-color: #eef4ff;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .animation-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        background-color: #e9fff3;
        font-weight: 600;
        margin-bottom: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🎓 AI Educational Video Generator</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    Create intelligent educational videos with AI narration,
    multilingual text, visual explanations, diagrams,
    formulas and real educational animations.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Video Settings")
st.sidebar.markdown("---")


# ============================================================
# LANGUAGE
# ============================================================

language = st.sidebar.selectbox(
    "🌐 Language",
    [
        "English",
        "Hindi",
        "Bengali",
    ],
)


# ============================================================
# EDUCATION LEVEL
# ============================================================

education_level = st.sidebar.selectbox(
    "🎓 Education Level",
    [
        "Class 5",
        "Class 8",
        "Class 10",
        "Class 12",
        "College",
        "General",
    ],
)


# ============================================================
# SUBJECT
# ============================================================

subject = st.sidebar.selectbox(
    "📚 Subject",
    [
        "General",
        "Mathematics",
        "Physics",
        "Chemistry",
        "Biology",
        "Computer Science",
        "History",
        "Geography",
    ],
)


# ============================================================
# VIDEO DURATION
# ============================================================

duration = st.sidebar.slider(
    "⏱️ Target Duration (seconds)",
    min_value=60,
    max_value=180,
    value=120,
    step=10,
)


# ============================================================
# VISUAL MODE
# ============================================================

visual_mode = st.sidebar.selectbox(
    "🎬 Visual Mode",
    [
        "Smart Automatic",
        "AI Images",
        "Animation Only",
    ],
)


# ============================================================
# VOICE
# ============================================================

voice_style = st.sidebar.selectbox(
    "🎙️ Voice",
    [
        "Female Teacher",
        "Male Teacher",
    ],
)


speech_rate = st.sidebar.slider(
    "🗣️ Speech Speed",
    -15,
    15,
    0,
    5,
)


# ============================================================
# INFORMATION
# ============================================================

st.sidebar.markdown("---")

st.sidebar.info(
    """
    **AI Educational Video Engine**

    🧠 Qwen  
    🎨 AI Visuals  
    🎞️ Real Frame Animation  
    📐 Formula Animation  
    🔬 Physics Visuals  
    🧪 Chemistry Visuals  
    📊 Diagram & Chart Engine  
    🤖 AIVA Character  
    🎙️ Multilingual Voice  
    📝 Subtitles  
    🎬 FFmpeg  

    **Languages**

    🇬🇧 English  
    🇮🇳 Hindi  
    🇮🇳 Bengali
    """
)


# ============================================================
# MAIN INPUT
# ============================================================

st.markdown(
    '<div class="section-title">📚 Educational Content</div>',
    unsafe_allow_html=True,
)

educational_text = st.text_area(
    "Enter the topic or lesson you want to convert into a video.",
    height=280,
    placeholder=(
        "Example:\n\n"
        "Explain Newton's Second Law to a Class 8 student. "
        "Explain force, mass and acceleration with a simple "
        "example and formula."
    ),
)


# ============================================================
# AIVA PREVIEW
# ============================================================

with st.expander("🤖 Meet AIVA — Your AI Educational Assistant"):

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(
            """
            ### 🤖 AIVA

            **Friendly Educational Robot**

            - Curious
            - Helpful
            - Child-safe
            - Friendly
            - Intelligent
            - Visual Teacher
            """
        )

    with col2:
        st.markdown(
            """
            AIVA helps students understand difficult concepts
            using simple explanations, visual examples,
            formulas, diagrams and step-by-step teaching.

            AIVA can appear during:

            - Introductions
            - Explanations
            - Questions
            - Examples
            - Summaries
            - Closing
            """
        )


# ============================================================
# GENERATE BUTTON
# ============================================================

generate_button = st.button(
    "🚀 Generate Educational Video",
    type="primary",
    use_container_width=True,
)


# ============================================================
# GENERATION PIPELINE
# ============================================================

if generate_button:

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    if not educational_text.strip():

        st.error(
            "Please enter educational content first."
        )

        st.stop()

    if len(educational_text.strip()) < 80:

        st.warning(
            "Please provide at least 80 characters "
            "so the AI can create a useful lesson."
        )

        st.stop()


    # ========================================================
    # JOB DIRECTORY
    # ========================================================

    try:

        job_dir = make_job_dir()

        image_dir = job_dir / "images"
        audio_dir = job_dir / "audio"
        animation_dir = job_dir / "animations"

        image_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        audio_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        animation_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    except Exception as exc:

        st.error(
            f"Could not create temporary job directory:\n{exc}"
        )

        st.stop()


    # ========================================================
    # PROGRESS
    # ========================================================

    progress = st.progress(0)
    status = st.empty()


    # ========================================================
    # STEP 1 — AI SCENE PLANNING
    # ========================================================

    status.info(
        "🧠 Step 1/6 — AI is understanding the lesson..."
    )

    progress.progress(10)

    try:

        scenes = generate_scene_plan(
            educational_text=educational_text,
            language=language,
            education_level=education_level,
            target_seconds=duration,
        )

    except TypeError:

        try:

            scenes = generate_scene_plan(
                educational_text,
                language,
                education_level,
                duration,
            )

        except Exception as exc:

            st.error(
                f"Scene planning failed:\n{exc}"
            )

            st.stop()

    except Exception as exc:

        st.error(
            f"Scene planning failed:\n{exc}"
        )

        st.stop()


    if not scenes:

        st.error(
            "The AI did not generate any scenes."
        )

        st.stop()


    st.success(
        f"AI created {len(scenes)} educational scenes."
    )


    # ========================================================
    # DATA STORAGE
    # ========================================================

    image_files = []
    animation_files = []
    audio_files = []

    actual_durations = []

    visual_decisions = []


    # ========================================================
    # STEP 2 — VISUAL DECISION ENGINE
    # ========================================================

    status.info(
        "🎨 Step 2/6 — AI is deciding how each concept "
        "should be visually explained..."
    )

    progress.progress(25)


    for index, scene in enumerate(
        scenes,
        start=1,
    ):

        narration = scene.get(
            "narration",
            "",
        ).strip()


        # ----------------------------------------------------
        # VISUAL DECISION
        # ----------------------------------------------------

        try:

            visual_decision = decide_visual(
                narration=narration,
                subject=subject,
                education_level=education_level,
                language=language,
            )

        except Exception:

            visual_decision = {
                "visual_type": "ai_image",
                "subject": subject.lower(),
                "reason": (
                    "Fallback visual because the "
                    "visual decision engine failed."
                ),
                "animation": "fade",
                "visual_prompt": narration,
                "formula": "",
                "explanation": narration,
                "chart_data": [],
                "diagram_elements": [],
                "whiteboard_steps": [],
                "equation_steps": [],
            }


        # ----------------------------------------------------
        # VISUAL MODE OVERRIDE
        # ----------------------------------------------------

        if visual_mode == "AI Images":

            visual_decision["visual_type"] = "ai_image"

        elif visual_mode == "Animation Only":

            visual_decision["visual_type"] = "animation"


        # ----------------------------------------------------
        # STORE DECISION
        # ----------------------------------------------------

        scene["visual_type"] = visual_decision.get(
            "visual_type",
            "ai_image",
        )

        scene["visual_decision"] = visual_decision

        visual_decisions.append(
            visual_decision
        )


        # ----------------------------------------------------
        # SHOW SCENE INFORMATION
        # ----------------------------------------------------

        visual_name = (
            visual_decision
            .get("visual_type", "ai_image")
            .replace("_", " ")
            .title()
        )

        with st.expander(
            f"🎬 Scene {index} — {visual_name}",
            expanded=False,
        ):

            st.markdown(
                f"""
                <div class="visual-badge">
                🎨 {visual_name}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(
                f"**Subject:** "
                f"{visual_decision.get('subject', subject)}"
            )

            st.write(
                f"**Reason:** "
                f"{visual_decision.get('reason', 'AI-selected visual')}"
            )

            st.write(
                f"**Animation:** "
                f"{visual_decision.get('animation', 'smooth')}"
            )

            if visual_decision.get("formula"):

                st.write(
                    f"**Formula:** "
                    f"{visual_decision['formula']}"
                )

            st.write(
                f"**Narration:** {narration}"
            )


    # ========================================================
    # STEP 3 — VOICE GENERATION
    # ========================================================

    status.info(
        "🎙️ Step 3/6 — Creating multilingual AI narration..."
    )

    progress.progress(40)


    for index, scene in enumerate(
        scenes,
        start=1,
    ):

        narration = scene.get(
            "narration",
            "",
        ).strip()


        audio_path = audio_dir / (
            f"scene_{index:02d}.mp3"
        )


        try:

            generated_audio = generate_voice(
                text=narration,
                language=language,
                output_path=audio_path,
                voice_style=voice_style,
                speech_rate=speech_rate,
            )

        except TypeError:

            # Compatibility with older TTS implementation

            try:

                generated_audio = generate_voice(
                    text=narration,
                    language=language,
                    output_path=audio_path,
                )

            except Exception as exc:

                st.error(
                    f"Voice generation failed "
                    f"for Scene {index}:\n{exc}"
                )

                st.stop()

        except Exception as exc:

            st.error(
                f"Voice generation failed "
                f"for Scene {index}:\n{exc}"
            )

            st.stop()


        # ----------------------------------------------------
        # AUDIO RESULT
        # ----------------------------------------------------

        if isinstance(
            generated_audio,
            tuple,
        ):

            generated_audio_path = generated_audio[0]

            generated_duration = float(
                generated_audio[1]
            )

        else:

            generated_audio_path = generated_audio

            generated_duration = 0.0


        if not generated_audio_path.exists():

            st.error(
                f"Audio was not created for Scene {index}."
            )

            st.stop()


        audio_files.append(
            generated_audio_path
        )

        actual_durations.append(
            generated_duration
        )


    # ========================================================
    # STEP 4 — VISUAL GENERATION + TRUE ANIMATION
    # ========================================================

    status.info(
        "🎬 Step 4/6 — Creating visuals and real animations..."
    )

    progress.progress(55)


    # Types that use the frame-based animation engine
    animation_types = {
        "formula",
        "equation",
        "diagram",
        "physics",
        "chemistry",
        "aiva",
        "animation",
    }


    for index, scene in enumerate(
        scenes,
        start=1,
    ):

        narration = scene.get(
            "narration",
            "",
        ).strip()

        visual_decision = scene.get(
            "visual_decision",
            {},
        )

        visual_type = visual_decision.get(
            "visual_type",
            "ai_image",
        )


        # ----------------------------------------------------
        # ACTUAL SCENE DURATION
        # ----------------------------------------------------

        scene_duration = actual_durations[index - 1]

        if scene_duration <= 0:

            scene_duration = max(
                3.0,
                duration / len(scenes),
            )


        visual_title = scene.get(
            "visual_focus",
            f"Scene {index}",
        )


        # ====================================================
        # TRUE ANIMATION
        # ====================================================

        if visual_type in animation_types:

            animation_path = (
                animation_dir /
                f"scene_{index:02d}.mp4"
            )


            try:

                create_animation_video(
                    animation_type=visual_type,
                    output_path=animation_path,
                    duration=scene_duration,
                    title=visual_title,
                    formula=visual_decision.get(
                        "formula",
                        "",
                    ),
                    explanation=visual_decision.get(
                        "explanation",
                        narration,
                    ),
                    steps=visual_decision.get(
                        "equation_steps",
                        [],
                    ),
                    nodes=visual_decision.get(
                        "diagram_elements",
                        [],
                    ),
                    subject=subject.lower(),
                )

            except Exception as exc:

                st.error(
                    f"Animation generation failed "
                    f"for Scene {index}:\n{exc}"
                )

                st.stop()


            if not animation_path.exists():

                st.error(
                    f"Animation was not created "
                    f"for Scene {index}."
                )

                st.stop()


            animation_files.append(
                animation_path
            )


            # ------------------------------------------------
            # ANIMATION PREVIEW
            # ------------------------------------------------

            with st.expander(
                f"🎞️ Preview Animated Scene {index}",
                expanded=False,
            ):

                st.markdown(
                    f"""
                    <div class="animation-badge">
                    🎞️ Real Frame Animation
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.video(
                    str(animation_path)
                )

                st.write(
                    f"**Visual Type:** "
                    f"{visual_type.replace('_', ' ').title()}"
                )

                st.write(
                    f"**Duration:** "
                    f"{scene_duration:.2f} seconds"
                )


        # ====================================================
        # AI IMAGE
        # ====================================================

        else:

            image_path = (
                image_dir /
                f"scene_{index:02d}.png"
            )


            image_prompt = visual_decision.get(
                "visual_prompt",
                scene.get(
                    "image_prompt",
                    narration,
                ),
            )


            on_screen_text = scene.get(
                "on_screen_text",
                "",
            )


            try:

                generate_scene_image(
                    prompt=image_prompt,
                    on_screen_text=on_screen_text,
                    scene_title=visual_title,
                    scene_number=index,
                    output_path=image_path,
                )

            except Exception as exc:

                st.error(
                    f"Image generation failed "
                    f"for Scene {index}:\n{exc}"
                )

                st.stop()


            if not image_path.exists():

                st.error(
                    f"Image was not created "
                    f"for Scene {index}."
                )

                st.stop()


            image_files.append(
                image_path
            )


            # ------------------------------------------------
            # IMAGE PREVIEW
            # ------------------------------------------------

            with st.expander(
                f"👁️ Preview Scene {index}",
                expanded=False,
            ):

                col1, col2 = st.columns(
                    [1, 1]
                )

                with col1:

                    st.image(
                        image_path,
                        caption=(
                            f"Scene {index} — "
                            f"{visual_type.replace('_', ' ').title()}"
                        ),
                        use_container_width=True,
                    )

                with col2:

                    st.markdown(
                        "### 🎙️ Narration"
                    )

                    st.write(
                        narration
                    )

                    st.markdown(
                        "### 🎨 Visual Method"
                    )

                    st.write(
                        visual_type.replace(
                            "_",
                            " ",
                        ).title()
                    )


        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        scene_progress = (
            index / len(scenes)
        )

        progress.progress(
            min(
                70,
                int(
                    55
                    + scene_progress * 15
                ),
            )
        )


    # ========================================================
    # STEP 5 — SUBTITLES
    # ========================================================

    status.info(
        "📝 Step 5/6 — Creating synchronized subtitles..."
    )

    progress.progress(75)


    try:

        subtitle_path = (
            job_dir /
            "subtitles.srt"
        )


        create_srt(
            scenes=scenes,
            durations=actual_durations,
            output_path=subtitle_path,
        )

    except Exception as exc:

        st.error(
            f"Subtitle generation failed:\n{exc}"
        )

        st.stop()


    # ========================================================
    # STEP 6 — FINAL VIDEO
    # ========================================================

    status.info(
        "🎥 Step 6/6 — Combining animation, narration "
        "and subtitles into the final video..."
    )

    progress.progress(85)


    try:

        video_path = (
            job_dir /
            "educational_video.mp4"
        )


        build_video(
            image_files=image_files,
            animation_files=animation_files,
            audio_files=audio_files,
            durations=actual_durations,
            subtitle_path=subtitle_path,
            output_path=video_path,
        )

    except TypeError:

        st.error(
            """
            Your video_service.py is still using the
            old build_video() function.

            Update video_service.py with the new version
            before generating the video.
            """
        )

        st.stop()

    except Exception as exc:

        st.error(
            f"Video rendering failed:\n{exc}"
        )

        st.stop()


    if not video_path.exists():

        st.error(
            "Final video was not created."
        )

        st.stop()


    # ========================================================
    # FINAL RESULT
    # ========================================================

    status.success(
        "✅ Educational video completed!"
    )

    progress.progress(100)

    st.balloons()


    st.markdown(
        '<div class="section-title">🎬 Final Educational Video</div>',
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    st.video(
        str(video_path)
    )


    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    with open(
        video_path,
        "rb",
    ) as video_file:

        st.download_button(
            label="⬇️ Download Educational Video",
            data=video_file.read(),
            file_name=(
                "ai_educational_video.mp4"
            ),
            mime="video/mp4",
            use_container_width=True,
        )


    # ========================================================
    # VISUAL DECISION SUMMARY
    # ========================================================

    st.markdown(
        '<div class="section-title">🧠 AI Visual Decisions</div>',
        unsafe_allow_html=True,
    )


    visual_counts = {}


    for decision in visual_decisions:

        visual_type = decision.get(
            "visual_type",
            "unknown",
        )

        visual_counts[visual_type] = (
            visual_counts.get(
                visual_type,
                0,
            )
            + 1
        )


    for visual_type, count in visual_counts.items():

        st.write(
            f"🎨 **{visual_type.replace('_', ' ').title()}** "
            f"— {count} scene(s)"
        )


    # ========================================================
    # EDUCATIONAL INFORMATION
    # ========================================================

    st.markdown("---")

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Scenes",
            len(scenes),
        )


    with col2:

        total_duration = sum(
            actual_durations
        )

        st.metric(
            "Video Duration",
            f"{total_duration:.1f}s",
        )


    with col3:

        st.metric(
            "Language",
            language,
        )


    # ========================================================
    # SUBTITLE DOWNLOAD
    # ========================================================

    if subtitle_path.exists():

        st.download_button(
            label="📝 Download Subtitles (.srt)",
            data=subtitle_path.read_text(
                encoding="utf-8"
            ),
            file_name=(
                "educational_video_subtitles.srt"
            ),
            mime="application/x-subrip",
        )


    # ========================================================
    # COMPLETE
    # ========================================================

    st.success(
        """
        🎓 Your educational video is ready.

        The video includes:

        • AI-generated educational explanation
        • Intelligent scene planning
        • AI visual decision system
        • AI-generated visuals
        • Real frame-based educational animation
        • Formula animation
        • Equation step animation
        • Diagram animation
        • Physics animation
        • Chemistry animation
        • AIVA animation
        • Multilingual narration
        • Synchronized subtitles
        • Automatic duration handling
        • Final MP4 rendering
        """
    )
