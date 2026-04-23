# News Brief — Remote Agent 任務書

每日自動整理台港澳 + 國際重要新聞，為手遊產品企劃 Tim 過濾有價值的訊號。

---

## ⚠️ 架構說明（最重要）

**Agent 不直接寫 HTML**。HTML 生成由 `generate.py` 負責。

你的唯一工作：
1. **查新聞** (WebSearch)
2. **寫 news.json**（結構化資料）
3. **跑 `python generate.py`**（生成器自動處理 HTML、備份、清理 7 天以上的舊檔）
4. **git push**

這個架構是為了避開 Claude Write 工具的 stream idle timeout（寫大量 HTML token 會卡）。**嚴格不要自己寫 HTML**。

---

## 執行流程

### Step 1 · 環境確認

```bash
pwd                        # 應該在 news-brief repo 根
ls -la                     # 確認 template.html, generate.py, style.css, app.js 都在
date -u '+%Y-%m-%d'        # UTC 當日
```

**TARGET_DATE** = UTC 當日 - 1 天（格式 `YYYY-MM-DD`）。台北時間也是這一天。

### Step 2 · WebSearch 查新聞

**台港澳**（至少 4 個查詢）：
- 台灣科技、遊戲產業、金管會、數位發展部 + `TARGET_DATE`
- 香港法規、金融、SFC、科技政策 + `TARGET_DATE`
- 中國遊戲版號 / 抽卡 / 未成年法規（影響台廠）+ `TARGET_DATE`
- 台灣半導體、AI 產業動態 + `TARGET_DATE`

**國際**（至少 5 個查詢）：
- 中美地緣、出口管制、關稅 + `TARGET_DATE`
- Apple / Google 平台政策、抽成 + `TARGET_DATE`
- AI 模型、OpenAI / Anthropic / Google 動態 + `TARGET_DATE`
- 遊戲產業（米哈遊、任天堂、索尼、網易、騰訊、Bandai Namco）+ `TARGET_DATE`
- 日韓手遊市場、NCSOFT、Netmarble + `TARGET_DATE`

查詢時用 `blocked_domains` 排除紅媒：
```
["globaltimes.cn", "chinadaily.com.cn", "xinhuanet.com", "people.cn", "cctv.com", "cgtn.com", "wenweipo.com", "takungpao.com", "rt.com", "sputniknews.com", "tass.com"]
```

### Step 3 · 篩選

**篩選判準**（由高到低）：
1. 結構變化 > 單一事件
2. 原始資料 > 二手報導
3. 與手遊產品企劃工作相關（遊戲產業、Apple/Google 政策、AI 工具、日韓市場、中國監管）
4. 延展性案例 > 熱度爆點

**避開**：政治口水、選舉情緒、娛樂八卦、「AI 將取代 XX」誇大、名嘴評論

**數量上限**：台港澳 ≤ 10 則、國際 ≤ 10 則，**加總 ≤ 20**。寧少勿濫。

### Step 4 · 寫 news.json

用 `Write` 工具寫入 `news.json`（位於 repo 根）。結構如下：

```json
{
  "date": "2026-04-22",
  "weekday": "週三",
  "must_read": [
    { "title": "短版標題", "hint": "一句話點出重要性", "article_id": "must-1" },
    { "title": "...", "hint": "...", "article_id": "must-2" },
    { "title": "...", "hint": "...", "article_id": "must-3" }
  ],
  "tw": [
    {
      "id": "must-1",               // 若是必看之一才有，否則省略
      "category": "work",           // work | industry | strategy
      "title": "繁中標題",
      "orig_title": "原文英文標題", // 國際新聞才有，台港澳可省略
      "summary": "1-2 句純事實摘要",
      "impact": "對你的意義：1-2 句 Tim 為什麼該在意",
      "date": "2026-04-22",
      "source": "來源媒體名",
      "link": "https://...",
      "link_text": "原文連結"        // 可省，預設就是「原文連結」
    }
  ],
  "intl": [ /* 同結構 */ ]
}
```

**必讀**：
- `must_read` 挑 3 則（優先 🎯 work，不足再用 📊 industry 補）。`article_id` 必須對應到 `tw` 或 `intl` 裡某則的 `id`
- 每則 `category` 必須是 `work` / `industry` / `strategy` 其中之一
- **「對你的意義」是精華**，不能省略或敷衍——這一段給 Tim 獨特價值
- 日期格式 `YYYY-MM-DD`（若不確定可填「近期」）
- `link` 必填，`orig_title` 國際新聞必填

### Step 5 · 跑生成器

```bash
python generate.py
```

應該看到類似輸出：
```
[generate] Date: 2026-04-22 (週三)
[generate] TW: 6 articles | INTL: 9 articles
[generate] Categories: work=4, industry=7, strategy=4
[generate] Must-read: 3 items
[generate] Active dates: [...]
[generate] Done.
```

**如果 generate.py 報錯**：回報完整錯誤訊息，**不要**自己改 `generate.py`、**不要**自己寫 HTML 當作備援。這代表 news.json 有問題，修正它再重跑。

生成器會自動處理：
- 寫入 `index.html` 和 `{date}.html`
- 備份舊 index（若日期不同）
- 更新 `dates.json`
- 刪除超過 7 天的舊 HTML 快照

### Step 6 · Commit + Push

```bash
git add -A
git status --short                   # 確認變更
git commit -m "自動更新：<TARGET_DATE> 新聞 brief（台港澳 X 則 / 國際 Y 則）"
git push
```

**如果 `git status` 顯示 nothing to commit**：代表內容跟昨天一模一樣（極罕見）。回報「今日訊號與昨日相同、跳過 commit」。

**如果 `git push` 失敗**：回報完整錯誤訊息，**不要**用 `--force`、**不要** `--no-verify`、**不要**刪 commit 重做。

### Step 7 · 回報

輸出：
- 涵蓋日期、各區則數
- 本次最值得看的 2–3 則（粗體）
- 公開 URL：https://timdachung.github.io/news-brief/

---

## 關鍵原則

- **絕對不要自己寫 HTML**：所有 HTML 生成由 `generate.py` 包辦
- **絕對不要改 `generate.py` / `template.html` / `style.css` / `app.js`**：這些是固定的基礎設施，你只負責餵 news.json
- **訊號優先於數量**：某區新聞少寧可留 5 則，不要湊到 10 則
- **翻譯貼原意**：國際新聞同時填 `orig_title`
- **「對你的意義」是精華**：每則都要，不能敷衍
- **跨日以 UTC 為準**：台北 08:30 = UTC 00:30，今天 UTC 日期 -1 天 = 目標日期

---

## 失敗回退

- WebSearch 失敗：重試 2 次，仍失敗則該區少放幾則並繼續
- `python generate.py` 報錯：修正 news.json 格式再重跑，不要手動寫 HTML
- `git push` 失敗：回報錯誤，等下次排程重試
- 若某天訊號極少：照常寫入 news.json，`impact` 註明「本日訊號稀薄」
