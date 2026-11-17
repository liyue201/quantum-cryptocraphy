#!/usr/bin/env python3
"""对密码学重要的两个量子特性：
  1) 测量坍缩 —— 不可逆的、真正随机的抽取。
  2) 纠缠 —— 两个量子比特共享同一个命运，它们始终一致。

运行:  pip install qiskit qiskit-aer && python3 main.py
"""

from collections import Counter

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector


def show_state(title: str, circ: QuantumCircuit) -> None:
    """Print exact probabilities of each basis state (before collapse)."""
    n = circ.num_qubits
    sv = Statevector.from_int(0, 2 ** n).evolve(circ)
    # 按规范的基态标签整理概率，让纠缠态正确显示为 |00> 与 |11>（而不是 |00> 与 |10>）
    probs = {}
    for b in range(2 ** n):
        p = float(abs(sv[b]) ** 2)
        if p:  # 只列出实际存在的基态
            probs[f"|{b:0{n}b}>"] = round(p, 2)
    print(f"[{title}] 测量前状态概率: {probs}")


def sample(title: str, circ: QuantumCircuit, shots: int = 256) -> Counter:
    """Measure the circuit `shots` times and return an outcome histogram."""
    n = circ.num_qubits
    measured = circ.measure_all(inplace=False)
    counts = AerSimulator().run(measured, shots=shots).result().get_counts()
    # 把结果的键统一成固定宽度，例如 '00'
    fixed = Counter({f"{k.zfill(n)}": v for k, v in counts.items()})
    print(f"[{title}] 测量 {shots} 次统计: {dict(sorted(fixed.items()))}")
    return fixed


# ---- 实验一：叠加，然后坍缩成一次随机抽取 ----
q1 = QuantumCircuit(2)   # 参数 2 = 电路里有 2 个量子比特（准备好 2 根线，初始都是 |0>）
q1.h(0)                  # 参数 0 = 在第 0 号线贴上哈达玛门 H（把它推进叠加态）
q1.h(1)                  # 参数 1 = 在第 1 号线贴上 H（也进入叠加）→ 两条线都是半 0 半 1
show_state("实验一 两根叠加", q1)
sample("实验一 测量坍缩", q1)

print()

# ---- 实验二：用 CNOT 把它们纠缠成 Bell 态 ----
q2 = QuantumCircuit(2)   # 同样是 2 个量子比特
q2.h(0)                  # 先让第 0 号线进入叠加态
q2.cx(0, 1)              # CNOT(控制线, 目标线)：当第 0 号线是 1 时翻转第 1 号线 → 两条线被"焊"成纠缠(Bell 态)
show_state("实验二 加 CNOT 纠缠", q2)
sample("实验二 测量纠缠", q2)