import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from aiohttp import web
from db import get_all_users

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Участники турнира</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; background: #0f0f0f; color: #eee; padding: 30px; }}
  h1 {{ color: #fff; margin-bottom: 6px; }}
  .subtitle {{ color: #888; margin-bottom: 20px; font-size: 14px; }}
  .toolbar {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .count {{ background: #1e90ff; color: #fff; border-radius: 20px; padding: 5px 16px; font-size: 14px; }}
  .btn {{ display: inline-block; padding: 7px 18px; border-radius: 7px; font-size: 14px; text-decoration: none; cursor: pointer; border: none; }}
  .btn-refresh {{ background: #2a2a2a; color: #aaa; }}
  .btn-refresh:hover {{ background: #333; color: #fff; }}
  .btn-excel {{ background: #1d6f42; color: #fff; }}
  .btn-excel:hover {{ background: #22834e; }}
  table {{ width: 100%; border-collapse: collapse; background: #1a1a1a; border-radius: 10px; overflow: hidden; }}
  th {{ background: #1e90ff; color: white; padding: 12px 16px; text-align: left; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}
  td {{ padding: 11px 16px; border-bottom: 1px solid #2a2a2a; font-size: 14px; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #222; }}
  .num {{ color: #555; width: 40px; }}
  .empty {{ text-align: center; padding: 40px; color: #555; }}
  a.tracker-link {{ color: #1e90ff; text-decoration: none; }}
  a.tracker-link:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>Участники турнира</h1>
<p class="subtitle">Список зарегистрированных игроков</p>
<div class="toolbar">
  <span class="count">{count} игроков</span>
  <a href="/" class="btn btn-refresh">🔄 Обновить</a>
  <a href="/export" class="btn btn-excel">📥 Скачать Excel</a>
</div>
<table>
  <thead>
    <tr>
      <th>#</th>
      <th>Telegram</th>
      <th>TG ID</th>
      <th>Epic ID</th>
      <th>Discord</th>
      <th>Актуальный MMR</th>
      <th>Пиковый MMR</th>
      <th>RL Tracker</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>
</body>
</html>"""

ROW_TEMPLATE = """<tr>
  <td class="num">{num}</td>
  <td>{username}</td>
  <td>{tg_id}</td>
  <td>{epic}</td>
  <td>{discord}</td>
  <td>{rank}</td>
  <td>{peak_rank}</td>
  <td>{tracker_cell}</td>
</tr>"""

EMPTY_ROW = '<tr><td colspan="8" class="empty">Никто ещё не зарегистрировался</td></tr>'


async def index(request):
    users = await get_all_users()

    def make_row(i, u):
        tracker = u.get("tracker") or ""
        tracker_cell = f'<a class="tracker-link" href="{tracker}" target="_blank">открыть</a>' if tracker else "—"
        return ROW_TEMPLATE.format(num=i, tracker_cell=tracker_cell, **{k: v for k, v in u.items() if k != "tracker"})

    rows = "\n".join(make_row(i, u) for i, u in enumerate(users, 1)) if users else EMPTY_ROW
    html = HTML_TEMPLATE.format(count=len(users), rows=rows)
    return web.Response(text=html, content_type="text/html")


async def export_excel(request):
    users = await get_all_users()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Участники"

    headers = ["#", "Telegram", "TG ID", "Epic ID", "Discord", "Актуальный MMR", "Пиковый MMR", "RL Tracker"]
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1E90FF")
    header_align = Alignment(horizontal="center", vertical="center")

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    col_widths = [5, 18, 15, 20, 20, 20, 20, 50]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    alt_fill = PatternFill("solid", fgColor="1A1A2E")
    for row_idx, u in enumerate(users, 2):
        row_data = [
            row_idx - 1,
            u.get("username", ""),
            u["tg_id"],
            u["epic"],
            u["discord"],
            u["rank"],
            u["peak_rank"],
            u.get("tracker", ""),
        ]
        fill = alt_fill if row_idx % 2 == 0 else None
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            if fill:
                cell.fill = fill

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return web.Response(
        body=buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=participants.xlsx"}
    )


async def start_web():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/export", export_excel)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 5000)
    await site.start()
    print("Веб-панель запущена на порту 5000")
