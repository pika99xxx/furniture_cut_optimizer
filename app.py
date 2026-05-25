# app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from optimizer import expand_parts, optimize_group, calculate_stats, SHEET_W, SHEET_H
from validator import validate_part

st.set_page_config(page_title="板式家具智能切割排版工具", layout="wide")

st.title("板式家具智能切割排版工具")
st.caption("原材料板尺寸：1206mm × 2430mm，支持按木纹组分组排版")

input_mode = st.radio("请选择输入方式", ["上传 Excel", "手动输入"])

df = None

if input_mode == "上传 Excel":
    uploaded_file = st.file_uploader("上传板件清单 Excel", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.subheader("板件清单")
        st.dataframe(df)

else:
    st.subheader("手动输入板件")

    if "manual_parts" not in st.session_state:
        st.session_state.manual_parts = []

    with st.form("part_form"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            grain = st.text_input("木纹组", value="A")
            name = st.text_input("部件名称", value="侧板")

        with col2:
            length = st.number_input("长度mm", min_value=1, value=780)
            width = st.number_input("宽度mm", min_value=1, value=400)

        with col3:
            qty = st.number_input("数量", min_value=1, value=2)
            thickness = st.number_input("厚度mm", min_value=1, value=15)

        with col4:
            material = st.text_input("材质", value="MDF")
            can_rotate = st.selectbox("是否可旋转", ["否", "是"])

        submitted = st.form_submit_button("添加板件")

        if submitted:
            st.session_state.manual_parts.append({
                "木纹组": grain,
                "部件名称": name,
                "长度mm": length,
                "宽度mm": width,
                "数量": qty,
                "厚度mm": thickness,
                "材质": material,
                "是否可旋转": can_rotate
            })

    if st.session_state.manual_parts:
        df = pd.DataFrame(st.session_state.manual_parts)
        st.dataframe(df)

        if st.button("清空手动输入"):
            st.session_state.manual_parts = []
            st.rerun()


kerf = st.sidebar.number_input("锯缝 kerf / mm", min_value=0, value=3)
trim = st.sidebar.number_input("修边预留 / mm", min_value=0, value=0)

if df is not None and st.button("开始自动排版"):
    st.subheader("工艺校验")

    all_errors = []

    for _, row in df.iterrows():
        errors = validate_part(row)
        all_errors.extend(errors)

    if all_errors:
        for err in all_errors:
            st.error(err)
    else:
        st.success("基础尺寸校验通过")

    parts = expand_parts(df)

    all_layout = []

    grouped = {}

    for p in parts:
        key = (p["grain"], p["material"], p["thickness"])
        grouped.setdefault(key, []).append(p)

    for key, group_parts in grouped.items():
        grain, material, thickness = key
        st.markdown(f"## 木纹组 {grain} / 材质 {material} / 厚度 {thickness}mm")

        layout = optimize_group(group_parts, kerf=kerf)
        stats = calculate_stats(layout)

        all_layout.extend(layout)

        stats_df = pd.DataFrame(stats)
        st.dataframe(stats_df)

        for sheet in stats:
            sheet_id = sheet["sheet_index"]
            items = [x for x in layout if x["sheet_index"] == sheet_id]

            st.markdown(f"### 第 {sheet_id} 张板｜利用率 {sheet['utilization']}%")

            fig, ax = plt.subplots(figsize=(3, 6))

            ax.set_xlim(0, SHEET_W)
            ax.set_ylim(0, SHEET_H)
            ax.set_aspect("equal")
            ax.invert_yaxis()

            # 原材料板外框
            board = plt.Rectangle((0, 0), SHEET_W, SHEET_H, fill=False, linewidth=2)
            ax.add_patch(board)

            for item in items:
                rect = plt.Rectangle(
                    (item["x"], item["y"]),
                    item["w"],
                    item["h"],
                    fill=False,
                    linewidth=1
                )
                ax.add_patch(rect)

                ax.text(
                    item["x"] + item["w"] / 2,
                    item["y"] + item["h"] / 2,
                    f'{item["part_name"]}\n{item["w"]}×{item["h"]}',
                    ha="center",
                    va="center",
                    fontsize=7
                )

            ax.set_title(f"Sheet {sheet_id} - {SHEET_W}×{SHEET_H}mm")
            ax.set_xlabel("Width / mm")
            ax.set_ylabel("Length / mm")

            st.pyplot(fig)

        layout_df = pd.DataFrame(all_layout)

st.subheader("3. 切割坐标明细")
st.dataframe(layout_df)

csv_data = layout_df.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "下载切割坐标 CSV",
    csv_data,
    file_name="cutting_layout.csv",
    mime="text/csv",
    key="download_cutting_layout_csv"
)
