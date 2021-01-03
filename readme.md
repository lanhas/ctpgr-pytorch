## The Chinese Traffic Police Gesture Recognizer

### 中国交通警察指挥手势识别

This is a pytorch deep learning project that recognizes 8 kinds of Traffic police commanding gestures.

<p align="center">
    <img src="docs/intro.gif" width="480">
</p>

## Paper
电子学报： http://www.ejournal.org.cn/CN/10.3969/j.issn.0372-2112.2020.05.018 

## Quick Start

### Download checkpoints from [GoogleDrive](https://drive.google.com/drive/folders/1kngUBiiUWUOt1NeasHS9IMGQvJrFoxpO?usp=sharing), put them into:

从上述GoogleDrive下载模型参数，放置在：
```
(project folder)/checkpoints
(project folder)/generated  # optional
```

### Download PoliceGesture dataset (required) and AI Challenger dataset (optional), put them into

下载交警手势数据集（必选）和AI Challenger数据集（可选），放置在：
```
(home folder)/PoliceGestureLong
(home folder)/AI_challenger_keypoint
# home folder is 'C:\Users\(name)' in Windows and `/home/(name)` in Ubuntu
```
### Police Gesture Dataset download:

交警手势数据集下载：

[Google Drive](https://drive.google.com/drive/folders/13KHZpweTE1vRGAMF7wqMDE35kDw40Uym?usp=sharing)

[Nutstore 坚果云](https://www.jianguoyun.com/p/DQFgxv8Q9_LMBhiVrvYB)

### Install pytorch and other requirements:

安装Pytorch和其它依赖：
```
# Python 3.8.5
conda install pytorch torchvision torchaudio cudatoolkit=10.2 -c pytorch
conda install ujson
pip install visdom opencv-python imgaug
```

### Run ctpgr.py
#### Recognize video 0 in test folder

识别交警数据集中test文件夹第0个视频
```
python ctpgr.py -b 0
```

#### Recognize a custom video

识别自定义视频文件
```
python ctpgr.py -p C:\Users\zc\PoliceGestureLong\test\012.mp4
```