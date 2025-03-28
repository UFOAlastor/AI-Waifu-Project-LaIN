# aec_module.py
# 目前采用apa算法方案, 依旧没有达到可用效果, 有待进一步优化和调试, 目前不启用

import sounddevice as sd
import numpy as np
import wavio
import soundfile as sf
import time
import os
import threading


def apa(x, d, N=256, P=5, mu=0.1):
    """
    仿射投影算法(Affine Projection Algorithm)实现

    参数:
    x: 参考信号（系统音频）
    d: 带回声信号（麦克风录音）
    N: 滤波器长度
    P: 投影阶数
    mu: 步长参数

    返回:
    e: 回声消除后的信号
    """
    nIters = min(len(x), len(d)) - N
    u = np.zeros(N)
    A = np.zeros((N, P))
    D = np.zeros(P)
    w = np.zeros(N)
    e = np.zeros(nIters)

    alpha = 0.1  # 正则化参数

    for n in range(nIters):
        # 更新输入矩阵
        for i in range(P):
            if i == 0:
                A[:, i] = x[n : n + N]
            else:
                if n - i >= 0:
                    A[:, i] = x[n - i : n - i + N]

        # 更新期望输出
        for i in range(P):
            if n - i >= 0:
                D[i] = d[n + N - 1 - i]

        # 计算输出
        y = np.dot(w, A[:, 0])

        # 计算误差
        e_n = D[0] - y

        # 计算自相关矩阵
        R = np.dot(A.T, A)

        # 添加正则化项以确保稳定性
        R = R + alpha * np.eye(P)

        # 计算更新项
        dw = mu * np.dot(A, np.linalg.solve(R, D - np.dot(A.T, w)))

        # 更新滤波器系数
        w = w + dw

        # 保存误差
        e[n] = e_n

    return e


class DualRecorder:
    def __init__(self):
        """初始化双通道录音器"""
        print("使用APA(仿射投影算法)进行回声消除")

    def record_dual_audio(self, duration=5, output_folder="recordings"):
        """同时录制麦克风输入和系统音频"""
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)

        # 录音参数设置
        sample_rate = 44100
        channels = 2
        timestamp = time.strftime("%Y%m%d")

        # 文件名
        mic_file = os.path.join(output_folder, f"mic_{timestamp}.wav")
        sys_file = os.path.join(output_folder, f"sys_{timestamp}.wav")
        output_file = os.path.join(output_folder, f"clean_{timestamp}.wav")

        # 查找系统音频设备
        devices = sd.query_devices()

        # 寻找麦克风输入设备
        mic_device = None
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0 and "mic" in dev["name"].lower():
                mic_device = i
                break

        if mic_device is None:
            for i, dev in enumerate(devices):
                if dev["max_input_channels"] > 0:
                    mic_device = i
                    break

        # 寻找系统音频设备
        sys_device = None
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0 and (
                "立体声混音" in dev["name"]
                or "Stereo Mix" in dev["name"]
                or "Loopback" in dev["name"]
            ):
                sys_device = i

        if mic_device is None or sys_device is None:
            print("错误: 未找到麦克风或系统音频设备")
            print("可用设备列表:")
            for i, dev in enumerate(devices):
                print(
                    f"{i}: {dev['name']} (输入: {dev['max_input_channels']}, 输出: {dev['max_output_channels']})"
                )
            return None

        print(f"使用麦克风设备: {devices[mic_device]['name']}")
        print(f"使用系统音频设备: {devices[sys_device]['name']}")

        # 检查设备设置
        try:
            sd.check_input_settings(
                device=mic_device, samplerate=sample_rate, channels=channels
            )
        except Exception as e:
            print(f"mic_device设备设置错误: {e}")
            return None
        try:
            sd.check_input_settings(
                device=sys_device, samplerate=sample_rate, channels=channels
            )
        except Exception as e:
            print(f"sys_device设备设置错误: {e}")
            return None

        # 录制麦克风音频
        print(f"开始录音，时长 {duration} 秒...")

        # 使用可变对象存储录音结果
        recordings = {"mic": None, "sys": None}

        def record_mic():
            recordings["mic"] = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=channels,
                device=mic_device,
                dtype="float32",
            )
            sd.wait()

        def record_sys():
            recordings["sys"] = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=channels,
                device=sys_device,
                dtype="float32",
            )
            sd.wait()

        # 创建并启动线程
        mic_thread = threading.Thread(target=record_mic)
        sys_thread = threading.Thread(target=record_sys)

        mic_thread.start()
        sys_thread.start()

        # 等待线程完成
        mic_thread.join()
        sys_thread.join()

        # 获取录音数据
        mic_recording = recordings["mic"]
        sys_recording = recordings["sys"]

        # 添加空数据检测
        if mic_recording is None or sys_recording is None:
            print("录音失败: 未获取到有效音频数据")
            return None

        # 修改为单通道
        mic_recording = mic_recording[:, 0]
        sys_recording = sys_recording[:, 1]

        # 归一化
        if np.max(np.abs(mic_recording)) > 0:
            mic_recording = mic_recording / (np.max(np.abs(mic_recording)) + 1e-5)
        if np.max(np.abs(sys_recording)) > 0:
            sys_recording = sys_recording / (np.max(np.abs(sys_recording)) + 1e-5)

        print("录音完成，保存文件中...")

        # 保存录音
        wavio.write(mic_file, mic_recording, sample_rate, sampwidth=2)
        wavio.write(sys_file, sys_recording, sample_rate, sampwidth=2)

        print(f"麦克风录音已保存至 {mic_file}")
        print(f"系统音频已保存至 {sys_file}")

        # 回声消除处理
        print("正在应用APA回声消除...")

        # 应用APA算法
        clean_audio = apa(
            sys_recording,  # 参考信号（系统音频）
            mic_recording,  # 带回声信号（麦克风录音）
            N=256,  # 滤波器长度
            P=5,  # 投影阶数
            mu=0.1,  # 步长参数
        )

        # 处理后的音频可能需要补齐长度
        if len(clean_audio) < len(mic_recording):
            clean_audio = np.pad(
                clean_audio, (0, len(mic_recording) - len(clean_audio)), "constant"
            )

        # 保存处理后的音频
        sf.write(output_file, clean_audio, sample_rate)
        print(f"回声消除后的音频已保存至 {output_file}")

        return {
            "mic_file": mic_file,
            "sys_file": sys_file,
            "clean_file": output_file,
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="回声消除录音系统")
    parser.add_argument(
        "--record", action="store_true", default=True, help="录制新的音频"
    )
    parser.add_argument("--duration", type=int, default=5, help="录音时长（秒）")
    parser.add_argument(
        "--output_folder", type=str, default="./audio", help="录音输出文件夹"
    )

    args = parser.parse_args()

    recorder = DualRecorder()

    if args.record:
        result = recorder.record_dual_audio(
            duration=args.duration, output_folder=args.output_folder
        )
        if result:
            print("\n录音和处理完成。文件路径:")
            for key, value in result.items():
                print(f"{key}: {value}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
