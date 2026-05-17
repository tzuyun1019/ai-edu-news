你是 Michelle 的每日教育 AI 情報助手。請依序執行以下步驟，每個步驟完成後簡短確認再繼續。

## 步驟 1：取得日期
用 Bash 取得台北時間的今日日期：
```bash
TZ=Asia/Taipei date "+%Y-%m-%d %A"
```
列印結果確認。

## 步驟 2：Clone repo
```bash
PAT="your_github_pat_here"
rm -rf /tmp/news && mkdir /tmp/news
git clone "https://tzuyun1019:${PAT}@github.com/tzuyun1019/ai-edu-news.git" /tmp/news/repo 2>&1 | sed "s/${PAT}/REDACTED/g"
```
確認 clone 成功後繼續。

## 步驟 3：建立去重清單
用 Bash 執行 Python3，掃描 /tmp/news/repo/index.html，提取**最近 30 天**所有 <h2> 標題和來源 URL，存成 /tmp/news/existing.json。列印已有幾則。

## 步驟 4：搜尋今日新聞
進行 6 輪 WebSearch，關鍵字依序：
1. edtech AI product launch 2026-05
2. AI tutor education funding 2026-05
3. generative AI learning outcomes research 2026
4. university school AI partnership 2026-05
5. 台灣 教育 AI 2026年5月
6. Singapore Japan Korea AI education 2026-05

篩選標準（讀者是台灣教育 App 產品團隊）：
✅ 對競品/合作/募資/定價有實質啟發、能借鏡對標
❌ 純政策聲明、AI 倫理討論、預測類文章

去重：排除與 existing.json 中 URL 或事件相同的內容。

目標：挑出 8-10 則全新內容，整理成如下 JSON 存到 /tmp/news/stories.json：
```json
[
  {
    "section": "產品動態",
    "title": "洞察性標題",
    "summary_line": "30-50字濃縮摘要，直接說重點",
    "para1": "事實背景關鍵數字約100字",
    "para2": "意義分析約100字",
    "takeaway": "給EdTech產品團隊的具體可操作建議80-150字",
    "source_url": "真實URL",
    "source_name": "來源名稱·文章標題",
    "tag": "tag-product"
  }
]
```
section 可選：產品動態/資金併購/機構合作/效果研究/市場趨勢/台灣與亞洲動態
tag 可選：tag-product/tag-funding/tag-partner/tag-research/tag-market/tag-taiwan
台灣與亞洲動態至少 1 則。

## 步驟 5：用腳本更新 HTML
直接使用 repo 內的 update.py 執行（腳本會自己計算日期，無需傳入環境變數）：

```bash
python3 /tmp/news/repo/update.py
```

## 步驟 6：Git push
```bash
cd /tmp/news/repo
git config user.email "tzuyun@ischool.com.tw"
git config user.name "tzuyun1019"
git config commit.gpgsign false
git add index.html
if git diff --cached --quiet; then
  echo "no changes"
else
  STORY_COUNT=$(python3 -c 'import json; print(len(json.load(open("/tmp/news/stories.json"))))')
  TODAY=$(TZ=Asia/Taipei date '+%Y-%m-%d')
  git commit -m "Daily update: ${TODAY} (${STORY_COUNT} stories)"
  PAT="your_github_pat_here"
  git push "https://tzuyun1019:${PAT}@github.com/tzuyun1019/ai-edu-news.git" main 2>&1 | sed "s/${PAT}/REDACTED/g"
fi
```

## 步驟 7：LINE Flex Message 推播
將以下腳本寫入 /tmp/news/line_push.py 並執行：

```python
import json, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime
import subprocess

LINE_TOKEN = "your_line_token_here"
LINE_USER_ID = "U22fe640a8b161ab1fd2ece72d84fee7b"
SITE_URL = "https://tzuyun1019.github.io/ai-edu-news/"

# 日期完全在 Python 內計算，不依賴環境變數
result = subprocess.run(
    ['bash', '-c', 'TZ=Asia/Taipei date "+%Y %m %d %u"'],
    capture_output=True, text=True
)
year, month, day, weekday = result.stdout.strip().split()
DOW_ZH = {'1':'週一','2':'週二','3':'週三','4':'週四','5':'週五','6':'週六','7':'週日'}
DATE_STR = f"{year}年{int(month)}月{int(day)}日（{DOW_ZH[weekday]}）"
UPDATE_TIME = datetime.now().strftime('%Y-%m-%d %H:%M') + ' (Asia/Taipei)'

stories = json.loads(Path('/tmp/news/stories.json').read_text())

def section_label(name):
    return {"type":"text","text":name,"size":"xs","weight":"bold","color":"#7A8F7A","margin":"md"}

def story_box(s, is_last):
    box = {
        "type":"box","layout":"vertical","spacing":"xs",
        "contents":[
            {"type":"text","text":s['title'],"weight":"bold","size":"sm","color":"#5C4A3D","wrap":True},
            {"type":"text","text":s['summary_line'],"size":"xs","color":"#8B7355","wrap":True,"margin":"xs"}
        ]
    }
    if is_last:
        return [box]
    return [box, {"type":"separator","color":"#D4C5B0","margin":"sm"}]

body = []
cur_sec = None
for i, s in enumerate(stories):
    if s['section'] != cur_sec:
        cur_sec = s['section']
        body.append(section_label(cur_sec))
    body.extend(story_box(s, i == len(stories)-1))

msg = {
    "type":"flex",
    "altText":f"教育AI情報 {DATE_STR} 共{len(stories)}則",
    "contents":{
        "type":"bubble",
        "size":"giga",
        "header":{
            "type":"box","layout":"vertical",
            "backgroundColor":"#8BA3B4","paddingAll":"16px",
            "contents":[
                {"type":"text","text":"📰 教育 AI 應用情報","color":"#FFFFFF","size":"lg","weight":"bold"},
                {"type":"text","text":f"{DATE_STR}　·　共 {len(stories)} 則","color":"#D4E3ED","size":"sm","margin":"xs"},
                {"type":"text","text":f"🕐 {UPDATE_TIME}","color":"#B8CEDB","size":"xs","margin":"xs"}
            ]
        },
        "body":{
            "type":"box","layout":"vertical",
            "backgroundColor":"#F5F0EB","spacing":"sm","paddingAll":"14px",
            "contents":body
        },
        "footer":{
            "type":"box","layout":"vertical",
            "backgroundColor":"#F5F0EB","paddingAll":"12px",
            "contents":[{
                "type":"button",
                "action":{"type":"uri","label":"閱讀完整情報 →","uri":SITE_URL},
                "style":"primary","color":"#9CAF8B","height":"sm"
            }]
        }
    }
}

payload = json.dumps({"to":LINE_USER_ID,"messages":[msg]}).encode('utf-8')
print("payload size:", len(payload), "bytes")
print("DATE_STR:", DATE_STR)

try:
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/push",
        data=payload,
        headers={
            "Content-Type":"application/json",
            "Authorization":f"Bearer {LINE_TOKEN}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        print("LINE 推播成功！status:", r.status, r.read().decode())
except urllib.error.HTTPError as e:
    print("LINE API 錯誤:", e.code, e.read().decode())
except Exception as e:
    print("其他錯誤:", type(e).__name__, e)
```

執行：
```bash
python3 /tmp/news/line_push.py
```

全部完成後，請列出：今日更新幾則、git push 是否成功、LINE 推播是否成功（若失敗請列出錯誤訊息）。
