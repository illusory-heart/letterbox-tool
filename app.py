import streamlit as st
from PIL import Image, ImageOps
import io

# --- 1. 기본 설정 및 정렬(Anchor) 좌표 ---
# 이미지가 캔버스 어디에 위치할지 결정하는 좌표입니다.
ANCHORS = {
    "중앙 (Center)": (0.5, 0.5),
    "위 (Top)": (0.5, 0.0),
    "아래 (Bottom)": (0.5, 1.0),
    "왼쪽 (Left)": (0.0, 0.5),
    "오른쪽 (Right)": (1.0, 0.5),
}

# --- 2. 핵심 함수 정의 ---

def parse_color(hex_color):
    """Streamlit 색상 선택기(#RRGGBB) 값을 RGB 튜플로 변환합니다."""
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def apply_letterbox(img, target_ratio_val, color, anchor_name):
    """이미지에 레터박스(여백)를 추가하여 비율을 맞춥니다."""
    
    # 이미지 모드 확인 (P모드나 투명도 등이 있으면 RGB로 변환)
    if img.mode != "RGB":
        img = img.convert("RGB")
        
    w, h = img.size
    src_ratio = w / h
    target_ratio = target_ratio_val

    # 이미 비율이 거의 같다면 원본 반환
    if abs(src_ratio - target_ratio) < 1e-4:
        return img.copy()

    # 원본이 목표보다 더 '가로로 긴' 경우 (위아래 여백 필요)
    if src_ratio > target_ratio:
        canvas_w = w
        canvas_h = int(round(w / target_ratio))
    # 원본이 목표보다 더 '세로로 긴' 경우 (양옆 여백 필요)
    else:
        canvas_h = h
        canvas_w = int(round(h * target_ratio))

    # 여백 계산
    extra_w = canvas_w - w
    extra_h = canvas_h - h
    
    # 정렬 기준에 따른 위치 계산
    ax, ay = ANCHORS[anchor_name]
    left = int(round(extra_w * ax))
    top = int(round(extra_h * ay))

    # 새 캔버스(배경) 생성
    canvas = Image.new("RGB", (canvas_w, canvas_h), color)
    # 원본 이미지 붙여넣기
    canvas.paste(img, (left, top))
    
    return canvas

def parse_ratio_text(text):
    """'16:9' 같은 문자열을 숫자(1.777...)로 변환합니다."""
    try:
        # 괄호 안의 설명 제거 (예: "1:1 (인스타)" -> "1:1")
        clean_text = text.split(' ')[0]
        if ":" in clean_text:
            w, h = map(float, clean_text.split(":"))
            return w / h
        return float(clean_text)
    except:
        return 1.0

# --- 3. Streamlit 앱 UI 구성 ---

# 페이지 기본 설정 (아이콘, 제목)
st.set_page_config(page_title="Letterbox Tool", page_icon="🖼️")

st.title("🖼️ 모바일 이미지 비율 맞춤")
st.write("사진 잘림 없이 원하는 비율로 배경을 채워보세요.")

# --- 사이드바: 옵션 설정 ---
with st.expander("⚙️ 설정 열기 (비율/색상/위치)", expanded=True):
    
    # 비율 선택
    ratio_options = [
        "1:1 (인스타그램/카톡프사)", 
        "4:5 (인스타그램 세로)", 
        "9:16 (릴스/틱톡/스토리)", 
        "16:9 (유튜브 썸네일)", 
        "3:4 (기본 사진비율)", 
        "직접 입력"
    ]
    selected_ratio_str = st.selectbox("만들고 싶은 비율", ratio_options)
    
    # 직접 입력일 경우 처리
    target_ratio = 1.0
    if selected_ratio_str == "직접 입력":
        custom_input = st.text_input("비율 입력 (예: 21:9)", "1:1")
        target_ratio = parse_ratio_text(custom_input)
    else:
        target_ratio = parse_ratio_text(selected_ratio_str)

    col1, col2 = st.columns(2)
    with col1:
        # 배경색 선택
        bg_color_hex = st.color_picker("배경색 선택", "#FFFFFF") # 기본값 흰색
    with col2:
        # 위치 정렬 선택
        anchor_selection = st.selectbox("사진 위치", list(ANCHORS.keys()))

# --- 메인 화면: 파일 업로드 및 결과 ---
uploaded_file = st.file_uploader("사진을 선택하세요", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file:
    try:
        # 이미지 로드
        image = Image.open(uploaded_file)
        
        # 🌟 중요: 휴대폰 사진 회전 정보(EXIF) 반영
        image = ImageOps.exif_transpose(image)
        
        st.image(image, caption="원본 사진", use_container_width=True)

        # 변환 버튼
        if st.button("배경 채우기 실행 ✨", type="primary", use_container_width=True):
            
            # 로딩 표시
            with st.spinner("이미지 처리 중..."):
                bg_rgb = parse_color(bg_color_hex)
                result_image = apply_letterbox(image, target_ratio, bg_rgb, anchor_selection)
                
                # 결과 보여주기
                st.success("완료되었습니다!")
                st.image(result_image, caption="결과물", use_container_width=True)
                
                # 다운로드 버튼 생성
                buf = io.BytesIO()
                # 호환성을 위해 PNG로 저장
                result_image.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                # 원본 파일명 앞에 'edited_' 붙이기
                original_name = uploaded_file.name.split('.')[0]
                download_name = f"edited_{original_name}.png"
                
                st.download_button(
                    label="⬇️ 앨범에 저장하기",
                    data=byte_im,
                    file_name=download_name,
                    mime="image/png",
                    use_container_width=True
                )
                
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.write("이미지 파일이 손상되었거나 지원하지 않는 형식일 수 있습니다.")
