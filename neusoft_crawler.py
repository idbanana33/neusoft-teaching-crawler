"""东软教务系统：二维码登录后保存主页面内容。

首次运行会打开可见浏览器。请在浏览器中完成二维码扫描/统一认证，
脚本检测到登录成功后，会保存 HTML、纯文本和截图。
"""

from pathlib import Path
from datetime import datetime
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


START_URL = (
    "https://teach.neusoft.edu.cn/jwapp/sys/homeapp/home/index.html"
    "?av=&contextPath=/jwapp#/"
)
PROFILE_DIR = Path(__file__).with_name("browser_profile")
OUTPUT_DIR = Path(__file__).with_name("crawl_output")


def scroll_page_and_panels(page) -> None:
    """滚动页面及内部滚动容器，触发懒加载并显示隐藏的课程卡片。"""
    for _ in range(20):
        before = page.evaluate("window.scrollY")
        page.mouse.wheel(0, 900)
        page.wait_for_timeout(250)
        after = page.evaluate("window.scrollY")
        if after == before:
            break

    # “我的课程”常见实现是卡片区域自身滚动，而不是整个窗口滚动。
    page.evaluate(
        """() => {
            const nodes = [...document.querySelectorAll('*')];
            for (const el of nodes) {
                const s = getComputedStyle(el);
                if ((s.overflowY === 'auto' || s.overflowY === 'scroll') &&
                    el.scrollHeight > el.clientHeight + 20) {
                    el.scrollTop = el.scrollHeight;
                }
            }
        }"""
    )
    page.wait_for_timeout(1200)


def save_page(page, name: str) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = OUTPUT_DIR / f"{name}_{stamp}.html"
    text_path = OUTPUT_DIR / f"{name}_{stamp}.txt"
    image_path = OUTPUT_DIR / f"{name}_{stamp}.png"

    html_path.write_text(page.content(), encoding="utf-8")
    text_path.write_text(page.locator("body").inner_text(), encoding="utf-8")
    page.screenshot(path=str(image_path), full_page=True)

    print(f"已保存 HTML：{html_path}")
    print(f"已保存文本：{text_path}")
    print(f"已保存截图：{image_path}")


