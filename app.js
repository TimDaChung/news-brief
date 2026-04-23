(function () {
  const articles = document.querySelectorAll('article');
  const chips = document.querySelectorAll('.chip');
  const searchInput = document.getElementById('search');
  const toast = document.getElementById('toast');

  let currentFilter = 'all';
  let currentKeyword = '';

  function applyFilters() {
    let twVisible = 0, intlVisible = 0;
    articles.forEach(a => {
      const cat = a.dataset.category;
      const matchCat = currentFilter === 'all' || cat === currentFilter;
      const text = a.textContent.toLowerCase();
      const matchKw = !currentKeyword || text.includes(currentKeyword);
      const show = matchCat && matchKw;
      a.classList.toggle('hidden', !show);
      if (show) {
        const region = a.closest('.news-list').dataset.region;
        if (region === 'tw') twVisible++;
        else if (region === 'intl') intlVisible++;
      }
    });
    document.querySelector('[data-count="tw"]').textContent = twVisible + ' 則';
    document.querySelector('[data-count="intl"]').textContent = intlVisible + ' 則';
    document.getElementById('totals').textContent = '台港澳 ' + twVisible + ' 則 · 國際 ' + intlVisible + ' 則';

    document.querySelectorAll('.news-list').forEach(list => {
      const visible = list.querySelectorAll('article:not(.hidden)').length;
      list.classList.toggle('empty', visible === 0);
    });
  }

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentFilter = chip.dataset.filter;
      applyFilters();
    });
  });

  searchInput.addEventListener('input', (e) => {
    currentKeyword = e.target.value.toLowerCase().trim();
    applyFilters();
  });

  // 複製摘要
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove('show'), 1800);
  }

  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const article = btn.closest('article');
      const title = article.querySelector('.title').textContent.trim();
      const origEl = article.querySelector('.orig-title');
      const orig = origEl ? origEl.textContent.trim() : '';
      const summary = article.querySelector('.summary').textContent.trim();
      const impactEl = article.querySelector('.impact');
      const impactRaw = impactEl ? impactEl.textContent.trim() : '';
      const impact = impactRaw.replace(/^對你的意義\s*/, '');
      const linkEl = article.querySelector('.footer-meta a');
      const link = linkEl ? linkEl.href : '';
      const source = article.querySelectorAll('.footer-meta span')[2]?.textContent.trim() || '';
      const date = article.querySelector('.footer-meta span')?.textContent.trim() || '';

      const text = [
        `*${title}*`,
        orig ? `_${orig}_` : null,
        '',
        summary,
        impact ? `\n💡 對你的意義：${impact}` : null,
        '',
        `📅 ${date}　📰 ${source}`,
        link ? `🔗 ${link}` : null
      ].filter(Boolean).join('\n');

      try {
        await navigator.clipboard.writeText(text);
        btn.classList.add('copied');
        btn.textContent = '✓ 已複製';
        showToast('已複製到剪貼簿');
        setTimeout(() => {
          btn.classList.remove('copied');
          btn.textContent = '📋 複製';
        }, 1800);
      } catch (err) {
        showToast('複製失敗，請手動選取');
      }
    });
  });

  // 必看連結點擊時平滑捲動（+ 短暫 highlight）
  document.querySelectorAll('.must-read-item').forEach(item => {
    item.addEventListener('click', (e) => {
      const href = item.getAttribute('href');
      if (!href || !href.startsWith('#')) return;
      e.preventDefault();
      const target = document.querySelector(href);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target.style.transition = 'box-shadow 0.3s';
        target.style.boxShadow = '0 0 0 2px var(--tag-work)';
        setTimeout(() => target.style.boxShadow = '', 1500);
      }
    });
  });

  // 日期導覽：讀 dates.json，動態產生選擇器與前後跳轉
  const currentDate = document.querySelector('meta[name="brief-date"]')?.content;
  const dateSelect = document.getElementById('date-select');
  const prevBtn = document.getElementById('prev-day');
  const nextBtn = document.getElementById('next-day');

  function weekday(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    return ['週日','週一','週二','週三','週四','週五','週六'][d.getDay()];
  }

  function urlFor(date, isLatest) {
    return isLatest ? './' : date + '.html';
  }

  fetch('dates.json', { cache: 'no-cache' })
    .then(r => r.ok ? r.json() : [])
    .then(dates => {
      if (!Array.isArray(dates) || dates.length === 0) {
        dates = currentDate ? [currentDate] : [];
      }
      dates.sort().reverse(); // 新到舊

      // 填充 select
      dateSelect.innerHTML = '';
      dates.forEach((d, idx) => {
        const opt = document.createElement('option');
        opt.value = d;
        const label = d + '（' + weekday(d) + '）' + (idx === 0 ? ' · 最新' : '');
        opt.textContent = label;
        if (d === currentDate) opt.selected = true;
        dateSelect.appendChild(opt);
      });

      dateSelect.addEventListener('change', () => {
        const target = dateSelect.value;
        const isLatest = target === dates[0];
        window.location.href = urlFor(target, isLatest);
      });

      // 前後按鈕
      const currentIdx = dates.indexOf(currentDate);
      if (currentIdx > 0) {
        // 有後一天（更新）
        const next = dates[currentIdx - 1];
        nextBtn.href = urlFor(next, currentIdx - 1 === 0);
      } else {
        nextBtn.classList.add('disabled');
      }

      if (currentIdx >= 0 && currentIdx < dates.length - 1) {
        // 有前一天（更舊）
        prevBtn.href = urlFor(dates[currentIdx + 1], false);
      } else {
        prevBtn.classList.add('disabled');
      }
    })
    .catch(() => {
      // 無 dates.json 時，保留當前日期為唯一選項
      prevBtn.classList.add('disabled');
      nextBtn.classList.add('disabled');
    });
})();
