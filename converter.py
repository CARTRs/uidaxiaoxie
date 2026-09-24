# -*- coding: utf-8 -*-
"""
数字大小写转换核心模块

支持：
    - 阿拉伯数字 -> 中文小写（一二三...）
    - 阿拉伯数字 -> 中文大写（壹贰叁...，财务金额写法）
    - 中文小写/大写 -> 阿拉伯数字（反向解析）
    - 负数、小数（角分）、万亿级大数
"""

# 中文小写数字
LOWER_DIGITS = "零一二三四五六七八九"
# 中文大写数字
UPPER_DIGITS = "零壹贰叁肆伍陆柒捌玖"

# 小写单位
LOWER_UNITS = ["", "十", "百", "千"]
# 大写单位（元以内）
UPPER_UNITS = ["", "拾", "佰", "仟"]

# 节权位（万、亿、万亿...）
LOWER_SECTIONS = ["", "万", "亿", "万亿", "亿亿"]
UPPER_SECTIONS = ["", "万", "亿", "万亿", "亿亿"]

# 货币单位
LOWER_MONEY = ("元", "角", "分")
UPPER_MONEY = ("元", "角", "分")

# 用于反向解析的映射表
_LOWER_CHAR_MAP = {
    "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    "壹": 1, "贰": 2, "叁": 3, "肆": 4, "伍": 5,
    "陆": 6, "柒": 7, "捌": 8, "玖": 9,
}
_UNIT_MAP = {
    "十": 10, "拾": 10, "百": 100, "佰": 100,
    "千": 1000, "仟": 1000,
}
_SECTION_MAP = {"万": 10 ** 4, "亿": 10 ** 8}


def _clean_digits(digit_str, digits_charset, units, sections):
    """把一个整数部分字符串（纯数字）转换为中文读法。

    Args:
        digit_str: 例如 "1005"
        digits_charset: "零一二三..." 或 "零壹贰叁..."
        units: ["", "十", "百", "千"] 或大写版本
        sections: ["", "万", "亿", ...]

    Returns:
        中文读法字符串，例如 "一千零五"
    """
    if not digit_str:
        return ""
    digit_str = digit_str.lstrip("0")
    if not digit_str:
        return digits_charset[0]

    zero = digits_charset[0]
    length = len(digit_str)

    # 按 4 位从右往左切分成节：低位在前
    chunks = []
    idx = length
    while idx > 0:
        start = max(0, idx - 4)
        chunks.append(digit_str[start:idx])
        idx = start
    # chunks[0] 是最低节，chunks[-1] 是最高节

    out = []
    for i in range(len(chunks) - 1, -1, -1):
        chunk = chunks[i]
        section_unit = sections[i] if i < len(sections) else ""
        chunk_text = _read_four(chunk, digits_charset, units)

        if chunk_text == "":
            # 整节为 0：只有当后面还有非零节时才补一个「零」，且不重复补
            if i > 0 and any(c.strip("0") for c in chunks[:i]):
                if out and not out[-1].endswith(zero):
                    out.append(zero)
            continue

        # 非最高节：若本节数值小于 1000（即节内高位是 0），说明需要补「零」。
        # 注意 chunk 是原始补位字符串（如 "0001"），用有效位数判断。
        effective_len = len(chunk.lstrip("0"))
        if i < len(chunks) - 1 and effective_len < 4:
            if out and not out[-1].endswith(zero):
                out.append(zero)

        out.append(chunk_text + section_unit)

    result = "".join(out)
    # 合并连续重复的零
    while zero * 2 in result:
        result = result.replace(zero * 2, zero)
    result = result.strip(zero)
    # 小写习惯：开头的「一十」省略为「十」（如 10 -> 十、15 -> 十五）
    if digits_charset == LOWER_DIGITS and result.startswith("一十"):
        result = result[1:]
    return result


def _read_four(chunk, digits_charset, units):
    """读取 4 位以内的数字块，例如 "1005" -> "一千零五"，"0010" -> "一十"。

    注意：这里不做节内前导零补位，由外层处理。
    「一十」-> 「十」的省略规则由 _clean_digits 在整体拼接后统一处理。
    """
    chunk = chunk.lstrip("0")
    if not chunk:
        return ""
    n = len(chunk)
    out = []
    zero_pending = False
    for i, ch in enumerate(chunk):
        d = int(ch)
        unit_index = n - i - 1
        if d == 0:
            zero_pending = True
        else:
            if zero_pending and out:
                out.append(digits_charset[0])
            zero_pending = False
            out.append(digits_charset[d] + units[unit_index])
    return "".join(out)


