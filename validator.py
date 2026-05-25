# validator.py

SHEET_W = 1206
SHEET_H = 2430

def validate_part(part):
    errors = []

    name = part["部件名称"]
    length = int(part["长度mm"])
    width = int(part["宽度mm"])

    # 最大尺寸校验，允许长宽互调
    if not (
        (length <= SHEET_H and width <= SHEET_W) or
        (length <= SHEET_W and width <= SHEET_H)
    ):
        errors.append(f"{name} 超过原材料最大尺寸 1206×2430mm")

    # 最小封边尺寸校验
    if length < 50 or width < 50:
        errors.append(f"{name} 小于最小可加工尺寸 50mm")

    if width == 50 and length <= 200:
        errors.append(f"{name} 宽度为50mm时，长度建议大于200mm")

    return errors