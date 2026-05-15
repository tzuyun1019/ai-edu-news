import json, re, os
from pathlib import Path
from datetime import datetime, date, timedelta

TODAY = os.environ['TODAY']
WEEKDAY = int(os.environ['WEEKDAY'])
MON_ISO = os.environ['MON_ISO']
MONTH = os.environ['MONTH']
DAY = os.environ['DAY']

DOW_ZH = {1:'週一',2:'週二',3:'週三',4:'週四',5:'週五',6:'週六',7:'週日'}
dow_zh = DOW_ZH[WEEKDAY]
date_zh = f"{TODAY[:4]} 年 {MONTH} 月 {DAY} 日（{dow_zh}）"

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
html = re.sub(r'<span id="updated">[^<]*</span>', f'<span id="updated">{now_str}</span>', html)

if WEEKDAY == 1:
    mon = date.fromisoformat(MON_ISO)
    sun = mon + timedelta(days=6)
    week_label = f"本週 {mon.year}/{mon.month}/{mon.day} – {sun.month}/{sun.day}"
    html = re.sub(r'id="weekrange"[^>]*>[^<]*<', f'id="weekrange">{week_label}<', html)
    html = re.sub(r'<section class="day-pane" data-day="[^"]*">.*?</section>\s*', '', html, flags=re.DOTALL)
    tabs_html = ''
    for i in range(7):
        d = mon + timedelta(days=i)
        dow_label = DOW_ZH[i+1]
        date_label = f"{d.month}/{d.day}"
        cls = 'tab active' if i == 0 else 'tab empty'
        today_badge = '<span class="tab-today">今日</span>' if i == 0 else ''
        tabs_html += f'<button class="{cls}" data-day="{d.isoformat()}"><span class="tab-dow">{dow_label}</span><span class="tab-date">{date_label}</span>{today_badge}</button>\n'
    html = re.sub(r'(<nav class="day-tabs" id="dayTabs">).*?(</nav>)', f'\\1\n{tabs_html}\\2', html, flags=re.DOTALL)
else:
    def remove_old_panes(h):
        def keep(m):
            day = re.search(r'data-day="([^"]+)"', m.group(0))
            if day and day.group(1) < MON_ISO:
                return ''
            return m.group(0)
        return re.sub(r'<section class="day-pane" data-day="[^"]*">.*?</section>', keep, h, flags=re.DOTALL)
    html = remove_old_panes(html)
    html = re.sub(r'class="tab active"', 'class="tab"', html)
    html = re.sub(r'<span class="tab-today">今日</span>', '', html)
    def activate_today_tab(h):
        h = re.sub(r'(<button )class="tab(?:\s+empty)?"( data-day="' + re.escape(TODAY) + r'")', r'\1class="tab active"\2', h)
        h = re.sub(r'(data-day="' + re.escape(TODAY) + r'"[^>]*>)((?:(?!</button>).)*)(</button>)', lambda m: m.group(1) + m.group(2) + '<span class="tab-today">今日</span>' + m.group(3), h, flags=re.DOTALL)
        return h
    html = activate_today_tab(html)
    html = re.sub(r'<section class="day-pane" data-day=', '<section class="day-pane" hidden data-day=', html)

insert_before = re.search(r'<section class="day-pane"', html)
if insert_before:
    pos = insert_before.start()
    html = html[:pos] + new_pane + '\n' + html[pos:]
else:
    html = re.sub(r'(<section [^>]*id="emptyPane")', new_pane + '\n\\1', html)

Path('/tmp/news/repo/index.html').write_text(html)
print(f'HTML 更新完成：{count} 則，{now_str}')
