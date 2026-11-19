"""版本化系统提示词：正文改动必须登记为新版本，否则测试会红。

为什么单独放一个模块（BACKLOG D6）：
- 提示词原来硬编码在 `nodes.py`，改一个字谁也不知道这轮回答用的是哪版；
- 线上排查「为什么今天回答风格变了」时，日志里只有一个模型名，没有提示词版本；
- 做法是最小可验证的：一个 `版本号 -> 正文` 的登记表 + 冻结的 sha256，
  当前版本取登记表最后一条；`FROZEN_SHA256` 里的哈希是手写常量，
  所以「改了正文但没升版本」会让 `tests/test_prompts.py` 直接失败。

约定（给后来的人）：
1. 改正文 = 新增一条 `(新版本号, 新正文)` + 新增一条冻结哈希，永远不要原地改旧版本；
2. 版本号用 `YYYY-MM-DD.n`，同一天多次改动递增 `.n`；
3. 校验：`pytest tests/test_prompts.py`，以及单测里断言 run 的 meta 带版本号。
"""

from __future__ import annotations

import hashlib

# 版本 -> 当时的正文。只增不改：历史版本留着，出问题时能对上是哪一版。
PROMPT_VERSIONS: dict[str, str] = {
    "2026-11-15.1": """你是 PetLumina 的宠物管家「Lumina」。你的服务对象是当前登录用户和他的宠物。

硬性规则：
1. 涉及宠物健康数据（心率/睡眠/体重/饮食/排泄）时，必须先调用工具查真实数据；查不到就直说查不到，禁止编造数值。
2. 任何医疗判断都要标注「仅供参考，不替代兽医诊断」；出现持续呕吐、抽搐、呼吸困难等急症，直接建议立刻就医。
3. 回答用中文、口语化、简短（默认 3 句以内），除非用户要求展开。
4. 引用工具结果时给出可核对的来源（记录标题 / 日期），不要模糊成「你说过」。
5. 不知道就说不知道。宁可少说，不要错说。""",
    "2026-11-19.1": """你是 PetLumina 的宠物管家「Lumina」。你的服务对象是当前登录用户和他的宠物。

硬性规则：
1. 涉及宠物健康数据（心率/睡眠/体重/饮食/排泄）时，必须先调用工具查真实数据；查不到就直说查不到，禁止编造数值。
2. 任何医疗判断都要标注「仅供参考，不替代兽医诊断」；出现持续呕吐、抽搐、呼吸困难等急症，直接建议立刻就医。
3. 回答用中文、口语化、简短（默认 3 句以内），除非用户要求展开。
4. 引用工具结果时给出可核对的来源（记录标题 / 日期），不要模糊成「你说过」。
5. 不知道就说不知道。宁可少说，不要错说。
6. 用户问「我有哪些宠物 / 我的宠物叫什么 / 宠物档案 / 宠物列表」时，必须先调用 get_pet_profile（不传 pet_id 表示全部宠物），再根据工具结果回答；禁止在没有调用工具的情况下声称「没有宠物查询工具」或「查不到宠物数据」。""",
}

# 冻结哈希：手写常量，不随正文重算——这是「改正文必须升版本」的闸门。
FROZEN_SHA256: dict[str, str] = {
    "2026-11-15.1": "a04df4e347821b8202e337c643be7a05d343cb7121fe9e21c6da82d8146806c9",
    "2026-11-19.1": "1ab5b7e4ea8ed798f417ecf6f9a48e22d5d0b24a733766f37b0dbdd70a77c5db",
}


def sha256_of(text: str) -> str:
    """统一的口径：UTF-8 字节的 sha256 十六进制。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def latest_version() -> str:
    """登记表最后一个键就是当前版本（按插入顺序，Python 3.7+ 保证）。"""
    return next(reversed(PROMPT_VERSIONS))


PROMPT_VERSION: str = latest_version()
SYSTEM_PROMPT: str = PROMPT_VERSIONS[PROMPT_VERSION]
PROMPT_SHA256: str = sha256_of(SYSTEM_PROMPT)

__all__ = [
    "FROZEN_SHA256",
    "PROMPT_SHA256",
    "PROMPT_VERSION",
    "PROMPT_VERSIONS",
    "SYSTEM_PROMPT",
    "latest_version",
    "sha256_of",
]
