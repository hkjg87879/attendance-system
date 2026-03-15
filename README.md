# 企业考勤管理系统 - 移动端优化版

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个基于 Streamlit 和人脸识别技术的企业考勤管理系统，支持多种打卡方式和完整的考勤统计功能。

![GitHub repo size](https://img.shields.io/github/repo-size/hkjg87879/attendance-system)
![GitHub last commit](https://img.shields.io/github/last-commit/hkjg87879/attendance-system)

## ✨ 核心功能

### 🎯 考勤打卡
- **人脸识别打卡** - 基于 dlib 和 face_recognition 库，支持实时摄像头拍摄
- **GPS 定位打卡** - 基于地理位置的打卡方式
- **二维码打卡** - 动态二维码验证打卡
- **手动打卡** - 传统的手动确认打卡方式

### 👤 人脸管理
- **人脸注册** - 支持上传 3 张照片进行人脸特征注册
- **人脸识别** - 128 维特征向量比对，相似度≥60% 即为匹配成功
- **特征管理** - 自动计算多张照片的平均特征向量，提高识别准确率

### 📊 统计报表
- **月度统计** - 按部门和个人统计出勤情况
- **趋势分析** - 可视化展示考勤趋势
- **打卡方式统计** - 分析各种打卡方式的使用情况
- **考勤明细** - 详细的打卡记录查询

### 🔐 用户管理
- **多角色支持** - 管理员和普通员工两种角色
- **部门管理** - 支持多层级部门结构
- **权限控制** - 基于角色的功能访问控制

## 🚀 快速开始

### 本地运行

1. **克隆项目**
```bash
git clone https://github.com/hkjg87879/attendance-system.git
cd attendance-system
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **初始化数据库**
```bash
python init_db.py
```

4. **启动应用**
```bash
streamlit run app_mobile_optimized.py
```

### Streamlit Cloud 部署

1. 在 GitHub 创建仓库并上传项目文件
2. 访问 [Streamlit Cloud](https://share.streamlit.io)
3. 连接 GitHub 仓库
4. 配置：
   - **Main file path**: `app_mobile_optimized.py`
   - **Branch**: `main`
   - **Python version**: `3.8` 或更高
5. 点击 **Deploy!**

⚠️ **注意**: 
- `attendance.db` 已加入 `.gitignore`，不会上传到 GitHub
- 首次部署后需要运行 `init_db.py` 初始化数据库
- 人脸识别功能需要编译 dlib，首次部署可能需要 5-10 分钟

## 📦 项目结构

```
attendance-system/
├── app_mobile_optimized.py      # 主程序
├── face_recognition_module.py   # 人脸识别模块
├── init_db.py                   # 数据库初始化脚本
├── requirements.txt             # Python 依赖列表
├── .streamlit/
│   └── config.toml             # Streamlit 配置
├── .gitignore                  # Git 忽略配置
└── README.md                   # 项目说明文档
```

## 🔧 技术栈

- **前端框架**: [Streamlit](https://streamlit.io/)
- **数据处理**: Pandas, NumPy
- **数据库**: SQLite
- **人脸识别**: 
  - [dlib](http://dlib.net/)
  - [face_recognition](https://github.com/ageitgey/face_recognition)
- **图像处理**: Pillow (PIL)
- **可视化**: Altair, Pandas
- **日期处理**: pytz, python-dateutil

## 📋 默认账号

### 管理员账号
- **用户名**: `admin`
- **密码**: `admin123`

### 预置员工账号
| 用户名 | 姓名 | 角色 | 人脸注册 |
|--------|------|------|----------|
| user1 | 张三 | 员工 | ❌ |
| user2 | 李四 | 员工 | ❌ |
| user3 | 王五 | 员工 | ❌ |
| user4 | 赵六 | 员工 | ❌ |
| user5 | 刘峰 | 员工 | ✅ |
| user6 | zywoo | 员工 | ❌ |
| user7 | 李芸 | 员工 | ✅ |

## 🎯 使用指南

### 人脸注册流程

1. 登录系统后进入**个人中心**
2. 点击**人脸注册**按钮
3. 上传 3 张清晰的正面照片（或使用摄像头拍摄）
4. 点击**提取特征并保存**
5. 系统自动提取 128 维人脸特征向量并保存

### 人脸识别打卡

1. 进入**人脸打卡**页面
2. 使用摄像头拍摄照片
3. 系统自动识别人脸并计算相似度
4. 相似度≥60% 时勾选**已验证成功**
5. 点击**确认上班/下班打卡**

### 其他打卡方式

- **GPS 打卡**: 需要授权地理位置权限
- **二维码打卡**: 扫描管理员生成的动态二维码
- **手动打卡**: 直接点击打卡按钮确认

## ⚠️ 注意事项

### 人脸识别
- 确保光线充足，面部无遮挡
- 正对摄像头，保持适当距离
- 注册和打卡时尽量保持相似的角度和表情
- 支持摄像头拍摄和文件上传两种方式

### 数据库
- 本地使用：数据保存在 `attendance.db`
- Streamlit Cloud: 使用临时文件系统，重启后数据可能丢失
- 生产环境：建议使用外部数据库（如 PostgreSQL、MySQL）

### 性能优化
- 首次启动时需要编译 dlib，可能需要较长时间
- 建议一次性注册多张照片以提高识别准确率
- 定期清理考勤数据以保持系统性能

## 📊 系统截图

### 登录页面
![Login](screenshots/login.png)

### 人脸注册
![Face Registration](screenshots/face_registration.png)

### 人脸识别打卡
![Face Check-in](screenshots/face_checkin.png)

### 统计报表
![Statistics](screenshots/statistics.png)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v1.0.0 (2026-03-15)
- ✨ 完整的人脸识别打卡功能
- 🐛 修复人脸注册数据保存问题
- ⚡ 优化文件上传和特征提取流程
- 📱 移动端优化界面
- 🔧 支持多种打卡方式并存

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 作者

- **hkjg87879** - *Initial work* - [hkjg87879](https://github.com/hkjg87879)

## 🙏 致谢

- [Streamlit](https://streamlit.io/) - 优秀的 Web 应用框架
- [face_recognition](https://github.com/ageitgey/face_recognition) - 简单易用的人脸识别库
- [dlib](http://dlib.net/) - 强大的机器学习工具包

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [提交 Issue](https://github.com/hkjg87879/attendance-system/issues)
- Email: [您的邮箱]

---

<div align="center">

**如果这个项目对您有帮助，请给一个 ⭐ Star！**

[⬆ 回到顶部](#企业考勤管理系统---移动端优化版)

</div>
