import sounddevice as sd
import numpy as np
import wavio
import soundfile as sf
import time
import os
import threading
from numpy.fft import fft, ifft


class PFDAF:
    def __init__(self, N=4, M=64, mu=0.1, partial_constrain=True):
        """
        初始化PFDAF(分区频域自适应滤波器)

        参数:
        N: 滤波器块数
        M: 每块的长度
        mu: 步长参数
        partial_constrain: 是否使用部分约束
        """
        self.N = N
        self.M = M
        self.N_freq = 1 + M
        self.N_fft = 2 * M
        self.mu = mu
        self.partial_constrain = partial_constrain

        # 初始化状态变量
        self.p = 0
        self.x = np.zeros(shape=(2 * self.M), dtype=np.float32)
        self.X = np.zeros((N, self.N_fft), dtype=np.complex64)
        self.H = np.zeros((N, self.N_fft), dtype=np.complex64)
        self.x_old = np.zeros(self.M)
        self.window = np.hanning(self.M)  # 使用汉宁窗进行平滑[^1]

    def filt(self, x, d):
        """
        使用PFDAF对输入信号进行滤波

        参数:
        x: 参考信号(块)
        d: 期望信号(块)

        返回:
        e: 误差信号(回声消除后的信号)
        """
        assert len(x) == self.M

        # 将当前输入与上一个输入拼接
        x_now = np.concatenate([self.x_old, x])

        # 计算当前输入的FFT
        X = fft(x_now)

        # 更新输入状态
        self.X[1:] = self.X[:-1]
        self.X[0] = X
        self.x_old = x

        # 计算滤波器输出
        Y = np.sum(self.H * self.X, axis=0)
        y = ifft(Y)[self.M :]

        # 计算误差
        e = d - y

        # 更新滤波器系数
        self.update(e)

        return e

    def update(self, e):
        """更新滤波器系数"""
        # 计算频域误差
        E = fft(np.concatenate([np.zeros(self.M), e]))

        # 频域更新
        for p in range(self.N):
            dH = (
                self.mu
                * np.conj(self.X[p])
                * E
                / (np.sum(np.abs(self.X) ** 2, axis=0) + 1e-6)
            )

            # 应用部分约束(如果启用)
            if self.partial_constrain:
                h = ifft(dH)
                h[self.M :] = 0
                dH = fft(h)

            self.H[p] += dH


def pfdaf(x, d, N=4, M=64, mu=0.1, partial_constrain=True):
    """
    PFDAF算法的主函数

    参数:
    x: 参考信号
    d: 带回声信号
    N: 滤波器块数
    M: 每块的长度
    mu: 步长参数
    partial_constrain: 是否使用部分约束

    返回:
    e: 回声消除后的信号
    """
    ft = PFDAF(N, M, mu, partial_constrain)
    num_block = min(len(x), len(d)) // M
    e = np.zeros(num_block * M)

    for n in range(num_block):
        x_n = x[n * M : (n + 1) * M]
        d_n = d[n * M : (n + 1) * M]
        e_n = ft.filt(x_n, d_n)
        e[n * M : (n + 1) * M] = e_n

    return e


class DualRecorder:
    def __init__(self):
        """初始化双通道录音器"""
        print("使用PFDAF(分区频域自适应滤波器)进行回声消除")

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
        print("正在应用PFDAF回声消除...")

        # 应用PFDAF算法[^6]
        clean_audio = pfdaf(
            sys_recording,  # 参考信号（系统音频）
            mic_recording,  # 带回声信号（麦克风录音）
            N=8,  # 滤波器块数
            M=64,  # 每块的长度
            mu=0.1,  # 步长参数
            partial_constrain=True,  # 使用部分约束
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

    # 创建录音器实例
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
