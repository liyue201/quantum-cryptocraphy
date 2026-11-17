#!/usr/bin/env python3
"""收官：一封加密且签名的'量子信'。

把全书反复出现的积木组装进一个可运行的小故事：
  - 指纹          : 对负载做 SHA-256
  - 签名          : 哈希基一次性签名（Shor 无法逆转）
  - 封装          : 用混合派生的会话密钥做 XOR 混淆加密
  - 验证与开信    : 验签 + 比对指纹
  - 篡改实验      : 改动一个字节 -> 立刻被发现

运行:  python3 main.py      （纯 Python + hashlib）
"""

import hashlib
import os


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---- 混合会话密钥：两条通道，拼接后再哈希（见第 5 篇第 1 章） ---------------
def hybrid_session(classic_ss: int, pq_ss: int) -> bytes:
    return hashlib.sha256(f"{classic_ss}:{pq_ss}".encode()).digest()


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    k = (key * (len(data) // len(key) + 1))[:len(data)]  # 把密钥循环铺满明文长度
    return bytes(a ^ b for a, b in zip(data, k))  # 逐字节异或混淆


# ---- 对摘要做简化的 Lamport 一次性签名 --------------------------------------
class OneTimeSig:
    def __init__(self, n: int = 8):
        self.n = n
        # 每个比特两个秘密：一个表 0，一个表 1；公钥 = 秘密的哈希
        self.sk = [[os.urandom(16), os.urandom(16)] for _ in range(n)]
        self.pk = [[hashlib.sha256(s).hexdigest() for s in pair] for pair in self.sk]

    def _bits(self, msg: bytes) -> list:
        h = hashlib.sha256(msg).digest()
        return [(h[i // 8] >> (7 - i % 8)) & 1 for i in range(self.n)]

    def sign(self, msg: bytes) -> list:
        bs = self._bits(msg)
        return [self.sk[i][bs[i]] for i in range(self.n)]  # 按位挑秘密

    def verify(self, pk, msg, sig) -> bool:
        bs = self._bits(msg)
        for i in range(self.n):
            if hashlib.sha256(sig[i]).hexdigest() != pk[i][bs[i]]:
                return False
        return True


def main() -> None:
    # 0) 明文信 + 指纹
    letter = b"Dear Alice, the quantum-safe era has arrived. - Bob"

    # 1) 两条通道的秘密（经典 + 后量子），派生出混合会话密钥
    classic_ss, pq_ss = 123456789, 987654321       # 代替 X25519 与 Kyber 的占位
    session = hybrid_session(classic_ss, pq_ss)

    # 2) 对摘要用哈希基一次性签名
    ot = OneTimeSig(8)
    pk = ot.pk
    sig = ot.sign(letter)

    # 3) 封装信（用混合会话密钥加密）
    seal = xor_encrypt(letter, session)

    print("=" * 58)
    print("量子信（收信前）")
    print("=" * 58)
    print(f"  明文指纹(哈希)      = {digest(letter)}")
    print(f"  摘要签名(哈希基, 8bit lamport) 长度 = {len(sig)}")
    print(f"  会话密钥(混合派生)  = {session.hex()[:16]}…")
    print(f"  封装密文(前16字节)  = {seal[:16].hex()}")
    print()

    # 4) 收信方：开信 + 验证
    opened = xor_encrypt(seal, session)   # 用同一把密钥解密
    sig_ok = ot.verify(pk, opened, sig)
    hash_ok = digest(opened) == digest(letter)
    print("=" * 58)
    print("收信：解密 + 验签 + 比对指纹")
    print("=" * 58)
    print(f"  解密内容匹配原文: {opened == letter}")
    print(f"  签名验证         : {sig_ok}")
    print(f"  指纹比对         : {hash_ok}")
    print(f"  判定: {'✅ 可信的量子信' if (sig_ok and hash_ok and opened == letter) else '❌ 不可信'}")

    # 5) 篡改实验：翻转一个字节
    tampered = bytearray(opened); tampered[-2] ^= 0x01; tampered = bytes(tampered)
    sig_ok2 = ot.verify(pk, tampered, sig)
    hash_ok2 = digest(tampered) == digest(letter)
    print()
    print("破坏实验：把正文最后一个字节翻转 1 bit")
    print(f"  篡改后验签 = {sig_ok2}   篡改后指纹比对 = {hash_ok2}")
    print("  >>> 一点改动即被识破 —— 与『量子测量坍缩、一看就穿』同理。")

    print("=" * 58)
    print("收官：算法(PQC/hash) + 物理直觉(QKD) + 工程(混合/一次性) 三层协同。")


if __name__ == "__main__":
    main()