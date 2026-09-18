# 东软教务系统自动 Python 爬虫

当前版本：`v0.1.0`

这是一个针对东软教务系统的自动 Python 爬虫，基于 Playwright 实现。程序打开可见浏览器，用户通过二维码完成登录后，程序读取首页和课表页面内容，并保存 HTML、TXT 和截图。

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

`course_grab_interface.py` 已为日后的自动抢课功能预留基础接口，定义了 `CourseTarget`、`CourseCandidate` 和 `CourseGrabber`，并提供禁止真实提交的 `NotImplementedCourseGrabber` 占位实现。

由于东软教务系统存在明确的抢课时间限制，且实际抢课规则、开放时间和提交流程仍需进一步确认，目前暂未实现真实的自动抢课功能。当前版本只负责登录、抓取和保存教务信息，不会向教务系统提交选课请求。

## 安全说明

- 不要提交 `browser_profile/`，其中可能包含登录态。
- 不要提交 `crawl_output/`，其中可能包含姓名、学号和课程信息。
- 仅对本人有权访问的教务系统账号和数据使用本项目。
