echo 正在拉取SenseVoiceSmall模型
:: 确保你拥有git lfs
git lfs install
git clone https://huggingface.co/FunAudioLLM/SenseVoiceSmall
echo SenseVoiceSmall模型拉取完成！

:: SAM++依赖安装
echo 安装SAM++依赖库
pip install addict -i https://mirrors.aliyun.com/pypi/simple/
pip install simplejson -i https://mirrors.aliyun.com/pypi/simple/
pip install sortedcontainers -i https://mirrors.aliyun.com/pypi/simple/
