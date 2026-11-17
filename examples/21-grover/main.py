#!/usr/bin/env python3
"""在 n=2 的量子比特上做 Grover 搜索：先撒开均匀叠加、用 oracle 标记目标，
再做‘幅度放大’把目标抬到接近 1。
对照：经典从 N 项中找目标平均要约试 N/2 次，Grover 只需约 sqrt(N) 次。

运行:  pip install qiskit qiskit-aer && python3 main.py
"""

from collections import Counter
from math import pi

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

N = 2
TARGET = 3  # 二进制 '11' —— 我们要搜索的标记基态


def oracle(n: int, target: int) -> QuantumCircuit:
    """构造一个‘给目标基态翻相位’的电路（oracle，黑盒）。"""
    circ = QuantumCircuit(n)
    for q in range(n):
        # 把小端序的测量顺序，转成我们真正指的二进制位。
        bit = (target >> (n - 1 - q)) & 1
        if bit == 0:
            circ.x(q)  # 是 0 的位置先 X 一下，便于统一作用到 |11>
    circ.mcp(pi, list(range(n - 1)), n - 1)  # 多控相位翻转门（翻转 pi 相位）
    for q in range(n):
        bit = (target >> (n - 1 - q)) & 1
        if bit == 0:
            circ.x(q)  # 执行完再 X 回来
    return circ


def diffusion(n: int) -> QuantumCircuit:
    """幅度放大算符：绕‘均值’反演的扩散门。"""
    circ = QuantumCircuit(n)
    circ.h(range(n))   # H 作用到所有线
    circ.x(range(n))   # 全部取反
    circ.h(n - 1)
    circ.mcp(pi, list(range(n - 1)), n - 1)  # 对最后一个比特做受控相位翻转
    circ.h(n - 1)
    circ.x(range(n))   # 再取反回来
    circ.h(range(n))
    return circ


# 完整 Grover 电路：均匀叠加 -> 交替施加 oracle + 扩散 k 次。
# 理想迭代次数 = ceil(pi/4 * sqrt(N))。对 N=4 约 2 轮，
# 理论能把目标态抬到接近 100%。
k = max(round(3.14159 / 4 * (2 ** (N / 2))), 1)  # 约 sqrt(N) 次迭代
circ = QuantumCircuit(N)
circ.h(range(N))          # 第 1 步：把全部 4 个候选都做成均匀叠加
for _ in range(k):
    circ.compose(oracle(N, TARGET), inplace=True)     # 第 2 步：oracle 标记目标
    circ.compose(diffusion(N), inplace=True)          # 第 3 步：扩散放大幅度
circ.measure_all()        # 测量所有比特

counts = AerSimulator().run(circ, shots=1024).result().get_counts()
fixed = Counter({f"{k.zfill(N)}": v for k, v in counts.items()})
total = sum(fixed.values())
found = fixed.get(f"{TARGET:0{N}b}", 0)

print(f"目标态: |{TARGET:0{N}b}>")
print(f"候选总数 N       = {2**N}")
print(f"经典平均试探次数   = ~{2**N // 2}")
print(f"Grover 迭代次数 k = {k}（约 √N = {2 ** (N / 2):.2f}）")
print()
print(f"测量 {total} 次统计: {dict(sorted(fixed.items()))}")
print(f"命中目标占比       = {found}/{total} = {found/total*100:.1f}%")
print("结论: Grover 把命中概率从 1/N 抬到接近 1，且只需约 √N 步。")