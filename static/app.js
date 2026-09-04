// PhotoShare 前端交互：图片灯箱
(function () {
  var lb = document.getElementById('lightbox');
  var lbImg = document.getElementById('lightbox-img');
  var closeBtn = document.getElementById('lightbox-close');
  if (!lb || !lbImg) return;

  function open(src) {
    if (!src) return;
    lbImg.src = src;
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
  }

  function close() {
    lb.hidden = true;
    lbImg.removeAttribute('src');
    document.body.style.overflow = '';
  }

  // 点击带 data-lightbox 的图片 -> 放大预览，不触发父级链接跳转
  document.addEventListener('click', function (e) {
    var target = e.target;
    var img = target && target.closest ? target.closest('img[data-lightbox]') : null;
    if (img) {
      e.preventDefault();
      open(img.getAttribute('src') || img.currentSrc);
      return;
    }
    if (target === lb) close();
  });

  closeBtn.addEventListener('click', close);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !lb.hidden) close();
  });
})();