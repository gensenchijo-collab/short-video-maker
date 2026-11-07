import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
import numpy as np
import tempfile
import os
import io

st.set_page_config(page_title="ショート動画メーカー", page_icon="🎬")

st.title("🎬 ショート動画メーカー")
st.write("写真と文章を入力して動画を自動作成します。")

title = st.text_input("動画タイトル", "最高にかわいい女性芸能人3選")
intro = st.text_input("冒頭の文章", "ぜひ最後までご覧ください！")

count = st.number_input("紹介する人数", 1, 8, 3)

items = []

for i in range(int(count)):
    st.subheader(f"{i+1}人目")

    img = st.file_uploader(
        "写真を選択",
        type=["jpg", "jpeg", "png"],
        key=f"img{i}"
    )

    name = st.text_input("名前", key=f"name{i}")
    comment = st.text_area("紹介コメント", key=f"comment{i}")
    seconds = st.slider("表示時間", 3, 12, 8, key=f"time{i}")

    items.append((img, name, comment, seconds))

bgm = st.file_uploader(
    "BGM（任意）",
    type=["mp3", "wav", "m4a"]
)

outro = st.text_input("最後のメッセージ", "最後までご覧いただきありがとうございます！")


def get_font(size):
    paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"
    ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def create_image(photo, heading, text, mode="normal"):

    W, H = 720, 1280

    if photo:
        img = Image.open(io.BytesIO(photo)).convert("RGB")

        ratio = max(W / img.width, H / img.height)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))

        x = (img.width - W) // 2
        y = (img.height - H) // 2

        img = img.crop((x, y, x + W, y + H))
    else:
        img = Image.new("RGB", (W, H), (25, 25, 35))

    draw = ImageDraw.Draw(img)

    # 下部を暗くする
    for y in range(650, H):
        alpha = int(170 * (y - 650) / 630)
        draw.line((0, y, W, y), fill=(0, 0, 0))

    if mode == "title":
        font = get_font(65)
        draw.text(
            (W // 2, 500),
            heading,
            fill="red",
            font=font,
            anchor="mm",
            stroke_width=5,
            stroke_fill="black"
        )

        draw.text(
            (W // 2, 850),
            text,
            fill="white",
            font=get_font(35),
            anchor="mm",
            stroke_width=4,
            stroke_fill="black"
        )

    elif mode == "outro":
        draw.text(
            (W // 2, H // 2),
            heading,
            fill="white",
            font=get_font(38),
            anchor="mm",
            stroke_width=5,
            stroke_fill="black"
        )

    else:
        draw.text(
            (W // 2, 900),
            heading,
            fill="yellow",
            font=get_font(42),
            anchor="mm",
            stroke_width=5,
            stroke_fill="black"
        )

        draw.text(
            (W // 2, 1030),
            text,
            fill="white",
            font=get_font(38),
            anchor="mm",
            stroke_width=5,
            stroke_fill="black"
        )

    return np.array(img)


def make_clip(photo, heading, text, seconds, mode="normal"):
    frame = create_image(photo, heading, text, mode)
    return ImageClip(frame).with_duration(seconds)


if st.button("🎥 動画を作成"):

    if not any(item[0] for item in items):
        st.error("写真を1枚以上選択してください。")
        st.stop()

    clips = []

    clips.append(
        make_clip(None, title, intro, 3, "title")
    )

    for img, name, comment, seconds in items:

        if img is None:
            continue

        clips.append(
            make_clip(
                img.getvalue(),
                name,
                comment,
                seconds
            )
        )

    clips.append(
        make_clip(None, outro, "", 3, "outro")
    )

    with st.spinner("動画を作成しています..."):

        video = concatenate_videoclips(
            clips,
            method="compose"
        )

        if bgm:
            with tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False
            ) as f:
                f.write(bgm.getvalue())
                audio_path = f.name

            audio = AudioFileClip(audio_path)

            if audio.duration < video.duration:
                from moviepy import concatenate_audioclips

                audio = concatenate_audioclips(
                    [audio] * (int(video.duration / audio.duration) + 1)
                )

            audio = audio.subclipped(0, video.duration)
            video = video.with_audio(audio)

        output = tempfile.NamedTemporaryFile(
            suffix=".mp4",
            delete=False
        ).name

        video.write_videofile(
            output,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            logger=None
        )

        with open(output, "rb") as f:
            result = f.read()

        st.success("動画が完成しました！")

        st.video(result)

        st.download_button(
            "📥 動画を保存",
            result,
            file_name="short_video.mp4",
            mime="video/mp4"
        )

        video.close()
        for clip in clips:
            clip.close()