def save_debug_info(page, name: str) -> None:
    """按钮匹配失败时保存现场，便于根据真实 DOM 调整选择器。"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = OUTPUT_DIR / f"debug_{name}_{stamp}.html"
    image_path = OUTPUT_DIR / f"debug_{name}_{stamp}.png"
    text_path = OUTPUT_DIR / f"debug_{name}_{stamp}.txt"

    html_path.write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(image_path), full_page=True)
    body_text = page.locator("body").inner_text(timeout=10000)
    relevant = [
        line.strip()
        for line in body_text.splitlines()
        if any(word in line for word in ("课表", "打印", "Word", "word"))
    ]
    text_path.write_text("\n".join(relevant), encoding="utf-8")
    print(f"已保存调试 HTML：{html_path}")
    print(f"已保存调试截图：{image_path}")
    print(f"相关页面文字：{relevant}")


def text_locator(page, text: str):
    """匹配包含指定文字的元素，兼容空格、箭头和嵌套 span。"""
    return page.get_by_text(re.compile(re.escape(text)), exact=False).first


def click_tab(page, title: str) -> bool:
    """点击页面上的指定中文模块/标签，成功返回 True。"""
    tab = page.get_by_text(title, exact=True).first
    try:
        if not tab.is_visible(timeout=3000):
            return False
        tab.scroll_into_view_if_needed()
        tab.click()
        page.wait_for_timeout(1200)
        return True
    except (PlaywrightTimeoutError, Exception):
        return False


def download_schedule_docx(page) -> bool:
    """进入课表页面并点击“学期课表打印”，保存系统生成的 DOCX。"""
    # 首页入口是一个 div 容器；优先使用其实际 DOM 类名，再回退到文字定位。
    view_schedule = page.locator("div.wdkbContainer___1SUk7").filter(
        has_text="查看我的课表"
    ).first
    if view_schedule.count() == 0:
        view_schedule = page.get_by_text("查看我的课表", exact=True).first
    try:
        if not view_schedule.is_visible(timeout=3000):
            print("未找到“查看我的课表”按钮。")
            return False
        old_pages = list(page.context.pages)
        view_schedule.scroll_into_view_if_needed()
        view_schedule.click(force=True)
        page.wait_for_timeout(3000)
        new_pages = [item for item in page.context.pages if item not in old_pages]
        work_page = new_pages[-1] if new_pages else page
        # 某些版本把点击事件挂在入口的父容器上；若第一次点击没有打开课表，
        # 再点击一次父容器，避免只点到内部文字节点。
        if not new_pages and work_page.get_by_text(
            "学期课表打印", exact=False
        ).count() == 0:
            parent = page.locator(
                "div.wdkbContainer___1SUk7"
            ).filter(has_text="查看我的课表").locator("xpath=..")
            parent.click(force=True)
            page.wait_for_timeout(3000)
            new_pages = [item for item in page.context.pages if item not in old_pages]
            work_page = new_pages[-1] if new_pages else page
        if new_pages:
            try:
                work_page.wait_for_load_state("domcontentloaded", timeout=30000)
            except PlaywrightTimeoutError:
                pass
            print("“查看我的课表”打开了新页面：", work_page.url)
        else:
            print("已点击“查看我的课表”，当前地址：", work_page.url)
    except Exception as exc:
        print(f"点击“查看我的课表”失败：{exc}")
        save_debug_info(page, "view_schedule")
        return False

    # 不再用“我的课表”判断页面，因为首页入口本身也含有这几个字。
    # 直接等待课表页独有的“学期课表打印”控件。
    print_button = work_page.get_by_text("学期课表打印", exact=True).first
    if print_button.count() == 0:
        print_button = text_locator(work_page, "学期课表打印")
    try:
        print("正在等待“学期课表打印”按钮加载，最多等待 2 分钟……")
        print_button.wait_for(state="visible", timeout=120000)
    except PlaywrightTimeoutError:
        print("未找到“学期课表打印”按钮。")
        save_debug_info(page, "print_button")
        return False

    try:
        # “学期课表打印”是下拉按钮，点击它只会展开 Word/PDF 等格式选项。
        print_button.click()
        word_option = text_locator(work_page, "Word")
        word_option.wait_for(state="visible", timeout=10000)
    except Exception as exc:
        print(f"展开打印菜单或找到 Word 选项失败：{exc}")
        save_debug_info(work_page, "word_option")
        return False

    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = OUTPUT_DIR / f"semester_schedule_{stamp}.docx"
    try:
        with work_page.expect_download(timeout=30000) as download_info:
            word_option.click()
        download_info.value.save_as(str(target))
        print(f"已保存课表 DOCX：{target}")
        return True
    except PlaywrightTimeoutError:
        print("点击后没有检测到 DOCX 下载，请检查页面是否弹出了打印/预览窗口。")
        return False


def crawl_home_modules(page) -> None:
    """读取主页、我的课程和我的课表等模块。"""
    # 主页上的公告、应用、学习日程、课程卡片等。
    scroll_page_and_panels(page)
    save_page(page, "home")

    # “我的课程”通常是主页内的标签，点击后再滚动到底部获取剩余课程。
    if click_tab(page, "我的课程"):
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        scroll_page_and_panels(page)
        save_page(page, "my_courses")
    else:
        print("未找到“我的课程”标签，已保留主页内容。")

    # “我的课表”可能与“我的课程”共用同一组标签。
    if click_tab(page, "我的课表"):
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        scroll_page_and_panels(page)
        save_page(page, "my_schedule")
    else:
        print("未找到“我的课表”标签。")

    # 前面的标签抓取可能改变了页面路由，回到首页后走官方入口下载 DOCX。
    page.goto(START_URL, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_function(
            "() => document.body && document.body.innerText.length > 80",
            timeout=30000,
        )
    except PlaywrightTimeoutError:
        pass
    download_schedule_docx(page)


def looks_logged_in(page) -> bool:
    url = page.url.lower()
    # 登录成功后通常会回到 jwapp 的业务页面；VPN/认证页不满足此条件。
    if "teach.neusoft.edu.cn/jwapp" not in url:
        return False
    try:
        body = page.locator("body").inner_text(timeout=3000).strip()
        return len(body) > 80
    except PlaywrightTimeoutError:
        return False


def main() -> None:
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(START_URL, wait_until="domcontentloaded", timeout=60000)

        print("浏览器已打开。请完成二维码扫描/登录；脚本会自动等待。")
        print("如果页面已登录，也会直接继续。最多等待 5 分钟。")

        try:
            page.wait_for_function(
                """() => {
                    const u = location.href.toLowerCase();
                    const text = document.body ? document.body.innerText : '';
                    return u.includes('teach.neusoft.edu.cn/jwapp') && text.length > 80;
                }""",
                timeout=300000,
                polling=1000,
            )
        except PlaywrightTimeoutError:
            print("等待登录超时。当前地址：", page.url)
            context.close()
            return

        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            # 教务系统可能持续保持接口连接，不影响读取当前 DOM。
            pass
        if not looks_logged_in(page):
            print("未确认登录成功，当前地址：", page.url)
        else:
            crawl_home_modules(page)
        context.close()


if __name__ == "__main__":
    main()
