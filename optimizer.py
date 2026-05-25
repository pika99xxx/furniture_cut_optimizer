# optimizer.py

from rectpack import newPacker

SHEET_W = 1206
SHEET_H = 2430

def expand_parts(df):
    parts = []

    for _, row in df.iterrows():
        qty = int(row["数量"])

        for i in range(qty):
            parts.append({
                "id": f'{row["部件名称"]}_{i + 1}',
                "name": row["部件名称"],
                "w": int(row["宽度mm"]),
                "h": int(row["长度mm"]),
                "grain": row["木纹组"],
                "thickness": row["厚度mm"],
                "material": row["材质"],
                "can_rotate": str(row["是否可旋转"]).strip() in ["是", "yes", "Y", "y", "1", "True"]
            })

    return parts


def optimize_group(parts, kerf=3):
    """
    parts: 同一木纹组 / 同一厚度 / 同一材质的板件
    kerf: 锯缝，默认 3mm
    """

    packer = newPacker(rotation=True)

    for p in parts:
        w = p["w"] + kerf
        h = p["h"] + kerf

        # 如果不可旋转，则 rectpack 本身不好单独控制
        # 第一版先通过 rotation=True 做快速 MVP
        # 第二版再改成自研 MaxRects 支持单件旋转控制
        packer.add_rect(w, h, rid=p["id"])

    # 先预设最多 50 张原材料板
    for i in range(50):
        packer.add_bin(SHEET_W, SHEET_H)

    packer.pack()

    result = []
    used_bins = set()

    for abin in packer:
        bin_index = abin.bid
        for rect in abin:
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            rid = rect.rid

            original = next(p for p in parts if p["id"] == rid)

            result.append({
                "sheet_index": bin_index + 1,
                "part_id": rid,
                "part_name": original["name"],
                "x": x,
                "y": y,
                "w": w - kerf,
                "h": h - kerf,
                "w_with_kerf": w,
                "h_with_kerf": h,
                "grain": original["grain"],
                "material": original["material"],
                "thickness": original["thickness"]
            })

            used_bins.add(bin_index + 1)

    return result


def calculate_stats(layout):
    sheet_area = SHEET_W * SHEET_H
    stats = []

    sheet_ids = sorted(set([x["sheet_index"] for x in layout]))

    for sid in sheet_ids:
        items = [x for x in layout if x["sheet_index"] == sid]
        used_area = sum(x["w"] * x["h"] for x in items)
        utilization = used_area / sheet_area * 100

        max_x = max(x["x"] + x["w_with_kerf"] for x in items)
        max_y = max(x["y"] + x["h_with_kerf"] for x in items)

        stats.append({
            "sheet_index": sid,
            "used_area": used_area,
            "sheet_area": sheet_area,
            "utilization": round(utilization, 2),
            "main_remain_width": SHEET_W - max_x,
            "main_remain_length": SHEET_H - max_y
        })

    return stats