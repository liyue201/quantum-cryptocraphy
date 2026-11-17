#!/usr/bin/env python3
"""为什么量子会打破今天的密码学：叠加态的直觉。

一个量子比特初始为 |0>。测量它永远得到 0。
去掉下面 H(哈达玛)门的注释，把它推入 |0> 与 |1> 的等幅叠加，
测量就会变成约 50/50 的随机翻转。

运行:  pip install qiskit  &&  python3 main.py
"""

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def show(title: str, circ: QuantumCircuit) -> None:
    """打印测量前每个结果的精确概率。"""
    sv = Statevector.from_int(0, 2 ** circ.num_qubits).evolve(circ)
    # 把 numpy 浮点转成普通浮点并四舍五入，保证输出整洁。
    probs = {f"|{b:0{circ.num_qubits}b}>": round(float(p), 2)
             for b, p in enumerate(sv.probabilities_dict().values())}
    print(f"== {title} ==")
    print("  叠加到测量前的状态概率:", probs)
    print()


# 情形一：一根"干净"的比特——不加任何门。测量永远坍缩为 0。
q1 = QuantumCircuit(1, 1)   # 参数 1,1 = 该电路有 1 个量子比特和 1 个经典寄存器
show("从未加门：一个干净的量子比特", q1)

# 情形二：施加哈达玛门 H -> 进入 |0> 与 |1> 的等幅叠加。
# 去掉下一行的注释，就能看到"量子翻转"发生。
q2 = QuantumCircuit(1, 1)
q2.h(0)                      # h(0) = 把 H 门贴在第 0 号线上（参数 0 是线的编号）
show("加了哈达玛门 H：进入 50/50 叠加态", q2)

print("提示：这也正是你私钥出问题的根源——")
print("当信息能以叠加态存在，旧数学难题就有了被并行撬开的可能。")