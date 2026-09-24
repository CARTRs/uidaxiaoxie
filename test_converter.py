# -*- coding: utf-8 -*-
"""转换逻辑测试用例"""
from converter import to_chinese, parse_chinese, auto_convert

# (输入, upper, money, 期望输出)
CASES = [
    # --- 基础整数 ---
    ("0", False, False, "零"),
    ("1", False, False, "一"),
    ("10", False, False, "十"),
    ("11", False, False, "十一"),
    ("20", False, False, "二十"),
    ("100", False, False, "一百"),
    ("101", False, False, "一百零一"),
    ("110", False, False, "一百一十"),
    ("1000", False, False, "一千"),
    ("1005", False, False, "一千零五"),
    ("1010", False, False, "一千零一十"),
    ("10000", False, False, "一万"),
    ("10001", False, False, "一万零一"),
    ("10010", False, False, "一万零一十"),
    ("10100", False, False, "一万零一百"),
    ("11000", False, False, "一万一千"),
    ("100000", False, False, "十万"),
    ("1000000", False, False, "一百万"),
    ("10000000", False, False, "一千万"),
    ("100000000", False, False, "一亿"),
    ("100000001", False, False, "一亿零一"),
    ("100010000", False, False, "一亿零一万"),
    ("1000000000", False, False, "十亿"),
    ("1234567890", False, False, "十二亿三千四百五十六万七千八百九十"),
    ("1000000000000", False, False, "一万亿"),
    # --- 小数 ---
    ("0.5", False, False, "零点五"),
    ("1.23", False, False, "一点二三"),
    ("1234.56", False, False, "一千二百三十四点五六"),
    ("0.05", False, False, "零点零五"),
    # --- 负数 ---
    ("-1", False, False, "负一"),
    ("-100", False, False, "负一百"),
    ("-0.5", False, False, "负零点五"),
    # --- 大写整数 ---
    ("1", True, False, "壹"),
    ("10", True, False, "壹拾"),
    ("100", True, False, "壹佰"),
    ("101", True, False, "壹佰零壹"),
    ("1000000", True, False, "壹佰万"),
    ("1234567890", True, False, "壹拾贰亿叁仟肆佰伍拾陆万柒仟捌佰玖拾"),
    # --- 金额大写 ---
    ("0", True, True, "零元整"),
    ("1", True, True, "壹元整"),
    ("10", True, True, "壹拾元整"),
    ("100", True, True, "壹佰元整"),
    ("1234.56", True, True, "壹仟贰佰叁拾肆元伍角陆分"),
    ("100.05", True, True, "壹佰元零伍分"),
    ("100.5", True, True, "壹佰元伍角"),
    ("0.5", True, True, "零元伍角"),
    ("0.05", True, True, "零元零伍分"),
    ("10000", True, True, "壹万元整"),
    ("-520.13", True, True, "负伍佰贰拾元壹角叁分"),
    # --- 金额小写 ---
    ("1234.56", False, True, "一千二百三十四元五角六分"),
    ("100.05", False, True, "一百元零五分"),
]

# 反向解析测试
PARSE_CASES = [
    ("一", "1"),
    ("十", "10"),
    ("一百零一", "101"),
    ("壹仟贰佰叁拾肆元伍角陆分", "1234.56"),
    ("壹佰元零伍分", "100.05"),
    ("负伍佰贰拾元壹角叁分", "-520.13"),
    ("一千二百三十四点五六", "1234.56"),
    ("一亿零一", "100000001"),
    ("壹拾", "10"),
]


def main():
    passed = failed = 0
    print("=" * 70)
    print("正向转换测试")
    print("=" * 70)
    for inp, up, mo, expect in CASES:
        try:
            got = to_chinese(inp, upper=up, money=mo)
        except Exception as e:
            got = f"<异常: {e}>"
        tag = "大写" if up else "小写"
        fmt = "金额" if mo else "普通"
        if got == expect:
            passed += 1
            print(f"  [OK]   {inp:>14} [{tag}/{fmt}] -> {got}")
        else:
            failed += 1
            print(f"  [FAIL] {inp:>14} [{tag}/{fmt}] -> {got}   (期望: {expect})")

    print()
    print("=" * 70)
    print("反向解析测试")
    print("=" * 70)
    for inp, expect in PARSE_CASES:
        try:
            got = parse_chinese(inp)
        except Exception as e:
            got = f"<异常: {e}>"
        if got == expect:
            passed += 1
            print(f"  [OK]   {inp:>24} -> {got}")
        else:
            failed += 1
            print(f"  [FAIL] {inp:>24} -> {got}   (期望: {expect})")

    print()
    print("=" * 70)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 70)
    return failed


if __name__ == "__main__":
    import sys
    sys.exit(1 if main() else 0)
