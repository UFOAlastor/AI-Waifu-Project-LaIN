import pyaudio
import numpy as np
import webrtcvad
import whisper
import wave
import tempfile

# import torch  # 用于将 numpy 转换为 Tensor
# from df import enhance, init_df  # 导入 DeepFilterNet 所需模块

# 配置录音
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
MAX_SILENCE_DURATION = 2  # 最大允许静音时长 (秒)

# 初始化 DeepFilterNet 模型
# model, df_state, _ = init_df()  # 加载默认模型

# 创建 VAD 对象; 1, 2, 3 数值低表示较宽松的模式, 适用于噪音较大的情况, 反之则是严格模式
vad = webrtcvad.Vad(2)


# 语音检测函数
def detect_speech(audio_data, sample_rate=16000, frame_duration_ms=20):
    frames = chunk_audio_data(audio_data, frame_duration_ms, sample_rate)
    for frame in frames:
        frame_bytes = np.array(frame, dtype=np.int16).tobytes()
        try:
            if vad.is_speech(frame_bytes, sample_rate):
                return True
        except Exception as e:
            print(f"Error processing frame: {e}")
    return False


# 将音频数据切分成固定时长的帧
def chunk_audio_data(audio_data, frame_duration_ms=20, sample_rate=16000):
    frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
    frames = [
        audio_data[i : i + frame_size] for i in range(0, len(audio_data), frame_size)
    ]
    return frames


# 使用 DeepFilterNet 进行降噪处理
# def denoise_audio(audio_data, sample_rate=16000):
#     # 将 numpy.ndarray 转换为 PyTorch Tensor，并确保为 float32 类型
#     audio_tensor = torch.from_numpy(
#         np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
#     )

#     # 增加一个批处理维度，形状变为 [1, 音频长度]
#     audio_tensor = audio_tensor.unsqueeze(0)

#     # 调用 DeepFilterNet 的 enhance 方法
#     enhanced_audio = enhance(model, df_state, audio_tensor)

#     # 将增强后的 Tensor 转换回 numpy 格式，去掉批处理维度
#     enhanced_audio = enhanced_audio.squeeze(0).cpu().numpy()

#     # 转换为 bytes 格式
#     return np.array(enhanced_audio, dtype=np.int16).tobytes()


# 开始录音并检测静音
def record_audio_with_vad_and_energy():
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )
    print("录音中...")
    frames = []
    silent_chunks = 0
    total_chunks = 0

    while True:
        data = stream.read(CHUNK)

        # # 对音频数据进行降噪
        # data = denoise_audio(data)

        # 检测是否为语音
        is_speech = detect_speech(np.frombuffer(data, dtype=np.int16))
        print(f"语音检测: {is_speech}")

        # 如果检测到语音，保存降噪后的数据
        frames.append(data)
        total_chunks += 1

        # 如果没有语音检测到，则认为是静音
        if not is_speech:
            silent_chunks += 1
        else:
            silent_chunks = 0  # 有语音输入，重置静音计数

        # 如果达到静音时间阈值，提前结束录音
        if silent_chunks > (RATE / CHUNK * MAX_SILENCE_DURATION):
            print("检测到静音，录音结束")
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # 返回降噪后的音频数据，以 bytes 形式存储在内存中
    audio_data = b"".join(frames)
    return audio_data


# 使用 Whisper 进行语音识别
def transcribe_realtime():
    model = whisper.load_model("small")
    audio_data = record_audio_with_vad_and_energy()

    # 创建一个临时的 .wav 文件，并将音频数据写入其中
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        with wave.open(temp_wav, "wb") as wf:
            wf.setnchannels(1)  # 单声道
            wf.setsampwidth(2)  # 每个样本占2字节
            wf.setframerate(RATE)
            wf.writeframes(audio_data)

        # 使用 whisper 进行语音识别，启用标点符号
        initial_prompt = (
            "以下是普通话为主的句子，这是提交给智能助手Lin的语音输入。请确保识别Lin字！"
        )
        result = model.transcribe(temp_wav.name, initial_prompt=initial_prompt)

        # 获取转录文本
        transcribed_text = result["text"]
        print(f"转录结果: {transcribed_text}")


if __name__ == "__main__":
    transcribe_realtime()
