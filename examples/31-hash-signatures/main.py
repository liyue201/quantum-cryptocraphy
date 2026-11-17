#!/usr/bin/env python3
"""一个极简教学级 Lamport 一次性签名（哈希基）。

核心思想：把消息哈希成一个比特串。对每个比特准备两个秘密
（一个表示‘这一位是0’，一个表示‘这一位是1’）。公钥=每个秘密的哈希。
签名=按位透露与消息匹配的秘密。验证=把透露的秘密做哈希、与公钥比对。
安全性完全只靠哈希的单向性——Shor 无法逆转，Grover 只能减半其强度。

运行:  python3 main.py      （纯 Python + hashlib，不需要 qiskit）
"""

import hashlib
import os


def bits_of(data: bytes, n: int) -> list:
    """取字节串的前 n 位（字节内为大端序）。"""
    out = []
    for i in range(n):
        b = data[i // 8]
        out.append((b >> (7 - i % 8)) & 1)
    return out


class LamportOneTime:
    """n 位 Lamport 一次性签名。"""

    def __init__(self, n: int = 8):
        self.n = n

    def keygen(self):
        # 每个比特两个秘密：下标 0 -> ‘这一位是0’，下标 1 -> ‘这一位是1’
        self.sk = [[os.urandom(16), os.urandom(16)] for _ in range(self.n)]
        self.pk = [[hashlib.sha256(s).hexdigest() for s in pair] for pair in self.sk]
        return self.pk

    def sign(self, msg: bytes) -> list:
        bits = bits_of(hashlib.sha256(msg).digest(), self.n)
        return [self.sk[i][bits[i]] for i in range(self.n)]  # 按位挑对应的秘密

    def verify(self, pk, msg, sig) -> bool:
        bits = bits_of(hashlib.sha256(msg).digest(), self.n)
        for i in range(self.n):
            if hashlib.sha256(sig[i]).hexdigest() != pk[i][bits[i]]:
                return False
        return True


def main() -> None:
    s = LamportOneTime(8)
    pk = s.keygen()
    msg = b"send 1.5 BTC to alice"
    sig = s.sign(msg)

    print(f"签名长度(字节数/被泄露的秘密数) = {len(sig)}")
    print("正常验证:", s.verify(pk, msg, sig))

    # 篡改消息 -> 立刻验证失败
    forged = s.verify(pk, b"send 100 BTC to EVIL", sig)
    print(f"篡改消息后验证: {forged}  (应为 False)")

    # 一次性使用警告：用同一把钥匙签两条【不同】消息，
    # 会把两组‘1’位上的秘密并集都暴露出来，等于削弱（泄露）钥匙。
    signed_bits_msg1 = bits_of(hashlib.sha256(msg).digest(), s.n)
    signed_bits_msg2 = bits_of(hashlib.sha256(b"different msg").digest(), s.n)
    revealed = [i for i in range(s.n) if signed_bits_msg1[i] == 1 or signed_bits_msg2[i] == 1]
    print(f"同把钥匙签两条不同消息，被『公开』的秘密位并集: {revealed}")
    print("→ 次数一多，外推秘密越来越多 → 这就是 Lamport 必须一次一钥，")
    print("  SPHINCS+ 用哈希树轮换新密钥来化解。")

    print("结论: 安全只靠哈希单向性；Shor 无法逆转单向性，量子只能平方根加速。")


if __name__ == "__main__":
    main()