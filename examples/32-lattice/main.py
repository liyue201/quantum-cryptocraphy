#!/usr/bin/env python3
"""品尝 LWE（带误差学习），它是 Kyber 背后的理论。

思路：一个秘密向量 s 和一个公开矩阵 A（做成 mod q 可逆）。
无噪声时，解 A*s = b 就是一个很快的线性方程求解并恢复出 s。
带微小噪声 e 时，朴素的线性求解就再找不到真正的 s 了——
解出来的整数 s' 会和真正的 s 严重偏离。正是这个偏离，
让 LWE 即使对量子计算机来说也依然难算。

最后给一个"Kyber 风味"的共享秘密小演练，体会 KEM 的精神。

运行:  python3 main.py      （纯 Python，用 numpy）
"""

import numpy as np


def mod_inv(a: int, q: int) -> int:
    """用扩展欧几里得求 a mod q 的模逆（q 为素数）。"""
    a %= q
    t, nt = 0, 1
    r, nr = q, a
    while nr:
        qq = r // nr
        r, nr = nr, r - qq * nr
        t, nt = nt, t - qq * nt
    return t % q


def solve_mod(A, b, q):
    """在模 Z/qZ 上用高斯消元解 A*s = b (mod q)。
    返回整数向量 s (mod q)。"""
    n = len(A)
    M = [[int(A[i][j]) % q for j in range(n)] + [int(b[i]) % q] for i in range(n)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if M[r][col] % q != 0), None)  # 选主元
        if pivot is None:
            continue
        M[col], M[pivot] = M[pivot], M[col]
        inv = mod_inv(M[col][col], q)  # 主元求逆，把主元归一
        for j in range(col, n + 1):
            M[col][j] = M[col][j] * inv % q
        for r in range(n):
            if r != col and M[r][col] % q != 0:  # 消去其它行的同列
                f = M[r][col]
                for j in range(col, n + 1):
                    M[r][j] = (M[r][j] - f * M[col][j]) % q
    return [M[i][n] % q for i in range(n)]  # 回代阶段，取每行最后一列


def main() -> None:
    rng = np.random.default_rng(7)
    n = 3
    q = 101  # 素模数，便于求逆

    # 构造一个 det 不被 q 整除的可逆矩阵 A。
    while True:
        A = rng.integers(0, q, size=(n, n)) % q
        if int(round(np.linalg.det(A))) % q != 0:
            break

    s = rng.integers(0, q, size=n) % q  # 秘密（私钥）
    print("=" * 58)
    print("迷你 LWE：秘密 s =", s, " 模数 q =", q)
    print("  构造矩阵 A（可逆 mod q）并公开。")
    print("=" * 58)

    # --- 无噪声：线性代数精确恢复 s -----------------------------------
    b_clean = (A @ s) % q
    x_mod = solve_mod(A, b_clean, q)
    print("无噪声：解得 s =", s, "  恢复 s'' =", x_mod, "  完全一致:", x_mod == list(s))
    print("  >>> 无噪声时，模线性代数即可精确恢复秘密 s。\n")

    # --- 带小噪声：恢复失效 --------------------------------------------
    e = rng.integers(-1, 2, size=n)  # 微小噪声，取值 {-1, 0, 1}
    b_noisy = (A @ s + e) % q
    x_mod = solve_mod(A, b_noisy, q)
    diff_tiny = np.minimum((np.array(x_mod) - np.array(s)) % q,
                           q - (np.array(x_mod) - np.array(s)) % q)
    print(f"带小噪声 e = {e}")
    print("  真实 s =", s, "  恢复 s' =", x_mod)
    print(f"  与真实 s 的模偏差 Σ|Δ|= {int(np.sum(diff_tiny))}  (0 才算成功)")
    print("  >>> 一小撮噪声就让普通线性代数失准 —— 恢复变难，量子也无捷径。\n")

    # --- Kyber 式共享密钥（KEM 精神） -----------------------------------
    print("=" * 58)
    print("Kyber 式『共享密钥』速写（KEM 精神）")
    print("=" * 58)
    sk_a = rng.integers(0, q, size=n) % q     # Alice 的私有项
    sk_b = rng.integers(0, q, size=n) % q     # Bob 的私有项
    noise_b = rng.integers(-1, 2, size=n)     # Bob 掺一点噪声
    pub_b = (A @ sk_b + noise_b) % q          # Bob 发布一个盲化值
    alice = (sk_a @ pub_b) % q
    shared = int(np.sum(alice)) % q
    print("双方各自输入随机项，经 Bob 发布的盲化值，Alice 得到共享占位:", shared)
    print(">>> 只要格难题在，窃听者即使拿到 A 与公开值，也算不出这个 shared。")


if __name__ == "__main__":
    main()