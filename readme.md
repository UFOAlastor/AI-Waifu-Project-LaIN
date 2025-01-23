# Project LaIN

一个支持长期记忆, 具有表情动作, 语音识别, 语音输出的AI Waifu.

![1737281226243](image/readme/1737281226243.png)

## 功能

- 拥有长期记忆 (基于letta框架实现)
- 两种角色显示
  - 立绘显示方案: 支持自动表情切换
  - live2d模型显示方案: 支持自动表情与动作切换, 口型同步
- 语音识别输入
  - 说话人情感识别(😊高兴, 😡生气/兴奋, 😔悲伤)
  - 背景环境音识别(😀笑声, 🎼音乐, 👏掌声, 🤧咳嗽&喷嚏, 😭哭声)
- 语音合成输出
  - 角色显示选择live2d模型支持口型同步
- 声纹识别
  - 可配置限定用户群体语音识别
  - 说话人身份识别功能 (ps: 可配置模型prompt以登记主人身份)
- 多种LLM支持
  - 可选基于letta框架, letta框架原生支持多种LLM
  - 可选基于ollama框架, ollama允许用户简易地自行部署多种LLM

## 使用说明

注意: **本项目的表情切换依赖prompt配置实现, 请务必关注prompt示例内容!**

(prompt配置请参考prompt_sample.md文件)

1. 在仓库根目录下执行 `pip install -r requirements.txt`指令以安装依赖库
2. 执行仓库根目录下脚本 `setup.bat`安装所需的模型以及live2d-py等依赖
3. 查看config.yaml配置文件, 并根据注释说明进行自定义配置
4. 模型框架部署:
   1. 默认建议采用[letta](https://github.com/letta-ai/letta)框架, 具有记忆能力, 请参考官方指引搭建本地服务 (支持docker部署)
   2. 也支持[Ollama](https://ollama.com/), 请参考官网指引安装并部署本地服务 (支持docker部署)
5. 语音生成服务:
   1. [vits-simple-api](https://github.com/Artrajz/vits-simple-api/blob/main/README_zh.md), 请参考vits-simple官方指引进行配置 (支持docker部署)
   2. 丛雨音色模型: https://github.com/YuzhidaOfficial/yuzhidaofficial.github.io/releases/download/Murasame/Murasame.Vits.zip
6. 运行程序:
   1. 运行letta服务
   2. 运行vits-simple服务
   3. 执行 `main.py`主程序 (初次加载模型可能会有较长耗时, 请耐心等待)
   4. 开始对话~

## 参考项目

- [letta-ai/letta: Letta (formerly MemGPT) is a framework for creating LLM services with memory.](https://github.com/letta-ai/letta)
- [FunAudioLLM/SenseVoice: Multilingual Voice Understanding Model](https://github.com/FunAudioLLM/SenseVoice)
- [Artrajz/vits-simple-api: A simple VITS HTTP API, developed by extending Moegoe with additional features.](https://github.com/Artrajz/vits-simple-api)
- [Arkueid/live2d-py: Live2D Library for Python (C++ Wrapper): Supports model loading, lip-sync and basic face rigging, precise click test.](https://github.com/Arkueid/live2d-py)
- [ABexit/ASR-LLM-TTS: This is a speech interaction system built on an open-source model, integrating ASR, LLM, and TTS in sequence. The ASR model is SenceVoice, the LLM models are QWen2.5-0.5B/1.5B, and there are three TTS models: CosyVoice, Edge-TTS, and pyttsx3](https://github.com/ABexit/ASR-LLM-TTS)
- [Zao-chen/ZcChat: 一个有长期记忆、表情动作立绘显示、立绘动画、语音合成、语音唤醒、直接对话和打断的ai桌宠](https://github.com/Zao-chen/ZcChat?tab=readme-ov-file)
