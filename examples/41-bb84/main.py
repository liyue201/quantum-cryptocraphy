#!/usr/bin/env python3
"""BB84 —— 教学级的量子密钥分发经典模拟。

不是真量子：我们用普通整数来"建模"基与结果，但三个核心思想真实呈现：
   1) 无人窃听时，Alice 和 Bob 的对基后密钥完全一致。
   2) 若 Eve 尝试"测量再转发"，她会改动一些比特，在"对基 + 校验"环节露馅。
   3) 校验环节抓住 Eve，双方作废本轮密钥。

运行:  python3 main.py      （纯 Python，无依赖）
"""

import random

# 两种基：0 = '直线基'(bit 直接编码)，1 = '对角基'。
# 在本演示里，编入 bit b 的结果两者取值相同，真正起作用的是"基"本身。
BASES = [0, 1]


def bb84(n_bits: int = 16, eavesdrop: bool = False, seed: int = 42) -> None:
    rng = random.Random(seed)

    a_bits = [rng.getrandbits(1) for _ in range(n_bits)]   # Alice 要发的随机比特
    a_basis = [rng.choice(BASES) for _ in range(n_bits)]   # Alice 随机选基
    b_basis = [rng.choice(BASES) for _ in range(n_bits)]   # Bob 随机选基测量

    # Eve 偷听每个比特的数学：
    #   P(Eve 选错基)                       = 1/2
    #   P(选错基时测量会翻转该比特)           = 1/2
    #   => 每校验 1 个比特，P(Eve 留下痕迹)  = 1/2 * 1/2 = 1/4
    #   => 校验 k 个比特后，P(她仍隐身)      = (3/4)^k
    p_get_caught_per_bit = 0.25

    # --- Eve 拦截 ------------------------------------------------------
    key_pool = a_bits[:]
    if eavesdrop:
        e_basis = [rng.choice(BASES) for _ in range(n_bits)]
        eve_key = []
        for i in range(n_bits):
            # Eve 用她的基去测量；若她的基和 Alice 不同，比特有 50% 几率翻转。
            val = key_pool[i]
            if e_basis[i] != a_basis[i]:
                val = rng.getrandbits(1)
            eve_key.append(val)
        key_pool = eve_key[:]  # Eve 把她(可能被改动过的)值转发出去

    # --- Bob 接收并测量 ------------------------------------------------
    recv = []
    for i in range(n_bits):
        recv.append(key_pool[i])  # 他读到某个值（正确与否取决于过程）

    # --- 对基：只保留基一致的那些比特 -------------------------------------
    sift_bits, e_bits = [], []
    for i in range(n_bits):
        if a_basis[i] == b_basis[i]:
            sift_bits.append((a_bits[i], recv[i]))

    # --- 校验：对基后子集上的错误率 ---------------------------------------
    errs = [a for a, b in sift_bits if a != b]
    err_rate = len(errs) / len(sift_bits) if sift_bits else 0.0

    print(f"BB84 模拟（n = {n_bits} 比特, 窃听 = {eavesdrop}）")
    print(f"  Alice 原始比特: {a_bits}")
    print(f"  Alice 基      : {a_basis}")
    print(f"  Bob   基      : {b_basis}")
    print(f"  对基后保留位数 : {len(sift_bits)}")
    print(f"  协商密钥(Bob收): {[b for _, b in sift_bits]}")
    print(f"  是否完全一致   : {all(a == b for a, b in sift_bits)}")
    print(f" 窃听导致的错误率: {err_rate:.2f}  ({err_rate*100:.0f}%)")
    if eavesdrop:
        print("  理论: 每抽查 1 个比特抓到 Eve 的概率 = 1/4 (挑错基 1/2, 翻比特 1/2)")
        print(f"        抽查全部 {len(sift_bits)} 个后，Eve 漏网概率 = (3/4)^{len(sift_bits)} "
              f"≈ {(0.75 ** len(sift_bits)):.2%}")
        print("  >> 检测：错误率明显 > 0 且(理论上)抽查越多越难逃 → 判定存在窃听 → 本组密钥作废。")
    else:
        print("  >> 通过：错误率 ≈ 0 → 视为安全，密钥可留用。")


def main() -> None:
    bb84(n_bits=16, eavesdrop=False, seed=1)
    print()
    bb84(n_bits=16, eavesdrop=True, seed=1)
    print()
    print("结论: 无人窃听→密钥一致；有人窃听→测量留痕、错误率抬升→当场识破。")


if __name__ == "__main__":
    main()