# 说明

此文件夹放置已经遗弃的旧版方案代码或者测试文件, 以供参考.

# 清单

1. "asr_whisper_module": 语音识别的whisper方案, 因为whisper存在严重幻觉情况以及中文识别效果表现不如SenseVoice而被替换, 对应的最后一版commit为**f9fedf3.**
2. "test_lipsync": 测试live2d口型同步效果的测试脚本, 请移动到根目录执行
3. "realtimeSTT_module": 语音识别的realtimeSTT方案, 虽然易用性不错, 但是本体还是基于whisper实现, 并且也没有针对whisper的幻觉进行优化, 此外对比目前的sensevoice方案没有明显优势.
4. 一系列AEC回声消除方案, 测试效果都不佳.
