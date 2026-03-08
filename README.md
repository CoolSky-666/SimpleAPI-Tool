# SimpleAPI Tool

一个基于SimpleTeX API的公式识别工具，用于将截图中的数学公式转换为LaTeX代码。

## 项目简介

SimpleAPI Tool是一个由coolsky通过Trae进行Vibecoding开发的桌面应用程序，旨在通过调用SimpleTeX的API实现快速、准确的数学公式识别。用户只需截图数学公式并粘贴到应用中，即可获得对应的LaTeX代码，支持MathML格式一键粘贴到word。你可以通过conda配置环境后运行python文件，也可以直接从dist目录中下载exe文件运行(PyInstaller打包的)。

## 功能特点

- 🚀 **两种识别模式**：极速模式和标准模式
- 📋 **多种复制格式**：纯LaTeX、行内LaTeX、块级LaTeX、MathML（Word兼容）
- 🎨 **现代UI设计**：简洁美观的用户界面
- 🔒 **安全存储**：本地存储API密钥
- 📊 **置信度展示**：实时显示识别置信度
- ⌨️ **快捷键支持**：Ctrl+V粘贴截图，Enter开始识别

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/simpleapi.git
cd simpleapi
```

### 2. 创建虚拟环境

```bash
python -m venv venv_clean
venv_clean\Scripts\activate
```

### 3. 安装依赖

```bash
pip install requests pillow latex2mathml
```

### 4. 获取API密钥

1. 访问 [SimpleTeX官网](https://simpletex.cn)
2. 注册并登录账号, 充值20元后每月可**免费识别2000次**
3. 在用户中心获取API Token

### 5. 运行应用

```bash
python simpleapi_app.py
```

## 使用方法

1. **设置API Token**：首次运行时会提示输入，或在应用顶部输入框中输入并点击"保存配置"
2. **选择识别模式**：根据需要选择"极速"或"标准"模式
3. **粘贴截图**：使用Ctrl+V粘贴包含数学公式的截图
4. **识别公式**：点击"识别公式"按钮或按Enter键
5. **复制结果**：根据需要选择不同格式的复制选项

## 项目结构

```
simpleapi/
├── simpleapi_app.py     # 主应用文件
├── config.json          # 配置文件（存储API密钥）
├── logo.ico             # 应用图标
├── README.md            # 项目说明文件
├── build/               # 打包输出目录
└── dist/                # 可执行文件目录
```

## 技术栈

- **Python 3.7+**：主要开发语言
- **tkinter**：GUI框架
- **PIL (Pillow)**：图像处理
- **requests**：API调用
- **latex2mathml**：LaTeX转MathML

## 打包应用

### 生成无命令行日志的应用exe文件

```bash
pyinstaller --onefile --windowed --noconfirm --clean --add-data "C:\Users\21123\anaconda3\envs\simpletex_pkg\Lib\site-packages\latex2mathml;latex2mathml"  --add-data "logo.ico;." -i "logo.ico" simpleapi_app.py
```

### 生成调试exe文件

```bash
pyinstaller --onedir --console --noconfirm --clean --add-data "C:\Users\21123\anaconda3\envs\simpletex_pkg\Lib\site-packages\latex2mathml;latex2mathml"  --add-data "logo.ico;." -i "logo.ico" simpleapi_app.py
```

> 注意：直接打包会漏掉`latex2mathml`的部分文件，因此需要通过`add-data`手动添加。

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 致谢

- [SimpleTeX](https://simpletex.cn) - 提供强大的公式识别API
- [latex2mathml](https://github.com/roniemartinez/latex2mathml) - LaTeX到MathML的转换库

## 支持

如果您在使用过程中遇到问题，请在GitHub上提交Issue。

---

**享受公式识别的便捷体验！** 🎉
