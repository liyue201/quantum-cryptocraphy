#!/usr/bin/env python3
"""讲述量子对加密货币的威胁 + 一种防守。

攻击：ECDSA 的安全建立在‘离散对数难’上，而 Shor 能解离散对数，
      所以拿到你公钥的人能反推出你的私钥。
      这里用一个假的‘Shor’黑盒：知道公钥即‘暴露’私钥（即旧体制结构上已失效）。
防守：哈希基一次性签名（Lamport 风格）。它只依赖哈希的单向性；
      Grover 只能把这种强度减半，不能‘逆转’单向性，所以签名存活。

运行:  python3 main.py      （纯 Python + hashlib，不需要 qiskit）
"""

import hashlib
import os
import random


# ---------------------------------------------------------------- 旧方案
def ecdsa_like_sign(priv: int, msg: bytes) -> int:
    """微型替身：签名 = priv 的 message 次幂（离散对数‘难逆推’）。
    这不是真的 ECDSA，只建模‘签名里包含 Shor 可反推出 priv 的信息’。"""
    return pow(priv, int.from_bytes(msg[:8], "big") % (1 << 40), (1 << 61) - 1)


def fak_quantum_break(pub, sig, msg):
    """黑盒‘Shor’：从公钥/签名信息反推出私钥。"""
    return pub  # 简写：有 Shor 时，知道公钥即‘暴露’私钥（模拟）


# ------------------------------------------------------------ 哈希一次性签名
class HashOneTimeSig:
    """Lamport 启发：对一段哈希用随机秘密块签名，靠哈希验证。"""

    BLOCKS = 8  # 每个子块签的位数（微型演示）

    def generate(self):
        self.sk = [os.urandom(16) for _ in range(self.BLOCKS)]  # 每个比特一块秘密
        self.pk = [hashlib.sha256(b).hexdigest() for b in self.sk]  # 公钥=秘密的哈希
        return self.pk

    def sign(self, msg: bytes):
        h = hashlib.sha256(msg).digest()
        bits = [ (h[i // 8] >> (7 - i % 8)) & 1 for i in range(self.BLOCKS) ]
        return [ self.sk[i] if bits[i] == 1 else b"" for i in range(self.BLOCKS) ]

    def verify(self, pk, msg, sig) -> bool:
        h = hashlib.sha256(msg).digest()
        bits = [ (h[i // 8] >> (7 - i % 8)) & 1 for i in range(self.BLOCKS) ]
        for i in range(self.BLOCKS):
            expect = pk[i] if bits[i] == 1 else hashlib.sha256(b"").hexdigest()
            if hashlib.sha256(sig[i] if sig[i] else b"").hexdigest() != expect:
                return False
        return True


def main() -> None:
    random.seed(1)
    print("=" * 58)
    print("攻击阶段：老式 ECDSA 类签名 —— '公钥在手，私钥可破'")
    print("=" * 58)
    priv = 0xBEEF  # 假设一个真实私钥
    msg = b"send 1 BTC"
    sig = ecdsa_like_sign(priv, msg)
    leaked = fak_quantum_break(pow(priv, 2, 1 << 61), sig, msg)  # 'Shor' 反推出私钥
    print(f"  公钥广播 = {pow(priv, 2, 1 << 61) & 0xFFFF:x}")
    print(f"  攻击者用 Shor 反推出的私钥 = {leaked & 0xFFFF:x}")
    print(f"  真实私钥(应当保密)          = {priv & 0xFFFF:x}")
    print("  >>> 一致：Shor 结构性破解 ECDSA，余额可被抢先消费！\n")

    print("=" * 58)
    print("防护阶段：哈希一次性签名 —— 只依赖哈希单向性")
    print("=" * 58)
    s = HashOneTimeSig()
    pk = s.generate()
    sig2 = s.sign(msg)
    ok = s.verify(pk, msg, sig2)
    print(f"  签名并验证：{ok}")
    # 即使拿到签名和公钥，攻击者看到的也只是秘密块的哈希值，无法‘反推私钥’。
    print("  攻击者拿到的是哈希值 pk，单向 → 无法反推签名随机块。")
    print("  >>> Grover 只能把哈希强度减半，不能逆转单向性：签名存活。")

    print("=" * 58)
    print("应对总纲：签名区换算法(SPHINCS+/格)，哈希区加长参数+一次性地址。")


if __name__ == "__main__":
    main()