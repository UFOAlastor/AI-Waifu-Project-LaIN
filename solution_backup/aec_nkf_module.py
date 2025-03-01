import sounddevice as sd
import numpy as np
import wavio
import soundfile as sf
import torch
import torch.nn as nn
import time
import os
from scipy import signal
import threading
import librosa


# 定义NKF模型架构
class ComplexGRU(nn.Module):
    def __init__(
        self,
        input_size,
        hidden_size,
        num_layers=1,
        batch_first=True,
        bias=True,
        dropout=0,
        bidirectional=False,
    ):
        super().__init__()
        self.gru_r = nn.GRU(
            input_size,
            hidden_size,
            num_layers,
            bias=bias,
            batch_first=batch_first,
            dropout=dropout,
            bidirectional=bidirectional,
        )
        self.gru_i = nn.GRU(
            input_size,
            hidden_size,
            num_layers,
            bias=bias,
            batch_first=batch_first,
            dropout=dropout,
            bidirectional=bidirectional,
        )

    def forward(self, x, h_rr=None, h_ir=None, h_ri=None, h_ii=None):
        Frr, h_rr = self.gru_r(x.real, h_rr)
        Fir, h_ir = self.gru_r(x.imag, h_ir)
        Fri, h_ri = self.gru_i(x.real, h_ri)
        Fii, h_ii = self.gru_i(x.imag, h_ii)
        y = torch.complex(Frr - Fii, Fri + Fir)
        return y, h_rr, h_ir, h_ri, h_ii


class ComplexDense(nn.Module):
    def __init__(self, in_channel, out_channel, bias=True):
        super().__init__()
        self.linear_real = nn.Linear(in_channel, out_channel, bias=bias)
        self.linear_imag = nn.Linear(in_channel, out_channel, bias=bias)

    def forward(self, x):
        y_real = self.linear_real(x.real)
        y_imag = self.linear_imag(x.imag)
        return torch.complex(y_real, y_imag)


class ComplexPReLU(nn.Module):
    def __init__(self):
        super().__init__()
        self.prelu = torch.nn.PReLU()

    def forward(self, x):
        return torch.complex(self.prelu(x.real), self.prelu(x.imag))


class KGNet(nn.Module):
    def __init__(self, L, fc_dim, rnn_layers, rnn_dim):
        super().__init__()
        self.L = L
        self.rnn_layers = rnn_layers
        self.rnn_dim = rnn_dim

        self.fc_in = nn.Sequential(
            ComplexDense(2 * self.L + 1, fc_dim, bias=True), ComplexPReLU()
        )

        self.complex_gru = ComplexGRU(fc_dim, rnn_dim, rnn_layers, bidirectional=False)

        self.fc_out = nn.Sequential(
            ComplexDense(rnn_dim, fc_dim, bias=True),
            ComplexPReLU(),
            ComplexDense(fc_dim, self.L, bias=True),
        )

    def init_hidden(self, batch_size, device):
        self.h_rr = torch.zeros(self.rnn_layers, batch_size, self.rnn_dim).to(
            device=device
        )
        self.h_ir = torch.zeros(self.rnn_layers, batch_size, self.rnn_dim).to(
            device=device
        )
        self.h_ri = torch.zeros(self.rnn_layers, batch_size, self.rnn_dim).to(
            device=device
        )
        self.h_ii = torch.zeros(self.rnn_layers, batch_size, self.rnn_dim).to(
            device=device
        )

    def forward(self, input_feature):
        feat = self.fc_in(input_feature).unsqueeze(1)
        rnn_out, self.h_rr, self.h_ir, self.h_ri, self.h_ii = self.complex_gru(
            feat, self.h_rr, self.h_ir, self.h_ri, self.h_ii
        )
        kg = self.fc_out(rnn_out).permute(0, 2, 1)
        return kg


