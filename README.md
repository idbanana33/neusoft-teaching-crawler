# 东软教务课表爬虫

当前版本：`v0.1.0`

这是一个基于 Playwright 的东软教务系统课表抓取工具。程序打开可见浏览器，用户通过二维码完成登录后，程序读取首页和课表页面内容，并保存 HTML、TXT 和截图。

## 功能

- 二维码/统一认证登录（由用户在浏览器中完成）
- 保存主页内容
- 读取“我的课程”和课表页面
- 滚动页面及内部滚动区域，尽量触发懒加载内容
- 输出课表 TXT、HTML 和 PNG
- 预留自动选课接口，但 `v0.1.0` 不会提交任何真实选课请求

## 安装

```powershell
pip install -r requirements.txt
playwright install chromium
```

## 运行

```powershell
python neusoft_crawler.py
```

首次运行会打开浏览器。请在浏览器中完成二维码登录。输出文件会写入 `crawl_output/`，登录会话会保存在 `browser_profile/`。

## 自动选课接口

`course_grab_interface.py` 定义了 `CourseTarget`、`CourseCandidate` 和 `CourseGrabber` 接口，并提供禁止真实提交的 `NotImplementedCourseGrabber` 占位实现。后续开发应在明确的人工确认、频率限制、失败处理和权限边界下进行，当前版本不会自动抢课。

## 安全说明

- 不要提交 `browser_profile/`，其中可能包含登录态。
- 不要提交 `crawl_output/`，其中可能包含姓名、学号和课程信息。
- 仅对本人有权访问的教务系统账号和数据使用本项目。
