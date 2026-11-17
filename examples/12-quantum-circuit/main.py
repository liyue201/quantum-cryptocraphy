#!/usr/bin/env python3
"""量子电路入门：搭一个微型电路，打印它的 ASCII 电路图，再运行
得到 Bell 态的统计结果（00 约 1/2，11 约 1/2）。

使用 Python + Qiskit。
"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def main() -> None:
    print("=" * 62)
    print("三零件: 比特(线) + 门(方块) + 测量(仪表)")
    print("=" * 62)

    # --- 1) 构建电路 ------------------------------------------------------
    qc = QuantumCircuit(2, 2)     # 参数 2,2 = 2 个量子比特 + 2 个经典寄存器
    qc.h(0)          # h(0) = 哈达玛门，作用在第 0 号线 -> 让它进入叠加态
    qc.cx(0, 1)      # cx(控制线0, 目标线1)：当 q0=1 时翻转 q1 -> 纠缠成 Bell 态
    qc.measure([0, 1], [0, 1])  # measure(量子线, 经典寄存器)：把 0、1 号线的结果记入寄存器

    # --- 2) 把电路画成 ASCII 图 ------------------------------------------
    print("电路图 (时间从左到右，每根线 = 一个量子比特):\n")
    print(qc.draw("text"))

    # --- 3) 运行并给出统计 ------------------------------------------------
    shots = 2048
    sim = AerSimulator()
    tqc = transpile(qc, sim)
    counts = sim.run(tqc, shots=shots).result().get_counts()

    print(f"\n运行 {shots} 次，结果分布:")
    for k, v in sorted(counts.items()):
        print(f"     {k}: {v:5d}  ({v/shots*100:.1f}%)")
    print("\n>> 只出现 00 与 11，且约各半 —— 这就是 CNOT 制造的纠缠(Bell 态)。")


if __name__ == "__main__":
    main()