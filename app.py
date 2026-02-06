import streamlit as st
from PIL import Image, ImageOps
import io

# --- 설정 및 함수 정의 ---
ANCHORS = {
      "center": (0.5, 0.5), "top": (0.5, 0.0), "bottom": (0.5, 1.0),
      "left": (0.0, 0.5), "right": (1.0, 0.5),
      "top-left": (0.0, 0.0), "top-right": (1.0, 0.0),
      "bottom-left": (0.0, 1.0), "bottom-right": (1.0, 1.0),
}

def parse_color(hex_color):
      # Hex 코드를 RGBA로 변환
      if hex_color.startswith("#"):
                hex_color = hex_color.lstrip('#')
                lv = len(hex_color)
                return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)) + (255,)
            return (255, 255, 255, 255)

def ensure_mode(img, color):
      # 투명도가 있거나 색상에 투명도가 있으면 RGBA로 변환
      if img.mode in ("RGBA", "LA") or (len(color) == 4 and color[3] < 255):
                return img.convert("RGBA")
            return img.convert("RGB")

def get_padding(w, h, target_w, target_h, anchor):
      target_ratio = target_w / target_h
    src_ratio = w / h

    if abs(src_ratio - target_ratio) < 1e-9:
              return (w, h, 0, 0, 0, 0)

    if src_ratio > target_ratio:
              canvas_w = w
              canvas_h = int(round(w / target_ratio))
              extra = canvas_h - h
              ax, ay = ANCHORS[anchor]
              top = int(round(extra * ay))
              bottom = extra - top
              return (canvas_w, canvas_h, 0, top, 0, bottom)
else:
        canvas_h = h
          canvas_w = int(round(h * target_ratio))
        extra = canvas_w - w
        ax, ay = ANCHORS[anchor]
        left = int(round(extra * ax))
        right = extra - left
        return (canvas_w, canvas_h, left, 0, right, 0)

def apply_letterbox(img, target_w, target_h, color, anchor):
      img = ensure_mode(img, color)
    w, h = img.size
    canvas_w, canvas_h, left, top, right, bottom = get_padding(w, h, target_w, target_h, anchor)

    if (left, top, right, bottom) == (0,0,0,0):
              return img.copy()

    canvas_mode = "RGBA" if (img.mode == "RGBA" or color[3] < 255) else "RGB"
    canvas = Image.new(canvas_mode, (canvas_w, canvas_h), color)
    canvas.paste(img, (left, top))
    return canvas

def parse_ratio_str(s):
      try:
                if ":" in s:
                              a, b = s.split(":", 1)
                              return float(a), float(b)
                          return 1.0, 1.0
    except:
        return 1.0, 1.0

# --- 화면 구성 (UI) ---
st.set_page_config(page_title="Letterbox Tool", page_icon="🎨")

st.title("🎨 이미지 비율 맞춤 도구")
st.write("인스타, 유튜브 등 원하는 비율로 여백을 만들어줍니다.")

# 사이드바 (설정 메뉴)
with st.expander("🛠️ 설정 열기 (비율/색상)", expanded=True):
      col1, col2 = st.columns(2)
    with col1:
              ratio_preset = st.selectbox(
                            "비율 선택",
                            ["1:1 (인스타/카톡)", "4:5 (인스타 세로)", "16:9 (유튜브)", "9:16 (릴스/쇼츠)", "4:3", "3:4", "직접 입력"]
              )
    with col2:
              bg_hex = st.color_picker("배경색", "#FFFFFF")

    anchor = st.selectbox("이미지 위치 정렬", list(ANCHORS.keys()), index=0)

    target_ratio_w, target_ratio_h = 1.0, 1.0
    if ratio_preset == "직접 입력":
              custom = st.text_input("비율 입력 (예: 21:9)", "21:9")
        target_ratio_w, target_ratio_h = parse_ratio_str(custom)
else:
        target_ratio_w, target_ratio_h = parse_ratio_str(ratio_preset.split(" ")[0])

# 파일 업로드
uploaded = st.file_uploader("이미지를 여기에 올리세요", type=["png", "jpg", "jpeg", "webp"])

if uploaded:
      # 이미지 열기 및 회전 보정
      original = Image.open(uploaded)
    original = ImageOps.exif_transpose(original)

    st.image(original, caption="원본", use_container_width=True)

    # 변환 실행 버튼
    if st.button("변환하기 ✨", type="primary", use_container_width=True):
              color_rgba = parse_color(bg_hex)
        result_img = apply_letterbox(original, target_ratio_w, target_ratio_h, color_rgba, anchor)

        st.success("완료되었습니다!")
        st.image(result_img, caption=f"결과물 ({ratio_preset})", use_container_width=True)

        # 다운로드 준비
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        byte_data = buf.getvalue()

        filename = uploaded.name.split(".")[0] + "_edited.png"
        st.download_button(
                      label="⬇️ 갤러리에 저장 (다운로드)",
                      data=byte_data,
                      file_name=filename,
                      mime="image/png",
                      use_container_width=True
        )
