/* ==========================================================================
   铟子vinds 小站 — 全站脚本
   1. 白天 / 夜间模式切换
   2. 图片预览(点缩略图后全屏查看)
   ========================================================================== */
(function () {
'use strict';

var doc = document;
var themeBtn = null;

/* ------------------------------------------------------------ 主题切换 */

function currentTheme() {
	var saved = null;
	try { saved = localStorage.getItem('theme'); } catch (e) { saved = null; }
	if (saved === 'light' || saved === 'dark') return saved;
	return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
	doc.documentElement.setAttribute('data-theme', theme);
	if (themeBtn) {
		themeBtn.textContent = theme === 'dark' ? '☀' : '☾';
		themeBtn.setAttribute('aria-label', theme === 'dark' ? '切换到白天模式' : '切换到夜间模式');
	}
}

/* 本脚本在 <head> 里加载, 那时按钮还不存在, 所以初始化要等 DOM 就绪 */
function initTheme() {
	themeBtn = doc.getElementById('theme-btn');
	applyTheme(currentTheme());
	if (!themeBtn) return;
	themeBtn.addEventListener('click', function () {
		var next = doc.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
		try { localStorage.setItem('theme', next); } catch (e) { /* 忽略 */ }
		applyTheme(next);
	});
}

/* ------------------------------------------------------------ 图片预览 */

function initViewer() {
	var box = doc.getElementById('viewer');
	if (!box) return;

	var img = box.querySelector('img');
	var name = box.querySelector('.viewer-name');
	var close = box.querySelector('.viewer-close');

	function hide() {
		box.classList.remove('open');
		img.removeAttribute('src');
		if (name) name.textContent = '';
	}

	function show(thumb) {
		img.src = thumb.getAttribute('data-full') || thumb.getAttribute('src');
		img.alt = thumb.getAttribute('alt') || '';
		if (name) name.textContent = thumb.getAttribute('data-name') || img.alt;
		box.classList.add('open');
	}

	/* 缩略图点了就放大看 */
	doc.addEventListener('click', function (ev) {
		var t = ev.target;
		if (t && t.classList && t.classList.contains('thumb')) {
			ev.preventDefault();
			show(t);
			return;
		}
		if (t === box || (t && t.classList && t.classList.contains('viewer-close'))) {
			hide();
		}
	});

	doc.addEventListener('keydown', function (ev) {
		if (ev.key === 'Escape') hide();
	});
}

/* ------------------------------------------------------------ 启动 */

function start() {
	initTheme();
	initViewer();
}

if (doc.readyState === 'loading') {
	doc.addEventListener('DOMContentLoaded', start);
} else {
	start();
}

})();
