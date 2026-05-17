import json, re, subprocess
from pathlib import Path
from datetime import datetime, date, timedelta

# 日期完全由 Python 呼叫 bash 取得，不依賴外部環境變數
r = subprocess.run(['bash', '-c', 'TZ=Asia/Taipei date "+%Y %m %d %u"'], capture_output=True, text=True)
year, month, day, weekday = r.stdout.strip().split()
TODAY = f"{year}-{month}-{day}"
WEEKDAY = int(weekday)
DOW_ZH = {1:'週一',2:'週二',3:'週三',4:'週四',5:'週五',6:'週六',7:'週日'}
dow_zh = DOW_ZH[WEEKDAY]
date_zh = f"{year} 年 {int(month)} 月 {int(day)} 日（{dow_zh}）"

KEEP_DAYS = 30
today_date = date.fromisoformat(TODAY)
cutoff = (today_date - timedelta(days=KEEP_DAYS - 1)).isoformat()

stories = json.loads(Path('/tmp/news/stories.json').read_text())
count = len(stories)
now_str = datetime.now().strftime('%Y-%m-%d %H:%M') + ' (Asia/Taipei)'

story_html_parts = []
current_section = None
for s in stories:
    if s['section'] != current_section:
        current_section = s['section']
        story_html_parts.append(f'  <div class="section-title">{current_section}</div>')
    story_html_parts.append(f'''  <article class="story">
    <span class="tag {s["tag"]}">{s["section"]} · {s["source_name"].split("·")[0].strip()}</span>
    <h2>{s["title"]}</h2>
    <p>{s["para1"]}</p>
    <p>{s["para2"]}</p>
    <div class="takeaway">
      <span class="takeaway-label">給 EdTech 產品團隊的啟示</span>
      <p>{s["takeaway"]}</p>
    </div>
    <div class="source">來源：<a href="{s["source_url"]}" target="_blank" rel="noopener">{s["source_name"]}</a></div>
  </article>''')

new_pane = f'''<section class="day-pane" data-day="{TODAY}">
  <div class="pane-header">
    <strong>{date_zh}</strong>　·　<span class="count">共 {count} 則</span>
  </div>
{chr(10).join(story_html_parts)}
</section>'''

html = Path('/tmp/news/repo/index.html').read_text()

# 更新時間戳
html = re.sub(r'<span id="updated">[^<]*</span>', f'<span id="updated">{now_str}</span>', html)

# 移除 30 天以前的舊 pane
def remove_old_panes(h):
    def keep(m):
        day_match = re.search(r'data-day="([^"]+)"', m.group(0))
        if day_match and day_match.group(1) < cutoff:
            return ''
        return m.group(0)
    return re.sub(r'<section class="day-pane" data-day="[^"]*">.*?</section>', keep, h, flags=re.DOTALL)

html = remove_old_panes(html)

# 重新產生最近 30 天的 tab bar（今日在最左邊）
tabs_html = ''
for i in range(KEEP_DAYS):
    d = today_date - timedelta(days=i)
    dow_label = DOW_ZH[d.isoweekday()]
    date_label = f"{d.month}/{d.day}"
    if i == 0:
        cls = 'tab active'
        today_badge = '<span class="tab-today">今日</span>'
    else:
        cls = 'tab'
        today_badge = ''
    tabs_html += f'<button class="{cls}" data-day="{d.isoformat()}"><span class="tab-dow">{dow_label}</span><span class="tab-date">{date_label}</span>{today_badge}</button>\n'

html = re.sub(r'(<nav class="day-tabs" id="dayTabs">).*?(</nav>)', f'\\1\n{tabs_html}\\2', html, flags=re.DOTALL)

# 更新頁頭的日期範圍說明
html = re.sub(r'id="weekrange"[^>]*>[^<]*<', f'id="weekrange">近 30 天紀錄<', html)

# 所有既有 pane 先隱藏，新的今日 pane 不隱藏
html = re.sub(r'<section class="day-pane" data-day=', '<section class="day-pane" hidden data-day=', html)

# 把今日 pane 插到最前面（不含 hidden）
insert_before = re.search(r'<section class="day-pane"', html)
if insert_before:
    pos = insert_before.start()
    html = html[:pos] + new_pane + '\n' + html[pos:]
else:
    html = re.sub(r'(<section [^>]*id="emptyPane")', new_pane + '\n\\1', html)

Path('/tmp/news/repo/index.html').write_text(html)
print(f'HTML 更新完成：{count} 則，{now_str}')
