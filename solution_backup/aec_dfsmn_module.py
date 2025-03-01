from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import sounddevice as sd
import numpy as np
import wavio
import soundfile as sf
import time
import os
import threading
from scipy import signal
import tempfile


def gcc_phat(sig, refsig, fs=1, max_tau=None, interp=16):
    """
    使用GCC-PHAT算法计算两个信号的时间延迟
    sig: 信号
    refsig: 参考信号
    fs: 采样率
    max_tau: 最大延迟时间
    interp: 插值因子
    """
    # 确保信号长度一致
    n = len(sig)

    # 计算FFT
    sig_fft = np.fft.rfft(sig)
    refsig_fft = np.fft.rfft(refsig)

    # 计算互功率谱
    R = sig_fft * np.conj(refsig_fft)

    # PHAT加权
    R /= np.abs(R) + 1e-10

    # 计算互相关
    cc = np.fft.irfft(R)

    # 找到最大互相关
    max_shift = int(n / 2)
    if max_tau:
        max_shift = min(int(fs * max_tau), max_shift)

    cc = np.concatenate((cc[-max_shift:], cc[: max_shift + 1]))

    # 使用插值提高精度
    if interp > 1:
        xp = np.linspace(0, len(cc) - 1, len(cc))
        x = np.linspace(0, len(cc) - 1, len(cc) * interp)
        cc = np.interp(x, xp, cc)

    # 找到最大值
    shift = np.argmax(cc) - len(cc) // 2
    tau = shift / (float(interp) * fs)

    return tau


def resample_audio(audio, orig_sr, target_sr):
    """重采样音频到目标采样率"""
    if orig_sr == target_sr:
        return audio

    # 计算重采样比例
    resample_ratio = target_sr / orig_sr

    # 重采样
    resampled = signal.resample(audio, int(len(audio) * resample_ratio))

    return resampled


def align_audio_arrays(ref_data, mic_data, sr=44100, max_tau=0.5):
    """
    对齐参考音频和麦克风音频，并返回对齐后的音频数组。

    参数:
        ref_data (np.ndarray): 参考音频信号
        mic_data (np.ndarray): 麦克风录音信号
        sr (int): 采样率
        max_tau (float): 最大延迟时间（秒）

    返回:
        ref_aligned (np.ndarray): 对齐后的参考音频
        mic_aligned (np.ndarray): 对齐后的麦克风音频
    """
    # 确保两个音频是单声道
    if ref_data.ndim > 1:
        ref_data = ref_data[:, 0]
    if mic_data.ndim > 1:
        mic_data = mic_data[:, 0]

    # 计算时间延迟
    tau = gcc_phat(
        mic_data[: sr * 10], ref_data[: sr * 10], fs=sr, max_tau=max_tau, interp=16
    )
    print(f"原始计算的时间延迟: {tau} 秒")

    # 转换为采样点，并保留符号
    tau_samples = int(round(tau * sr))
    print(f"转换后的时间延迟: {tau_samples} 采样点")

    # 对齐信号
    if tau_samples > 0:
        # mic 信号滞后于 ref 信号，前面补零
        mic_aligned = np.pad(mic_data, (tau_samples, 0), "constant")[: len(ref_data)]
        ref_aligned = ref_data[: len(mic_aligned)]
    elif tau_samples < 0:
        # mic 信号提前于 ref 信号，前面补零
        ref_aligned = np.pad(ref_data, (-tau_samples, 0), "constant")[: len(mic_data)]
        mic_aligned = mic_data[: len(ref_aligned)]
    else:
        # 没有延迟
        ref_aligned = ref_data
        mic_aligned = mic_data

    # 确保对齐后的信号长度一致
    min_len = min(len(ref_aligned), len(mic_aligned))
    ref_aligned = ref_aligned[:min_len]
    mic_aligned = mic_aligned[:min_len]

    return ref_aligned, mic_aligned, sr


class DualRecorder:
    def __init__(self):
        """初始化双通道录音器"""
        print("使用ModelScope的AEC管道进行回声消除")
        # 初始化ModelScope AEC管道
        self.aec_pipeline = pipeline(
            Tasks.acoustic_echo_cancellation, model="damo/speech_dfsmn_aec_psm_16k"
        )

    def record_dual_audio(self, duration=5, output_folder="recordings"):
        """同时录制麦克风输入和系统音频"""
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)

        # 录音参数设置
        sample_rate = 16000  # ModelScope模型可能要求16k采样率
        channels = 1  # ModelScope模型可能需要单声道

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
                break

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

        # 确保单声道
        mic_recording = mic_recording[:, 0] if mic_recording.ndim > 1 else mic_recording
        sys_recording = sys_recording[:, 0] if sys_recording.ndim > 1 else sys_recording

        # 对齐音频数据
        sys_recording, mic_recording, _ = align_audio_arrays(
            sys_recording, mic_recording, sr=sample_rate
        )

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
        print("正在应用ModelScope的AEC回声消除...")

        # 使用临时文件保存输入音频
        with tempfile.TemporaryDirectory() as tmpdirname:
            nearend_mic_path = os.path.join(tmpdirname, "nearend_mic.wav")
            farend_speech_path = os.path.join(tmpdirname, "farend_speech.wav")
            cleaned_output_path = os.path.join(tmpdirname, "cleaned_output.wav")

            # 保存对齐后的音频为临时文件
            sf.write(nearend_mic_path, mic_recording, sample_rate)
            sf.write(farend_speech_path, sys_recording, sample_rate)

            # 准备输入字典
            input_dict = {
                "nearend_mic": nearend_mic_path,
                "farend_speech": farend_speech_path,
            }

            # 调用AEC管道
            result = self.aec_pipeline(input_dict, output_path=cleaned_output_path)

            print("回声消除完成。")

            # 将清理后的音频复制到输出文件夹
            os.makedirs(output_folder, exist_ok=True)
            final_clean_file = os.path.join(output_folder, output_file)
            sf.copy(cleaned_output_path, final_clean_file)

            print(f"回声消除后的音频已保存至 {final_clean_file}")

        return {
            "mic_file": mic_file,
            "sys_file": sys_file,
            "clean_file": final_clean_file,
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
    # 移除模型路径参数，因为使用ModelScope的预训练模型

    args = parser.parse_args()

    # 创建录音器实例，使用ModelScope AEC
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
