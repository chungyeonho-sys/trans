import streamlit as st

from translator import TranslationError, translate

MAX_CHARS = 5000

# 버튼 라벨 -> (화면 표시용 언어명, 모델에 전달할 언어명)
LANGUAGES = {
    "🇺🇸 영어": ("영어", "English"),
    "🇯🇵 일본어": ("일본어", "Japanese"),
    "🇻🇳 베트남어": ("베트남어", "Vietnamese"),
}


def load_css() -> None:
    # 색상은 하드코딩하지 않고 Streamlit 테마 변수/투명도 기반으로 지정해 라이트·다크 모두 대응
    st.markdown(
        """
        <style>
        /* Windows에는 국기 이모지 글리프가 없어 "US"처럼 글자로 보이므로 웹폰트로 보완 */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&display=swap');
        .block-container { max-width: 760px; padding-top: 2.5rem; }
        .app-subtitle { opacity: 0.7; margin-top: -0.75rem; margin-bottom: 1.25rem; }
        div[data-testid="stButton"] button {
            font-size: 1.05rem; padding: 0.6rem 0; border-radius: 10px;
            transition: transform 0.12s ease, box-shadow 0.12s ease;
        }
        div[data-testid="stButton"] button p {
            font-family: "Noto Color Emoji", "Source Sans", sans-serif;
        }
        div[data-testid="stButton"] button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(127, 127, 127, 0.25);
        }
        .char-count { text-align: right; font-size: 0.85rem; opacity: 0.6; margin-top: -0.5rem; }
        .char-count.over { color: var(--st-red-color, #ff4b4b); opacity: 1; font-weight: 600; }
        .result-label { font-weight: 600; font-size: 1.05rem; margin-bottom: 0.4rem; }
        .app-footer { text-align: center; font-size: 0.8rem; opacity: 0.5; margin-top: 3rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def live_char_counter() -> None:
    # Streamlit의 text_area는 포커스를 잃거나 Ctrl+Enter를 눌러야 값이 서버로 전달되므로,
    # 글자 수는 브라우저에서 입력할 때마다 직접 갱신한다. 리렌더링마다 리스너가 중복 등록되지 않도록 한 번만 건다.
    st.html(
        f"""
        <script>
        if (!window.__charCounterBound) {{
          window.__charCounterBound = true;
          document.addEventListener("input", (e) => {{
            if (e.target.tagName !== "TEXTAREA") return;
            const el = document.querySelector(".char-count");
            if (!el) return;
            const n = e.target.value.length;
            el.textContent = n.toLocaleString("en-US") + " / {MAX_CHARS:,}";
            el.classList.toggle("over", n > {MAX_CHARS});
          }});
        }}
        </script>
        """,
        unsafe_allow_javascript=True,
    )


st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="centered")
load_css()

st.title("🌐 다국어 번역기")
st.markdown(
    '<p class="app-subtitle">번역할 글을 입력하고 언어 버튼을 누르세요.</p>',
    unsafe_allow_html=True,
)

text = st.text_area(
    "번역할 글",
    height=200,
    placeholder="예) 안녕하세요. 만나서 반갑습니다.",
    label_visibility="collapsed",
    # max_chars는 쓰지 않는다: 한도를 넘는 붙여넣기를 Streamlit이 안내 없이 통째로 무시하기 때문
)
over = len(text) > MAX_CHARS
st.markdown(
    f'<div class="char-count{" over" if over else ""}">{len(text):,} / {MAX_CHARS:,}</div>',
    unsafe_allow_html=True,
)
live_char_counter()

selected = None
for col, label in zip(st.columns(3), LANGUAGES):
    if col.button(label, width="stretch"):
        selected = label

if selected:
    display_name, target = LANGUAGES[selected]
    # 새 요청이 성공하지 못하면(경고·오류) 이전 결과가 이번 요청의 결과처럼 보이지 않도록 지운다
    st.session_state.pop("result", None)
    if not text.strip():
        st.warning("번역할 내용을 입력해 주세요.", icon="⚠️")
    elif over:
        st.warning(
            f"입력은 최대 {MAX_CHARS:,}자까지 가능합니다. (현재 {len(text):,}자)", icon="⚠️"
        )
    else:
        with st.spinner("번역 중..."):
            try:
                st.session_state.result = translate(text, target)
                st.session_state.result_lang = display_name
            except TranslationError as e:
                st.error(str(e).removeprefix("❌ "), icon="❌")

if "result" in st.session_state:
    with st.container(border=True):
        st.markdown(
            f'<div class="result-label">번역 결과 ({st.session_state.result_lang})</div>',
            unsafe_allow_html=True,
        )
        # st.code는 우측 상단에 복사 버튼을 제공한다
        st.code(st.session_state.result, language=None, wrap_lines=True)

st.markdown(
    '<div class="app-footer">Powered by OpenAI · Streamlit</div>', unsafe_allow_html=True
)