class NKF(nn.Module):
    def __init__(self, L=4):
        super().__init__()
        self.L = L
        self.kg_net = KGNet(L=self.L, fc_dim=18, rnn_layers=1, rnn_dim=18)
        self.stft = lambda x: torch.stft(
            x,
            n_fft=1024,
            hop_length=256,
            win_length=1024,
            window=torch.hann_window(1024).to(x.device),
            return_complex=True,
        )
        self.istft = lambda X: torch.istft(
            X,
            n_fft=1024,
            hop_length=256,
            win_length=1024,
            window=torch.hann_window(1024).to(X.device),
            return_complex=False,
        )

    def forward(self, x, y):
        if x.dim() == 1:
            x = x.unsqueeze(0)
        if y.dim() == 1:
            y = y.unsqueeze(0)
        x = self.stft(x)
        y = self.stft(y)
        B, F, T = x.shape
        device = x.device
        h_prior = torch.zeros(B * F, self.L, 1, dtype=torch.complex64, device=device)
        h_posterior = torch.zeros(
            B * F, self.L, 1, dtype=torch.complex64, device=device
        )
        self.kg_net.init_hidden(B * F, device)

        x = x.contiguous().view(B * F, T)
        y = y.contiguous().view(B * F, T)
        echo_hat = torch.zeros(B * F, T, dtype=torch.complex64, device=device)

        for t in range(T):
            if t < self.L:
                xt = torch.cat(
                    [
                        torch.zeros(
                            B * F, self.L - t - 1, dtype=torch.complex64, device=device
                        ),
                        x[:, : t + 1],
                    ],
                    dim=-1,
                )
            else:
                xt = x[:, t - self.L + 1 : t + 1]
            if xt.abs().mean() < 1e-5:
                continue

            dh = h_posterior - h_prior
            h_prior = h_posterior
            e = y[:, t] - torch.matmul(xt.unsqueeze(1), h_prior).squeeze()

            input_feature = torch.cat([xt, e.unsqueeze(1), dh.squeeze()], dim=1)
            kg = self.kg_net(input_feature)
            h_posterior = h_prior + torch.matmul(kg, e.unsqueeze(-1).unsqueeze(-1))

            echo_hat[:, t] = torch.matmul(xt.unsqueeze(1), h_posterior).squeeze()

        s_hat = self.istft(y - echo_hat).squeeze()

        return s_hat


# GCC-PHAT时延估计
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


# 同时记录系统音频和麦克风输入
class DualRecorder:
    def __init__(self, model_path=None):
        """初始化双通道录音器"""
        # 加载NKF模型
        self.model = NKF(L=4)
        self.model.load_state_dict(
            torch.load(model_path, map_location=torch.device("cpu")), strict=True
        )
        self.model.eval()
        print("已加载回声消除模型")

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

        # 空数据检测
        if mic_recording is None or sys_recording is None:
            print("录音失败: 未获取到有效音频数据")
            return None

        # 双通道取平均
        mic_recording = mic_recording[:, 0]
        sys_recording = sys_recording[:, 1]

        # # 对齐音频数据
        # sys_recording, mic_recording, _ = align_audio_arrays(
        #     sys_recording, mic_recording
        # )

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
        if self.model:
            print("正在应用NKF回声消除...")

            # 转换为PyTorch张量
            mic_tensor = torch.FloatTensor(mic_recording)
            sys_tensor = torch.FloatTensor(sys_recording)

            # 应用NKF模型
            with torch.no_grad():
                clean_audio = self.model(sys_tensor, mic_tensor)

            # 保存处理后的音频
            clean_audio_np = clean_audio.numpy()
            # 裁剪异常值
            clean_audio_np = np.clip(clean_audio_np, -1, 1)
            sf.write(output_file, clean_audio_np, sample_rate)
            print(f"回声消除后的音频已保存至 {output_file}")

            return {
                "mic_file": mic_file,
                "sys_file": sys_file,
                "clean_file": output_file,
            }
        else:
            return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="回声消除录音系统")
    parser.add_argument(
        "--record", action="store_true", default=True, help="录制新的音频"
    )
    parser.add_argument("--duration", type=int, default=5, help="录音时长（秒）")
    parser.add_argument(
        "--output_folder", type=str, default="audio", help="录音输出文件夹"
    )
    parser.add_argument(
        "--model", type=str, default="./NKF-AEC/nkf_epoch70.pt", help="NKF模型路径"
    )
    parser.add_argument(
        "--align", action="store_true", default=True, help="是否对齐音频"
    )

    args = parser.parse_args()

    # 创建双通道录音器
    recorder = DualRecorder(model_path=args.model)

    if args.record:
        # 录制模式
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
