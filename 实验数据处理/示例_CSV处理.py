#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电池充放电数据批量处理 + 出图
================================

这个脚本解决的问题：仪器导出的 CSV 每次都要手动算容量保持率、库伦效率，
写成脚本后一次搞定，重复可用。

需要: numpy, pandas, matplotlib
    pip install numpy pandas matplotlib

用法:
    python 示例_CSV处理.py                    # 处理同目录下的 示例数据.csv
    python 示例_CSV处理.py 你的数据.csv        # 处理指定文件
"""

import os
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")            # 不弹窗，直接存文件（服务器/脚本环境友好）
import matplotlib.pyplot as plt


# ----------------------------------------------------------------------
# 0. 中文显示配置——Windows 上不做这一步，图里中文会变成方框
# ----------------------------------------------------------------------
def 设置中文字体():
    """
    matplotlib 默认字体不含中文，必须显式指定。

    Microsoft YaHei（微软雅黑）Win10/11 都有，放在最前面。
    axes.unicode_minus = False 是为了让负号正常显示（否则负号也会变方框）。
    """
    matplotlib.rcParams["font.sans-serif"] = [
        "Microsoft YaHei", "SimHei", "DejaVu Sans",
    ]
    matplotlib.rcParams["axes.unicode_minus"] = False
    print("  中文字体已配置: Microsoft YaHei")


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
            df = pd.read_csv(路径, encoding=编码)
            print(f"  文件编码识别为: {编码}")
            return df
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法识别 {路径} 的编码，请检查文件")


def 清理数据(df):
    """统一列名、去掉缺数据的行。"""
    期望列 = ["循环序号", "放电容量(mAh/g)", "充电容量(mAh/g)"]

    缺失 = [c for c in 期望列 if c not in df.columns]
    if 缺失:
        raise RuntimeError(
            f"缺少列: {缺失}\n实际列名: {list(df.columns)}\n"
            f"请把列名改成: {期望列}"
        )

    df = df[期望列].copy()
    df = df.apply(pd.to_numeric, errors="coerce")   # 非数字变成 NaN
    df = df.dropna(subset=["循环序号", "放电容量(mAh/g)"])
    return df.sort_values("循环序号").reset_index(drop=True)


# ----------------------------------------------------------------------
# 2. 计算指标
# ----------------------------------------------------------------------
def 计算指标(df):
    循环 = df["循环序号"].to_numpy()
    放电 = df["放电容量(mAh/g)"].to_numpy()
    充电 = df["充电容量(mAh/g)"].fillna(df["放电容量(mAh/g)"]).to_numpy()

    首圈, 末圈 = 放电[0], 放电[-1]
    保持率 = 末圈 / 首圈 * 100
    平均效率 = float(np.mean(放电 / 充电) * 100)
    每圈衰减 = (首圈 - 末圈) / max(len(放电) - 1, 1)

    return {
        "圈数": len(放电),
        "首圈容量": 首圈,
        "末圈容量": 末圈,
        "最高容量": float(放电.max()),
        "最低容量": float(放电.min()),
        "容量保持率": 保持率,
        "平均库伦效率": 平均效率,
        "平均每圈衰减": 每圈衰减,
        "循环": 循环,
        "放电": 放电,
        "充电": 充电,
    }


# ----------------------------------------------------------------------
# 3. 出图
# ----------------------------------------------------------------------
def 画图(结果, 输出路径):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))

    # 左图：容量-循环曲线
    ax1.plot(结果["循环"], 结果["放电"], "o-", color="#1f77b4",
             markersize=3.5, linewidth=1.6, label="放电容量")
    ax1.plot(结果["循环"], 结果["充电"], "s--", color="#ff7f0e",
             markersize=3.0, linewidth=1.3, label="充电容量")
    ax1.set_xlabel("循环序号")
    ax1.set_ylabel("比容量 (mAh/g)")
    ax1.set_title("充放电容量-循环曲线")
    ax1.legend()
    ax1.grid(alpha=0.3)

    # 右图：库伦效率
    效率 = 结果["放电"] / 结果["充电"] * 100
    ax2.plot(结果["循环"], 效率, "^-", color="#2ca02c",
             markersize=3.5, linewidth=1.6)
    ax2.axhline(100, color="gray", linestyle=":", linewidth=1)
    ax2.set_xlabel("循环序号")
    ax2.set_ylabel("库伦效率 (%)")
    ax2.set_title(f"库伦效率（平均 {结果['平均库伦效率']:.2f}%）")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(输出路径, dpi=200)
    plt.close(fig)
    print(f"  图表已保存: {os.path.basename(输出路径)}")


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

    设置中文字体()
    df = 清理数据(读数据(路径))
    print(f"有效数据: {len(df)} 圈")

    结果 = 计算指标(df)

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

    画图(结果, os.path.join(脚本目录, "充放电曲线.png"))

    # 同时导出汇总表，方便贴进实验报告
    汇总 = pd.DataFrame([{
        "循环圈数": 结果["圈数"],
        "首圈容量(mAh/g)": round(结果["首圈容量"], 2),
        "末圈容量(mAh/g)": round(结果["末圈容量"], 2),
        "容量保持率(%)": round(结果["容量保持率"], 2),
        "平均库伦效率(%)": round(结果["平均库伦效率"], 2),
        "平均每圈衰减(mAh/g)": round(结果["平均每圈衰减"], 3),
    }])
    汇总路径 = os.path.join(脚本目录, "汇总结果.xlsx")
    汇总.to_excel(汇总路径, index=False)
    print(f"  汇总表已保存: {os.path.basename(汇总路径)}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())