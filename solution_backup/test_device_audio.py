import sounddevice as sd
import numpy as np
import wavio


def record_system_audio():
    # 录音参数设置
    duration = 5
    sample_rate = 44100
    channels = 2

    # 获取可用设备列表
    devices = sd.query_devices()
    print("可用设备列表:")
    for i, dev in enumerate(devices):
        print(f"{i}: {dev['name']}")

    # 根据系统选择设备类型
    system = "Windows"
    if system == "Windows":
        # Windows需要启用"立体声混音"并选择对应的设备索引
        device_index = next(
            (
                i
                for i, dev in enumerate(devices)
                if "立体声混音" in dev["name"] or "Loopback" in dev["name"]
            ),
            None,
        )
    elif system == "Linux":
        # Linux使用PulseAudio的monitor设备
        device_index = next(
            (i for i, dev in enumerate(devices) if "Monitor" in dev["name"]), None
        )
    elif system == "Darwin":
        # macOS需要BlackHole虚拟声卡
        device_index = next(
            (i for i, dev in enumerate(devices) if "BlackHole" in dev["name"]), None
        )
    else:
        raise NotImplementedError("不支持的操作系统")

    if device_index is None:
        raise ValueError("未找到可用的环回设备，请先配置系统音频设置")

    try:
        print(f"正在使用设备 {devices[device_index]['name']} 进行录音...")
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            device=device_index,
            dtype="int16",
        )
        sd.wait()
        print("录音完成，保存文件中...")
        wavio.write("system_audio.wav", recording, sample_rate, sampwidth=2)
        print("文件已保存为 system_audio.wav")

    except Exception as e:
        print(f"录音失败: {str(e)}")


if __name__ == "__main__":
    record_system_audio()