def _normalize_number(number):
    """把输入统一成 (符号, 整数部分字符串, 小数部分字符串)。

    Returns:
        (sign, int_str, frac_str)  例如 ("-", "123", "45")
    """
    if isinstance(number, str):
        s = number.strip().replace(",", "").replace("，", "")
    else:
        s = str(number)

    sign = ""
    if s.startswith("-") or s.startswith("负"):
        sign = "-"
        s = s.lstrip("-").lstrip("负")
    elif s.startswith("+"):
        s = s[1:]

    if "." in s:
        int_part, frac_part = s.split(".", 1)
    else:
        int_part, frac_part = s, ""

    int_part = int_part or "0"
    return sign, int_part, frac_part


def to_chinese(number, upper=False, money=False, with_liang=False):
    """把阿拉伯数字转换为中文读法。

    Args:
        number: 数字或数字字符串，例如 1234.56, "-100", "1000000"
        upper: True 表示用大写（壹贰叁），False 用小写（一二三）
        money: True 表示按金额格式输出（元角分），小数最多保留 2 位
        with_liang: 小写模式下是否用「两」（仅用于「2」在节首的场景，默认关闭）

    Returns:
        中文读法字符串
    """
    digits_charset = UPPER_DIGITS if upper else LOWER_DIGITS
    units = UPPER_UNITS if upper else LOWER_UNITS
    sections = UPPER_SECTIONS if upper else LOWER_SECTIONS

    sign, int_str, frac_str = _normalize_number(number)

    if money:
        # 金额模式：四舍五入到分
        from decimal import Decimal, ROUND_HALF_UP
        val = Decimal(f"{int_str}.{frac_str or '0'}")
        val = val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if val < 0:
            sign = "-"
        val = abs(val)
        int_str = str(int(val))
        frac_str = f"{val:.2f}".split(".")[1]

    # 整数部分
    if int_str.strip("0") == "":
        int_text = digits_charset[0]
    else:
        int_text = _clean_digits(int_str, digits_charset, units, sections)

    if not money:
        # 普通模式
        if frac_str.strip("0") == "":
            result = int_text
        else:
            frac_text = "".join(digits_charset[int(c)] for c in frac_str)
            if int_text == digits_charset[0]:
                result = digits_charset[0] + "点" + frac_text
            else:
                result = int_text + "点" + frac_text
        return ("负" + result) if sign == "-" else result

    # 金额模式：元角分
    money_unit = UPPER_MONEY if upper else LOWER_MONEY
    yuan_unit, jiao_unit, fen_unit = money_unit

    jiao = int(frac_str[0]) if len(frac_str) > 0 else 0
    fen = int(frac_str[1]) if len(frac_str) > 1 else 0

    has_int = int_str.strip("0") != ""

    if not has_int and jiao == 0 and fen == 0:
        # 0.00 -> 零元整
        result = digits_charset[0] + yuan_unit + "整"
        return ("负" + result) if sign == "-" else result

    parts = []
    if has_int:
        parts.append(int_text + yuan_unit)
    else:
        parts.append(digits_charset[0] + yuan_unit)

    if jiao == 0 and fen == 0:
        result = "".join(parts) + "整"
    elif jiao == 0:
        # 如 100.05 -> 壹佰元零伍分；0.05 -> 零元零伍分
        parts.append(digits_charset[0])
        parts.append(digits_charset[fen] + fen_unit)
        result = "".join(parts)
    else:
        parts.append(digits_charset[jiao] + jiao_unit)
        if fen != 0:
            parts.append(digits_charset[fen] + fen_unit)
        result = "".join(parts)

    return ("负" + result) if sign == "-" else result


