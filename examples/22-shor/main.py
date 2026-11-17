#!/usr/bin/env python3
"""用纯 Python 演示 Shor 算法的‘数学骨架’。

真正的 Shor 用‘量子相位估计(QPE)’来快速求阶，这里我们展示最关键的一步：
一旦知道了阶 r（或退而求其次、用小的周期试探出来），就怎么把质因子拆出来——
随机取一个与 N 互质的 g，找到最小 r 使 g^r ≡ 1 (mod N)，再用 gcd 拆出因子。

运行:  python3 main.py      （纯 Python，不需要 qiskit）
"""

from math import gcd
from random import randrange


def order(g: int, n: int) -> int:
    """求最小正整数 r，使 g**r == 1 (mod n)。仅作为经典演示。"""
    x = 1
    for r in range(1, n):  # 对互质的 g，必有 r < n
        x = (x * g) % n
        if x == 1:
            return r
    return 0


def shor_factor(n: int) -> tuple:
    """按 Shor 的步骤返回一队 (p, q) 使 p*q == n。"""
    for _ in range(20):
        g = randrange(2, n - 1)
        if gcd(g, n) != 1:  # 幸运：g 本身已经和 n 共享因子
            return gcd(g, n), n // gcd(g, n)
        r = order(g, n)
        if r % 2 == 0:
            half = pow(g, r // 2, n)
            if half != (n - 1):  # g^(r/2) != -1 mod n
                p = gcd(half + 1, n)
                return p, n // p
    return 0, 0  # 对小 N 加多次重试不应发生


def main() -> None:
    n = 15
    print(f"目标: 分解 N = {n}")
    print("=" * 44)

    g = randrange(2, n - 1)
    while gcd(g, n) != 1:
        g = randrange(2, n - 1)
    r = order(g, n)
    print(f"① 随机取与 N 互质的 g = {g}")
    print(f"② order finding：求最小 r 使 {g}^r ≡ 1 (mod {n}) → r = {r}")
    half = pow(g, r // 2, n)
    p, q = gcd(half + 1, n), gcd(half - 1, n)
    print(f"③ 用 r 拆：gcd(g^(r/2)+1, N) = {p}, gcd(g^(r/2)-1, N) = {q}")
    print(f"   => 得到因子：{p} × {q} = {p * q}")
    print("=" * 44)

    # 一致性检查：多跑几次，p*q 必须始终等于 N。
    ok = all((lambda a: a[0] * a[1] == n)(shor_factor(n)) for _ in range(5))
    print(f"多次随机 g 试跑，因子乘积恒等于 N = {n}: {'通过' if ok else '失败'}")
    print("结论: Shor 把『分解』变成『找周期』，再变成 `gcd` 一步——")
    print("      量子相位估计让找 r 变得多项式级快，RSA/ECDSA 就此失守。")


if __name__ == "__main__":
    main()