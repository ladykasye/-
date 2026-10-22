#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电池充放电数据批量处理示例
============================

这个脚本解决的问题：仪器导出的 CSV 每次都要手动算容量保持率、库伦效率，
写成脚本后一次搞定，重复可用。

只用 Python 标准库，不需要安装 numpy / pandas / matplotlib。

用法:
    python 示例_CSV处理.py                    # 处理同目录下的 示例数据.csv
    python 示例_CSV处理.py 你的数据.csv        # 处理指定文件
"""

import csv
import os
import sys


# ----------------------------------------------------------------------
# 1. 读文件——重点是编码处理
# ----------------------------------------------------------------------
def 读数据(路径):
    """
    读取 CSV，自动尝试多种编码。

    为什么需要这个：国产仪器（蓝电、新威等）导出的文件常是 GBK 编码，
    直接用 UTF-8 打开会报 UnicodeDecodeError，或者中文列名变乱码。
    """
    for 编码 in ("utf-8-sig", "gbk", "utf-8"):
        try:
            with open(路径, "r", encoding=编码, newline="") as f:
                行列表 = list(csv.DictReader(f))
            print(f"  文件编码识别为: {编码}")
            return 行列表
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法识别 {路径} 的编码，请检查文件")


def 取数字(行, 列名):
    """从一行里取数值，空值或非法值返回 None。"""
    值 = (行.get(列名) or "").strip()
    if not 值:
        return None
    try:
        return float(值)
    except ValueError:
        return None


# ----------------------------------------------------------------------
# 2. 计算指标
# ----------------------------------------------------------------------
def 计算指标(行列表):
    循环, 放电, 充电 = [], [], []

    for 行 in 行列表:
        n = 取数字(行, "循环序号")
        d = 取数字(行, "放电容量(mAh/g)")
        c = 取数字(行, "充电容量(mAh/g)")
        if n is None or d is None:
            continue          # 跳过缺数据的行
        循环.append(int(n))
        放电.append(d)
        充电.append(c if c is not None else d)

    首圈 = 放电[0]
    末圈 = 放电[-1]
    保持率 = 末圈 / 首圈 * 100

    # 库伦效率 = 放电容量 / 充电容量，逐圈算再取平均
    效率列表 = [d / c * 100 for d, c in zip(放电, 充电) if c]
    平均效率 = sum(效率列表) / len(效率列表)

    # 每圈衰减率（线性估计）
    每圈衰减 = (首圈 - 末圈) / (len(放电) - 1)

    return {
        "圈数": len(放电),
        "首圈容量": 首圈,
        "末圈容量": 末圈,
        "最高容量": max(放电),
        "最低容量": min(放电),
        "容量保持率": 保持率,
        "平均库伦效率": 平均效率,
        "平均每圈衰减": 每圈衰减,
        "循环": 循环,
        "放电": 放电,
    }


# ----------------------------------------------------------------------
# 3. 纯文本画图（没有 matplotlib 也能看趋势）
# ----------------------------------------------------------------------
def 文本柱状图(循环, 放电, 宽=40):
    最小, 最大 = min(放电), max(放电)
    范围 = 最大 - 最小 or 1

    print("\n容量衰减趋势（每格约 %.1f mAh/g）" % (范围 / 宽))
    print("  " + "-" * (宽 + 20))

    for n, d in zip(循环, 放电):
        长度 = int((d - 最小) / 范围 * 宽)
        print(f"  {n:>3} |{'█' * 长度:<{宽}}| {d:.1f}")

    print("  " + "-" * (宽 + 20))


# ----------------------------------------------------------------------
# 4. 主流程
# ----------------------------------------------------------------------
def main():
    脚本目录 = os.path.dirname(os.path.abspath(__file__))
    路径 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(脚本目录, "示例数据.csv")

    if not os.path.exists(路径):
        print(f"找不到文件: {路径}")
        return 1

    print("=" * 58)
    print("电池充放电数据处理")
    print("=" * 58)
    print(f"数据文件: {os.path.basename(路径)}")

    行列表 = 读数据(路径)
    print(f"读到 {len(行列表)} 行")

    结果 = 计算指标(行列表)

    print()
    print("-" * 58)
    print("分析结果")
    print("-" * 58)
    print(f"  循环圈数        : {结果['圈数']}")
    print(f"  首圈放电容量    : {结果['首圈容量']:.1f} mAh/g")
    print(f"  末圈放电容量    : {结果['末圈容量']:.1f} mAh/g")
    print(f"  最高 / 最低     : {结果['最高容量']:.1f} / {结果['最低容量']:.1f} mAh/g")
    print(f"  容量保持率      : {结果['容量保持率']:.1f} %")
    print(f"  平均库伦效率    : {结果['平均库伦效率']:.2f} %")
    print(f"  平均每圈衰减    : {结果['平均每圈衰减']:.2f} mAh/g")

    文本柱状图(结果["循环"], 结果["放电"])

    print()
    print("提示: 装好 matplotlib 后就能出正式图表：")
    print("      pip install matplotlib")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())