def parse_chinese(text):
    """把中文数字（小写或大写）解析回阿拉伯数字字符串。

    支持：整数、小数（点）、元角分金额、负/负号。
    返回字符串形式的阿拉伯数字。
    """
    if not text:
        raise ValueError("输入为空")

    s = text.strip().replace(" ", "")
    sign = ""
    if s.startswith("负"):
        sign = "-"
        s = s[1:]
    s = s.lstrip("负")

    # 金额格式：含有 元/角/分
    if any(u in s for u in ("元", "圆", "角", "分", "整")):
        return _parse_money(s, sign)

    # 含小数点
    if "点" in s:
        int_part, frac_part = s.split("点", 1)
        int_val = _parse_integer(int_part) if int_part else 0
        frac_digits = "".join(str(_LOWER_CHAR_MAP[c]) for c in frac_part if c in _LOWER_CHAR_MAP)
        return f"{sign}{int_val}.{frac_digits}" if frac_digits else f"{sign}{int_val}"

    return f"{sign}{_parse_integer(s)}"


def _parse_integer(text):
    """解析中文整数部分，返回 int。"""
    if not text:
        return 0
    text = text.replace("零", "")
    total = 0
    section = 0
    number = 0

    for ch in text:
        if ch in _LOWER_CHAR_MAP:
            number = _LOWER_CHAR_MAP[ch]
        elif ch in _UNIT_MAP:
            unit = _UNIT_MAP[ch]
            if number == 0:
                number = 1  # 处理「十」= 10、「拾伍」= 15
            section += number * unit
            number = 0
        elif ch in _SECTION_MAP:
            section += number
            total += section * _SECTION_MAP[ch]
            section = 0
            number = 0
        else:
            raise ValueError(f"无法识别的字符：{ch}")

    return total + section + number


def _parse_money(text, sign=""):
    """解析中文金额，返回字符串形式数字。"""
    text = text.rstrip("整")
    yuan = 0
    jiao = 0
    fen = 0

    if "元" in text or "圆" in text:
        sep = "元" if "元" in text else "圆"
        yuan_part, rest = text.split(sep, 1)
        yuan = _parse_integer(yuan_part) if yuan_part else 0
        if "角" in rest:
            jiao_part, rest = rest.split("角", 1)
            jiao = _LOWER_CHAR_MAP.get(jiao_part[-1], 0) if jiao_part else 0
        if "分" in rest:
            fen_part = rest.replace("分", "")
            fen = _LOWER_CHAR_MAP.get(fen_part[-1], 0) if fen_part else 0
    else:
        # 没有元，直接是角分
        if "角" in text:
            jiao_part, rest = text.split("角", 1)
            jiao = _LOWER_CHAR_MAP.get(jiao_part[-1], 0) if jiao_part else 0
        else:
            rest = text
        if "分" in rest:
            fen_part = rest.replace("分", "")
            fen = _LOWER_CHAR_MAP.get(fen_part[-1], 0) if fen_part else 0

    result = f"{yuan}.{jiao}{fen}"
    return f"{sign}{result}"


def auto_convert(text, upper=False, money=True):
    """智能转换：自动判断输入是阿拉伯数字还是中文数字，双向转换。

    Args:
        text: 输入文本
        upper: 阿拉伯数字 -> 中文时，是否使用大写
        money: 阿拉伯数字 -> 中文时，是否使用金额格式

    Returns:
        (结果字符串, 转换方向说明)
    """
    if not text or not text.strip():
        raise ValueError("输入为空")

    s = text.strip()
    # 判断是否为阿拉伯数字输入
    probe = s.replace(",", "").replace("，", "").lstrip("-+")
    is_arabic = bool(probe) and all(
        c.isdigit() or c == "." for c in probe
    ) and probe.count(".") <= 1

    if is_arabic:
        result = to_chinese(s, upper=upper, money=money)
        direction = "阿拉伯数字 → 中文" + ("大写" if upper else "小写") + ("（金额）" if money else "")
    else:
        result = parse_chinese(s)
        direction = "中文 → 阿拉伯数字"
    return result, direction


if __name__ == "__main__":
    # 简单自测
    cases = [
        ("0", False, False),
        ("10", False, False),
        ("100", False, False),
        ("1005", False, False),
        ("10000", False, False),
        ("100000001", False, False),
        ("1234.56", False, False),
        ("1234.56", True, True),
        ("1000000", True, False),
        ("-520.13", True, True),
    ]
    for num, up, mo in cases:
        print(f"{num!r:>14} upper={up} money={mo} -> {to_chinese(num, upper=up, money=mo)}")
