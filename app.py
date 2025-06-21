import pandas as pd
import streamlit as st
import random
import re
import os

# === Load Excel đa sheet ===
@st.cache_data(ttl=0)
def load_sheets(path):
    xls = pd.ExcelFile(path)
    return {sheet: xls.parse(sheet) for sheet in xls.sheet_names}

def reload_excel():
    global all_sheets, df_all
    all_sheets = load_sheets(excel_file)
    if sheet_name == 'All':
        df_all = pd.concat(all_sheets.values(), ignore_index=True)
    else:
        df_all = all_sheets[sheet_name]

excel_file = r"C:\Users\bena\OneDrive\BSNT Ngoại - Sản UMP 2025\Môn 4 - Sản phụ khoa\(!) Siêu cấp luyện đề\Ngân hàng câu hỏi môn 4 full.xlsx"
image_folder = r"C:\Users\bena\OneDrive\BSNT Ngoại - Sản UMP 2025\Môn 4 - Sản phụ khoa\(!) Siêu cấp luyện đề\images"
all_sheets = load_sheets(excel_file)

# === Sidebar điều khiển ===
st.sidebar.title("Tùy chọn")
sheet_options = ['All'] + list(all_sheets.keys())
sheet_name = st.sidebar.selectbox("Chọn slide (sheet):", sheet_options)

if st.sidebar.button("🔄 Tải lại file Excel"):
    reload_excel()
    st.rerun()

available_topics = all_sheets[sheet_name]['CodeTopic'].dropna().unique().tolist() if sheet_name != 'All' else pd.concat(all_sheets.values(), ignore_index=True)['CodeTopic'].dropna().unique().tolist()
topic_options = ['All'] + sorted(available_topics)
selected_topic = st.sidebar.selectbox("Chọn CodeTopic:", topic_options)
search_term = st.sidebar.text_input("Tìm từ khóa trong Original (ví dụ: 6123):").strip()
mode = st.sidebar.selectbox("Chọn chế độ hiển thị câu hỏi:", ["Ngẫu nhiên 1 câu", "Tăng dần theo Original", "Giảm dần theo Original", "Toàn bộ không sắp xếp"], index=1)
st.session_state.setdefault("show_note", True)
st.session_state.show_note = st.sidebar.checkbox("📝 Hiện ghi chú", value=st.session_state.show_note)

# === Dữ liệu chính ===
df_all = pd.concat(all_sheets.values(), ignore_index=True) if sheet_name == 'All' else all_sheets[sheet_name]
df = df_all[df_all['CodeTopic'] == selected_topic] if selected_topic != 'All' else df_all
if search_term:
    df = df[df['Original'].astype(str).str.contains(search_term, case=False, na=False)]

if df.empty:
    st.warning("Không có câu hỏi phù hợp với lựa chọn hiện tại.")
    st.stop()

if 'random_index' not in st.session_state:
    st.session_state.random_index = 0
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = ""

if mode == "Ngẫu nhiên 1 câu":
    st.session_state.random_index = random.randint(0, len(df) - 1)
    df_sorted = df
    questions = [df_sorted.iloc[st.session_state.random_index].to_dict()]
elif mode == "Tăng dần theo Original":
    df_sorted = df.sort_values(by='Original', ascending=True)
    if st.session_state.last_mode != mode:
        st.session_state.random_index = 0
    questions = [df_sorted.iloc[st.session_state.random_index].to_dict()]
    st.session_state.last_mode = mode
elif mode == "Giảm dần theo Original":
    df_sorted = df.sort_values(by='Original', ascending=False)
    if st.session_state.last_mode != mode:
        st.session_state.random_index = 0
    questions = [df_sorted.iloc[st.session_state.random_index].to_dict()]
    st.session_state.last_mode = mode
else:
    df_sorted = df
    questions = df_sorted.to_dict(orient='records')

# === Hiển thị câu hỏi ===
st.title("Luyện đề trắc nghiệm")
for q in questions:
    st.markdown(f"### {q['Original']}")

    text = q['Question']
    pattern = r"(?s)(.*?)\s+A\.\s+(.*?)\s+B\.\s+(.*?)\s+C\.\s+(.*?)\s+D\.\s+(.*?)\s*(?:E\.\s+(.*))?$"
    match = re.match(pattern, text)
    if match:
        question_text = match.group(1).strip()
        st.markdown(question_text)

        options = []
        for i, label in enumerate(['A', 'B', 'C', 'D', 'E']):
            content = match.group(i + 2)
            if content:
                options.append((label, f"{label}. {content.strip()}"))

        labels = [label for label, _ in options]
        display = [desc for _, desc in options]
        selected = st.radio("Chọn đáp án:", labels, format_func=dict(options).get, key=q['Original'] + '_select', horizontal=False)

        if st.button(f"Kiểm tra đáp án cho {q['Original']}"):
            correct = str(q['Anwser']) if pd.notna(q['Anwser']) else ""
            if correct == "":
                st.info("Câu hỏi này chưa có đáp án trong file. Vui lòng bổ sung sau.")
            elif selected == correct:
                st.success("\u2714 Đúng rồi!")
            else:
                st.error(f"\u2716 Sai! Đáp án đúng là: {correct}")
    else:
        st.markdown(text)

    if mode in ["Tăng dần theo Original", "Giảm dần theo Original"]:
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            if st.button("⏮ Câu đầu tiên"):
                st.session_state.random_index = 0
                st.rerun()
        with col2:
            if st.button("← Câu trước"):
                st.session_state.random_index = max(0, st.session_state.random_index - 1)
                st.rerun()
        with col3:
            if st.button("→ Câu tiếp theo"):
                st.session_state.random_index += 1
                st.rerun()
        with col4:
            if st.button("⏭ Câu cuối cùng"):
                st.session_state.random_index = len(df_sorted) - 1
                st.rerun()

    if pd.notna(q.get('Hình')):
        try:
            img_path = os.path.join(image_folder, str(q['Hình']).strip())
            if os.path.isfile(img_path):
                st.image(img_path, width=400)
            else:
                st.warning(f"Không tìm thấy hình: {q['Hình']}")
        except:
            st.warning(f"Không tải được hình: {q['Hình']}")

    if st.session_state.show_note:
        st.markdown("#### ✏️ Ghi chú (Note)")
        edited_note = st.text_area("Nhập ghi chú cho câu này:", value=q.get('Note') or "", key=q['Original'] + '_note', height=200)

        if st.button(f"💾 Lưu ghi chú cho {q['Original']}"):
            df_index = df_all[df_all['Original'] == q['Original']].index
            if not df_index.empty:
                df_all.loc[df_index[0], 'Note'] = edited_note
                with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                    for sh in all_sheets:
                        df_sheet = all_sheets[sh]
                        df_sheet.to_excel(writer, sheet_name=sh, index=False)
                reload_excel()
                st.success("Đã lưu ghi chú vào Excel.")
                st.rerun()
