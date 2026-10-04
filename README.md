# 铟子vinds 小站

主站主页，和文章站（`article_web/`）用同一套配色与版式。

## 目录结构

```
/
├── index.html          主页（壁纸 + 三个方块）
├── style.css           全站样式（白天/夜间两套变量）
├── app.js              主题切换 + 图片预览 + 手机端目录
├── favicon.ico         站点图标
├── wallpaper.png       主页壁纸（1587×893）
├── site-data.js        自动生成：文件清单数据
├── build.py            文件页生成脚本
├── _headers            Cloudflare Pages 响应头（.vesta 用纯文本返回）
├── robots.txt
└── files/              所有对外文件
    ├── index.html      自动生成：文件总览
    ├── pdf/            PDF（可直接在浏览器里看，也可以下载）
    │   └── index.html  自动生成
    ├── png/            图片（缩略图 + 点击放大预览，也可以下载）
    │   └── index.html  自动生成
    └── other/          其他（VESTA 结构文件等，点击下载）
        └── index.html  自动生成
```

## 主页

- 顶部导航栏：左边「铟子vinds」指向本站主页，右侧只有白天/夜间切换按钮
- 一张壁纸（`wallpaper.png`，最大宽度 760px，窄屏按比例缩小）
- 三个方块：
  1. **社交媒体** —— Bilibili、知乎、个人QQ、QQ群1、QQ群2
  2. **文件** —— 标题点击进入 `/files`，下面列出 PDF / 图片 / 其他
  3. **子域名** —— 文章 → <https://article.vinds.top>
- 页脚：`GitHub | Copyright © 2026-present | 铟子vinds`

## 增删文件

1. 把文件放进 `files/pdf/`、`files/png/` 或 `files/other/`
2. 跑一次生成脚本：

   ```bash
   python build.py
   ```

它会重新生成 `files/index.html`、三个分类页和 `site-data.js`，
并把每个文件的大小（图片还会显示像素尺寸）写进去。

> 图片分类里的缩略图就是原图本身，靠 CSS 裁成小方块；点一下会全屏预览原图，
> 按 `Esc` 或点右上角 ✕ 关闭。

## 部署

| 设置项 | 值 |
| --- | --- |
| Framework preset | None |
| Build command | (留空) |
| Build output directory | `/` |

链接都用相对路径，所以放在域名根目录或者子目录里都能正常打开
（子域名方案就是把它放在 `vinds.top` 对应的项目里）。
