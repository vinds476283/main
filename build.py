#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铟子vinds 小站 — 文件页生成脚本

用法(在本文件所在目录执行):
    python build.py

它会读取 ./files/ 目录, 生成:
    index.html                小站主页(图标 + 三个方块)
    files/index.html          文件总览(列出所有分类)
    files/<分类>/index.html   每个分类下列出所有文件, 图片可以直接预览

只依赖 Python 标准库。往 files/ 里增删文件之后重新跑一次即可。
"""

import os
import json
import struct
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------- 站点配置
SITE_TITLE = "vinds"                       # 浏览器标题前缀: "vinds | …"
SITE_AUTHOR = "铟子vinds"
SITE_HOME = "https://y.vinds.top"          # 页脚里的"铟子vinds"链接
SITE_REPO = "https://github.com/vinds476283/article"

# 各个文件分类: 目录名 -> 显示名
CATEGORIES = [
    ("pdf", "PDF"),
    ("png", "图片"),
    ("other", "其他"),
]

# 主页方块: 社交媒体
SOCIAL_LINKS = [
    ("Bilibili", "https://space.bilibili.com/1660195030"),
    ("知乎", "https://www.zhihu.com/people/vinds476283"),
    ("个人QQ", "https://qm.qq.com/cgi-bin/qm/qr?k=-KSy3idVKY-m-He9e9tio1zAovXOsjDL"),
    ("QQ群1", "https://qun.qq.com/universal-share/share?ac=1&authKey=jSR9CCUMH3iHudFvwbqYh0NH3ev1ZngkVbwecY9V7mcYqbhfo6BmQCMTEmtP7iWw&busi_data=eyJncm91cENvZGUiOiI3OTMyNDk3OTciLCJ0b2tlbiI6IjNZMUVXZUwwUEtPZU1wTUs3R1BrUm8zdWhyQ3U3NHpBMjEwNWN0VDRVYjFsZFd5SDlqVFRFdEpNK3ZIWUQ3ZXYiLCJ1aW4iOiIxMzU1MzEwMjAwIn0=&data=nz5m8RomgxfRneqE97q94nlAzDxM0J1oAPjvj7syhi8YFf_QTp2EMAgBDkLrOB1y9Ib3Njr2RPhC1NJQRcM4yURxeg0M-qLwEBJU8eWzzlo&svctype=5&tempid=h5_group_info"),
    ("QQ群2", "https://qun.qq.com/universal-share/share?ac=1&authKey=C7DtsDgOe8oerdpWAD3Znb6JImXnysqqf%2BfG4LWhb7x5plKZiTJoIhMZjExlOmSc&busi_data=eyJncm91cENvZGUiOiI5Nzg0MDM2MDYiLCJ0b2tlbiI6Ilo0OVZEOHBxK2NWM01ncDRtTmxPMlllNmh4STM2NmU4ZnJqY0YydlloUEJMQ2xMN3BjOVk3ckFLOFQwK3VMRHQiLCJ1aW4iOiIxMzU1MzEwMjAwIn0%3D&data=8DYRfIDt9BHv06IpWFdFL1mXFbyb2uf25RgZR7ovn6isibAC1yTvBWyljTu1VcmpftSzUqy8Q9GBd3_BLLzod6PYGG3JY05tXceBa1obPVg&svctype=5&tempid=h5_group_info"),
]

# 主页方块: 子域名
SUBDOMAINS = [
    ("文章", "https://article.vinds.top"),
]

WALLPAPER = "wallpaper.png"
HOME_TITLE = "铟子vinds的小站"

IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".avif")

FOOT = (
    '<footer class="foot">\n'
    '\t\t<p><a href="{repo}" target="_blank">GitHub</a> | '
    'Copyright © 2026-present | '
    '<a href="{home}" target="_blank">铟子vinds</a></p>\n'
    '\t</footer>'
).format(repo=SITE_REPO, home=SITE_HOME)


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def quote_path(p: str) -> str:
    """按路径段转义(与 JavaScript 的 encodeURI 行为一致)"""
    from urllib.parse import quote
    return "/".join(quote(seg, safe="!'()*-._~+/&$=:@") for seg in p.split("/"))


def human_size(n: int) -> str:
    if n < 1024:
        return "{} B".format(n)
    if n < 1024 * 1024:
        return "{:.0f} KB".format(n / 1024)
    if n < 1024 * 1024 * 1024:
        return "{:.1f} MB".format(n / (1024 * 1024))
    return "{:.2f} GB".format(n / (1024 * 1024 * 1024))


def image_size(path: str):
    """尽量读出图片的像素尺寸, 读不出来就返回 None"""
    try:
        with open(path, "rb") as fh:
            head = fh.read(32)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return w, h
            if head[:2] == b"\xff\xd8":       # JPEG: 扫描 SOFn 段
                fh.seek(2)
                while True:
                    b = fh.read(1)
                    while b and b != b"\xff":
                        b = fh.read(1)
                    while b == b"\xff":
                        b = fh.read(1)
                    if not b:
                        return None
                    marker = b[0]
                    if marker in (0xd8, 0xd9) or 0xd0 <= marker <= 0xd7:
                        continue
                    seg = fh.read(2)
                    if len(seg) < 2:
                        return None
                    length = struct.unpack(">H", seg)[0]
                    if 0xc0 <= marker <= 0xcf and marker not in (0xc4, 0xc8, 0xcc):
                        data = fh.read(5)
                        if len(data) < 5:
                            return None
                        h, w = struct.unpack(">HH", data[1:5])
                        return w, h
                    fh.seek(length - 2, 1)
            if head[:6] in (b"GIF87a", b"GIF89a"):
                w, h = struct.unpack("<HH", head[6:10])
                return w, h
    except Exception:
        return None
    return None


def collect_files():
    """扫描 files/ 目录, 返回 [(目录名, 显示名, [文件信息]), ...]"""
    out = []
    for dirname, label in CATEGORIES:
        abs_dir = os.path.join(HERE, "files", dirname)
        items = []
        if os.path.isdir(abs_dir):
            for name in sorted(os.listdir(abs_dir), key=lambda s: s.lower()):
                full = os.path.join(abs_dir, name)
                if not os.path.isfile(full) or name.startswith("."):
                    continue
                # 跳过本脚本自己生成的页面
                if name.lower() == "index.html":
                    continue
                size = os.path.getsize(full)
                info = {
                    "name": name,
                    "url": "files/{}/{}".format(dirname, quote_path(name)),
                    "size": human_size(size),
                    "bytes": size,
                }
                if name.lower().endswith(IMG_EXT):
                    dim = image_size(full)
                    if dim:
                        info["dim"] = "{}×{}".format(dim[0], dim[1])
                    info["image"] = True
                items.append(info)
        out.append((dirname, label, items))
    return out


# ----------------------------------------------------------------- 页面骨架
def page_shell(*, root, title, desc, body_class, content_html, need_viewer,
               show_home_link=True):
    """root: 回到站点根目录的相对前缀("<home>" 用 root + index.html 拼出来)"""
    home = root + "index.html"
    navlink = ('\t\t<a class="navlink" href="{home}">主页</a>\n'.format(home=home)
               if show_home_link else "")
    nav = (
        '<header class="nav">\n'
        '\t\t<a class="brand" href="{home}">铟子vinds</a>\n'
        '\t\t<span class="spacer"></span>\n'
        '{navlink}'
        '\t\t<button class="theme-btn" id="theme-btn" type="button" aria-label="切换夜间模式">☾</button>\n'
        '\t</header>'
    ).format(home=home, navlink=navlink)

    viewer = ""
    if need_viewer:
        viewer = (
            '<div class="viewer" id="viewer">\n'
            '\t\t<img src="" alt="">\n'
            '\t\t<button class="viewer-close" type="button" aria-label="关闭">✕</button>\n'
            '\t\t<p class="viewer-name"></p>\n'
            '\t</div>'
        )

    return (
        '<!DOCTYPE html>\n'
        '<html lang="zh-CN">\n'
        '<head>\n'
        '\t<meta charset="utf-8">\n'
        '\t<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '\t<title>{title}</title>\n'
        '\t<meta name="description" content="{desc}">\n'
        '\t<link rel="icon" href="{favicon}">\n'
        '\t<link rel="apple-touch-icon" href="{favicon}">\n'
        '\t<link rel="stylesheet" href="{css}">\n'
        '\t<script>(function(){{try{{var t=localStorage.getItem("theme");'
        'if(t!=="light"&&t!=="dark"){{t=window.matchMedia&&'
        'window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";}}'
        'document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>\n'
        '\t<script src="{app}"></script>\n'
        '</head>\n'
        '<body class="{body_class}">\n'
        '\t{nav}\n'
        '\t<main>\n{content}\n\t</main>\n'
        '\t{foot}\n'
        '\t{viewer}\n'
        '</body>\n'
        '</html>\n'
    ).format(
        title=esc(title),
        desc=esc(desc),
        favicon=root + "favicon.ico",
        css=root + "style.css",
        app=root + "app.js",
        body_class=body_class,
        nav=nav,
        content=content_html,
        foot=FOOT,
        viewer=viewer,
    )


def gen(out_path, html):
    full = os.path.join(HERE, out_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)


def build_files_page(root, is_root, categories, current=None):
    """生成一个文件页; root 是回到站点根目录的相对前缀"""
    if is_root:
        title = "文件"
        desc = "文件列表"
        body = ['<h1>文件</h1>']
        body.append('<p class="note">点分类进入, 图片可以直接点开预览, 其它文件点名字下载。</p>')
        body.append('<ul class="file-list">')
        total = 0
        for dirname, label, items in categories:
            total += len(items)
            body.append(
                '<li>\n'
                '\t\t\t<div class="meta">\n'
                '\t\t\t\t<div class="name"><a href="{href}">{label}</a></div>\n'
                '\t\t\t\t<div class="size">{n} 个文件</div>\n'
                '\t\t\t</div>\n'
                '\t\t</li>'.format(
                    href=quote_path(dirname) + "/", label=esc(label), n=len(items))
            )
        body.append('</ul>')
        body.append('<p class="note">共 {} 个文件。</p>'.format(total))
        crumbs = ('<p class="crumbs"><a href="{home}">主页</a> / 文件</p>'
                  .format(home=root + "index.html"))
        content = '\t\t<div class="wrap">\n\t\t' + crumbs + '\n\t\t' + \
            '\n\t\t'.join(body) + '\n\t\t</div>'
        title = SITE_TITLE + " | 文件"
        return page_shell(root=root, title=title, desc=desc,
                          body_class="page-files", content_html=content,
                          need_viewer=False)

    # 分类页
    label = dict((d, l) for d, l, _ in categories)[current]
    items = dict((d, it) for d, _, it in categories)[current]
    title = SITE_TITLE + " | 文件 · " + label
    desc = "文件 · " + label
    body = ['<h1>文件 · {}</h1>'.format(esc(label))]
    if items:
        body.append('<ul class="file-list">')
        for it in items:
            thumb = ""
            if it.get("image") and it["url"].lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".avif")):
                thumb = ('<img class="thumb" src="{src}" alt="{alt}" '
                         'data-full="{full}" data-name="{name}">').format(
                    src=esc(root + it["url"]), alt=esc(it["name"]),
                    full=esc(root + it["url"]), name=esc(it["name"]))
            meta = [it["size"]]
            if it.get("dim"):
                meta.append(it["dim"])
            body.append(
                '<li>\n'
                '\t\t\t{thumb}\n'
                '\t\t\t<div class="meta">\n'
                '\t\t\t\t<div class="name"><a href="{href}"{attr}>{name}</a></div>\n'
                '\t\t\t\t<div class="size">{meta}</div>\n'
                '\t\t\t</div>\n'
                '\t\t</li>'.format(
                    thumb=thumb,
                    href=esc(root + it["url"]),
                    attr=' download' if not it.get("image") else '',
                    name=esc(it["name"]),
                    meta=esc(" · ".join(meta)))
            )
        body.append('</ul>')
    else:
        body.append('<p class="empty">这个分类里还没有文件。</p>')

    crumbs = ('<p class="crumbs"><a href="{home}">主页</a> / '
              '<a href="{up}">文件</a> / {label}</p>').format(
        home=root + "index.html", up=root + "files/", label=esc(label))
    content = '\t\t<div class="wrap">\n\t\t' + crumbs + '\n\t\t' + \
        '\n\t\t'.join(body) + '\n\t\t</div>'
    return page_shell(root=root, title=title, desc=desc + " · " + label,
                      body_class="page-files", content_html=content,
                      need_viewer=True)


def build_home(categories):
    """主页: 无导航栏主页链接, 一张壁纸 + 三个方块"""
    total = sum(len(it) for _, _, it in categories)

    social = "".join(
        '<li><a href="{url}" target="_blank" rel="noopener">{label}</a></li>'.format(
            url=esc(url), label=esc(label))
        for label, url in SOCIAL_LINKS
    )
    subs = "".join(
        '<li><a href="{url}" target="_blank" rel="noopener">{label}</a></li>'.format(
            url=esc(url), label=esc(label))
        for label, url in SUBDOMAINS
    )

    content = (
        '\t\t<div class="wrap">\n'
        '\t\t<h1>{title}</h1>\n'
        '\t\t<img class="wallpaper" src="{wall}" alt="{title}">\n'
        '\t\t<div class="box-list">\n'
        '\t\t\t<div class="box">\n'
        '\t\t\t\t<h2>社交媒体</h2>\n'
        '\t\t\t\t<ul class="box-items">{social}</ul>\n'
        '\t\t\t</div>\n'
        '\t\t\t<div class="box">\n'
        '\t\t\t\t<h2><a href="files/">文件</a></h2>\n'
        '\t\t\t\t<ul class="box-items">{cats}</ul>\n'
        '\t\t\t\t<p class="note">共 {total} 个文件</p>\n'
        '\t\t\t</div>\n'
        '\t\t\t<div class="box">\n'
        '\t\t\t\t<h2>子域名</h2>\n'
        '\t\t\t\t<ul class="box-items">{subs}</ul>\n'
        '\t\t\t</div>\n'
        '\t\t</div>\n'
        '\t\t</div>'
    ).format(
        title=esc(HOME_TITLE),
        wall=esc(WALLPAPER),
        social=social,
        cats="".join(
            '<li><a href="{href}">{label}</a></li>'.format(
                href=esc("files/" + d + "/"), label=esc(l))
            for d, l, _ in categories),
        total=total,
        subs=subs,
    )

    return page_shell(
        root="",
        title=SITE_TITLE + " | " + HOME_TITLE,
        desc="{} 的主页".format(SITE_AUTHOR),
        body_class="page-home",
        content_html=content,
        need_viewer=False,
        show_home_link=False,
    )


def main():
    categories = collect_files()

    # 主页
    gen("index.html", build_home(categories))
    # 文件总览
    gen("files/index.html", build_files_page("../", True, categories))
    # 各分类
    for dirname, label, items in categories:
        gen(os.path.join("files", dirname, "index.html"),
            build_files_page("../../", False, categories, current=dirname))

    # 给脚本/自检用的数据
    data = {
        "title": SITE_TITLE,
        "author": SITE_AUTHOR,
        "categories": [
            {"dir": d, "name": l, "url": "files/" + d + "/", "count": len(it),
             "items": it}
            for d, l, it in categories
        ],
        "updated": datetime.date.today().isoformat(),
    }
    with open(os.path.join(HERE, "site-data.js"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("/* 由 build.py 自动生成, 请勿手工修改 */\n")
        fh.write("window.FILES = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")

    # 缺文件就说一声
    for need in ("style.css", "app.js", "favicon.ico", WALLPAPER):
        if not os.path.exists(os.path.join(HERE, need)):
            print("警告: 缺少文件 " + need)

    print("完成:")
    for d, l, it in categories:
        print("  - {} ({}): {} 个文件".format(d, l, len(it)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
