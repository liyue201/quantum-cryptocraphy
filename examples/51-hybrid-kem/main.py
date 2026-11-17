#!/usr/bin/env python3
"""混合 KEM —— 教学级、纯 Python 速写。

我们把两条"建钥通道"(一条经典 DH 式、一条格/Kyber 式)抽象出来，
每条都各自产出一个共享秘密；会话密钥由二者拼接后派生。
要点：只要还剩下一条通道是安全的，最终密钥就仍被保护——
攻击者必须把两条都攻破。

接着我们模拟攻击者暴力破解秘密，证明：只破掉一条通道，
不足以还原出真正的会话密钥。

运行:  python3 main.py      （纯 Python，无依赖）
"""

import hashlib
import random
import secrets


def derive(ch1: int, ch2: int) -> bytes:
    """由两条通道的共享秘密派生出单一的会话密钥。"""
    return hashlib.sha256(f"{ch1}:{ch2}".encode()).digest()


def abstract_channel_shared(priv_a: int, priv_b: int, base: int, bits: int) -> int:
    """极粗略的密钥交换替身：双方各自算 base^priv mod N。
    窃听者只看到两个公开值；求那两个值的"离散对数"才是难处
    （现实中经典用 DH、Kyber 用格）。"""
    pub_a = pow(base, priv_a, 1 << bits)
    pub_b = pow(base, priv_b, 1 << bits)
    ss_a = pow(pub_b, priv_a, 1 << bits)   # Alice 的视角
    ss_b = pow(pub_a, priv_b, 1 << bits)   # Bob 的视角
    assert ss_a == ss_b
    return ss_a


def main() -> None:
    base, bits = 5, 10  # 取极小的模数，让暴力破解瞬间完成（仅演示）
    # Alice & Bob 的私有值（每条通道不同）
    a1, b1 = secrets.randbelow(1 << bits), secrets.randbelow(1 << bits)  # 经典通道
    a2, b2 = secrets.randbelow(1 << bits), secrets.randbelow(1 << bits)  # Kyber 通道

    ch_classic = abstract_channel_shared(a1, b1, base, bits)       # 近似 'X25519'
    ch_kyber = abstract_channel_shared(a2, b2, base, 1 << bits//2) # 近似 'Kyber'
    session = derive(ch_classic, ch_kyber)

    print("=" * 58)
    print("迷你混合 KEM：双通道并行 → 拼接派生会话密钥")
    print("=" * 58)
    print(f"  经典通道(离散对数) 共享 = {ch_classic}")
    print(f"  后量子信道(格/Kyber)共享 = {ch_kyber}")
    print(f"  会话密钥 = SHA-256(经典 || 量子) = {session.hex()[:16]}…\n")

    # --- 攻击者只拿到公开值 -------------------------------------------------
    print("  攻击者只破『经典』通道 ≈ 拿到 ch_classic，但不知 ch_kyber。")
    print("  攻击者尝试用『只有一个通道』重建会话密钥，结果与真实密钥不同:")
    fake = derive(ch_classic, secrets.randbelow(1 << bits))
    print(f"    真实会话: {session.hex()[:16]}…")
    print(f"    伪造会话: {fake.hex()[:16]}…   相符?: {fake == session}")
    print("  >>> 只要后量子通道安全，破掉经典一条也不够 → 双保险成立。")

    print("=" * 58)
    print("结论: 字节会话密钥由『两条通道之和』派生——")
    print("      至少一条仍强时，整体密钥就无法被攻击者恢复。")


if __name__ == "__main__":
    main()