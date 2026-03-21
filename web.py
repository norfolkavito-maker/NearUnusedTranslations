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
  .subtitle {{ color: #888; margin-bottom: 24px; font-size: 14px; }}
  .count {{ display: inline-block; background: #1e90ff; color: #fff; border-radius: 20px; padding: 4px 14px; font-size: 14px; margin-bottom: 20px; }}
  table {{ width: 100%; border-collapse: collapse; background: #1a1a1a; border-radius: 10px; overflow: hidden; }}
  th {{ background: #1e90ff; color: white; padding: 12px 16px; text-align: left; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}
  td {{ padding: 11px 16px; border-bottom: 1px solid #2a2a2a; font-size: 14px; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #222; }}
  .num {{ color: #555; }}
  .empty {{ text-align: center; padding: 40px; color: #555; }}
  .refresh {{ float: right; background: #333; color: #aaa; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; text-decoration: none; }}
  .refresh:hover {{ background: #444; color: #fff; }}
</style>
</head>
<body>
<h1>Участники турнира <a href="/" class="refresh">Обновить</a></h1>
<p class="subtitle">Список зарегистрированных игроков</p>
<div class="count">{count} / {max_players} игроков</div>
<table>
  <thead>
    <tr>
      <th>#</th>
      <th>Telegram ID</th>
      <th>Epic ID</th>
      <th>Discord</th>
      <th>Ранг</th>
      <th>Пик ранг</th>
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
  <td>{tg_id}</td>
  <td>{epic}</td>
  <td>{discord}</td>
  <td>{rank}</td>
  <td>{peak_rank}</td>
</tr>"""

EMPTY_ROW = '<tr><td colspan="6" class="empty">Никто ещё не зарегистрировался</td></tr>'


async def index(request):
    from config import MAX_PLAYERS
    users = await get_all_users()

    if users:
        rows = "\n".join(
            ROW_TEMPLATE.format(num=i, **u)
            for i, u in enumerate(users, 1)
        )
    else:
        rows = EMPTY_ROW

    html = HTML_TEMPLATE.format(count=len(users), max_players=MAX_PLAYERS, rows=rows)
    return web.Response(text=html, content_type="text/html")


async def start_web():
    app = web.Application()
    app.router.add_get("/", index)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 5000)
    await site.start()
    print("Веб-панель запущена на порту 5000")
