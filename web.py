import asyncio
from aiohttp import web
from openpyxl import Workbook
from db_turso import get_all_users
from datetime import datetime
import io


async def index(request):
    users = await get_all_users()
    if not users:
        return web.Response(text="Никто ещё не зарегистрировался.", content_type="text/html")
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Участники турнира</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f2f2f2; }
            .rank { font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>📋 Список участников турнира</h1>
        <table>
            <tr>
                <th>№</th>
                <th>Username</th>
                <th>Epic Nickname</th>
                <th>Discord</th>
                <th>Rank</th>
                <th>Peak Rank</th>
                <th>Tracker</th>
            </tr>
    """
    
    for i, u in enumerate(users, 1):
        html += f"""
            <tr>
                <td>{i}</td>
                <td>{u.get('username', '—')}</td>
                <td>{u['epic']}</td>
                <td>{u['discord']}</td>
                <td class="rank">{u['rank']}</td>
                <td class="rank">{u['peak_rank']}</td>
                <td>{u.get('tracker', '—')}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")


async def export_excel(request):
    users = await get_all_users()
    wb = Workbook()
    ws = wb.active
    ws.title = "Участники"
    
    headers = ["ID", "Username", "Epic", "Discord", "Rank", "Peak Rank", "Tracker"]
    ws.append_row(headers)
    
    for i, u in enumerate(users, 1):
        ws.append_row([
            i,
            u.get('username', ''),
            u['epic'],
            u['discord'],
            u['rank'],
            u['peak_rank'],
            u.get('tracker', '')
        ])
    
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return web.Response(
        body=buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=participants.xlsx"}
    )


async def handle_health(request):
    """Health check endpoint"""
    return web.Response(text="OK", status=200)


async def handle_participants(request):
    return await index(request)


async def handle_export(request):
    return await export_excel(request)


async def start_web():
    app = web.Application()
    app.router.add_route('GET', '/participants', handle_participants)
    app.router.add_route('GET', '/export', handle_export)
    app.router.add_route('GET', '/health', handle_health)
    
    runner = web.AppRunner(app)
    
    print("🌐 Веб-панель запущена на порту 5000")
    
    try:
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        await site.start()
    except Exception as e:
        print(f"Ошибка запуска веб-сервера: {e}")
    finally:
        # Cleanup
        try:
            await runner.cleanup()
        except:
            pass
