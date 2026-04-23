# News Brief — Remote Agent 任務書

每日自動整理台港澳 + 國際重要新聞，為手遊產品企劃 Tim 過濾有價值的訊號。

本檔案由 Anthropic 雲端 Routine agent 讀取並執行。本地手動觸發版本見 `~/.claude/skills/news-brief/SKILL.md`。

---

## 執行流程

### Step 1 · 判斷日期

- CWD 是 news-brief repo 的 clone。執行 `pwd` 與 `ls` 確認環境
- 執行 `date -u '+%Y-%m-%d'` 取 UTC 當日
- **目標日期 = UTC 當日 - 1 天**（前一個自然日，台北時間也是這一天）
- 把這個日期記為 `TARGET_DATE`（格式 `YYYY-MM-DD`）

### Step 2 · WebSearch 分區查詢

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

### Step 3 · 篩選與整理

**篩選判準（由高到低）**：
1. 結構變化 > 單一事件
2. 原始資料 / 官方發佈 > 二手報導
3. 與手遊產品企劃工作相關（Gamesofa、出海日韓、遊戲監管、AI 工具、平台政策）
4. 延展性案例 > 熱度爆點

**避開**：
- 純政治口水、選舉情緒、名嘴評論
- 「AI 將取代 XX」誇大未來式
- 娛樂八卦、犯罪社會、體育（除非產業關聯）
- 紅媒（已在 WebSearch 黑名單）

**數量**：台港澳 ≤ 10 則、國際 ≤ 10 則、**加總上限 20**。訊號稀薄寧少勿濫。

**每則必備欄位**：
- 繁中標題（國際新聞同時附原文標題）
- `data-category` 三選一：`work`（🎯 工作直擊）/ `industry`（📊 產業視野）/ `strategy`（🌏 策略背景）
- 1–2 句純事實摘要
- 「對你的意義」1–2 句（Tim 為什麼該在意）
- 日期、來源媒體名、原文連結

**今日必看 3 則**：從 🎯 類別挑 3 則（若 🎯 不足 3 則用 📊 補），放在網頁頂部置頂區，給 `id="must-1|2|3"`，主列表對應 article 也用同樣 id。

### Step 4 · 生成 HTML（**關鍵：讀現有 index.html 當模板**）

1. `Read` 當前 `index.html`，擷取它的整體結構（CSS、JS、date-nav、filters、must-read 區塊、article 卡片樣式、footer）
2. **保留**：所有 CSS、JS、date-nav 的 DOM 結構（功能會自動運作）
3. **替換**：
   - `<title>` 和 `<meta name="brief-date">` 的日期改為 `TARGET_DATE`
   - `.meta-line` 裡的日期 pill、更新日期、總計數
   - `.must-read` 區塊的 3 張小卡
   - `.filters` 的 chip 計數
   - 左右兩欄的 `<article>` 卡片列表
4. 從 `index.html` 抽出 `meta[name="brief-date"]` 當前值，記為 `OLD_DATE`

### Step 5 · 7 天歷史保留

```bash
# 用 grep 抽出舊日期
OLD_DATE=$(grep -oP 'name="brief-date" content="\K[^"]+' index.html)

# 若舊日期 ≠ 目標日期且 OLD_DATE.html 不存在，先備份
if [ "$OLD_DATE" != "$TARGET_DATE" ] && [ ! -f "$OLD_DATE.html" ]; then
  cp index.html "$OLD_DATE.html"
fi
```

接著：
1. **寫入新 `index.html`**（TARGET_DATE 的完整內容）
2. **同時寫入 `TARGET_DATE.html`**（一模一樣的內容，固定 URL 供分享）
3. **更新 `dates.json`**：
   - Read 當前 `dates.json`
   - 加入 TARGET_DATE（若不存在）
   - 按字串 sort、reverse（新到舊）
   - 取前 7 個
   - Write 回去
4. **刪除超過 7 天的 HTML**：
   - 列出所有 `[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].html` 檔
   - 對每個檔案，若其日期不在 dates.json 的 7 天內，`rm` 掉

### Step 6 · Commit + Push

```bash
git add -A
git status --short  # 確認變更
git commit -m "自動更新：$TARGET_DATE 新聞 brief（台港澳 X 則 / 國際 Y 則）"
git push
```

失敗時回報錯誤訊息，不要 `--force`、不要 `--no-verify`、不要刪 commit 重做。

### Step 7 · 回報

完成後輸出簡短總結：
- 涵蓋日期、各區則數
- 本次最值得看的 2–3 則（粗體點出）
- 公開 URL：https://timdachung.github.io/news-brief/

---

## 關鍵原則

- **HTML 模板必須讀現有 index.html**：不要自己從頭寫，會漏掉 date-nav、filters、JS 等重要結構
- **訊號優先於數量**：某區新聞少寧可留 5 則，不要湊到 10 則
- **翻譯盡量貼原意**：國際新聞同時保留原文標題（給 `.orig-title`）
- **「對你的意義」是精華**：這一段給 Tim 獨特價值，不能省略或敷衍
- **跨日以 UTC 為準**：避免時區混淆（台北 08:30 = UTC 00:30）

## 失敗回退

- WebSearch 失敗：重試 2 次，仍失敗則在該區放「查詢失敗」訊息並繼續其他區
- Git push 失敗：回報錯誤，等下次排程重試
- 若某天新聞訊號真的極少（例如國慶、大選日）：寫入但標註「本日訊號稀薄」
