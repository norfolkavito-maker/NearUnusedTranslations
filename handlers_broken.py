# ── Admin Management ─────────────────────────────────────────────────────────────
async def admin_manage_id(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("admin_action", "add")
    
    print(f"DEBUG: admin_manage_id called with action: {action}, data: {data}")
    
    try:
        admin_id = int(msg.text.strip())
        
        if action == "add":
            # Получаем информацию о добавляемом пользователе
            try:
                user_info = await msg.bot.get_chat(admin_id)
                username = user_info.username or ""
                print(f"DEBUG: Adding admin {admin_id} with username {username}")
            except:
                username = ""
                print(f"DEBUG: Could not get user info for {admin_id}")
            
            await add_admin(admin_id, username, msg.from_user.id)
            await state.clear()
            await msg.answer(
                f"✅ Пользователь <code>{admin_id}</code> добавлен в админы!",
                reply_markup=kb_admin_panel
            )
        elif action == "remove":
            # Don't allow removing self
            if admin_id == msg.from_user.id:
                await msg.answer("⚠️ Нельзя удалить самого себя из админов")
                return
            
            await remove_admin(admin_id)
            await state.clear()
            await msg.answer(
                f"✅ Пользователь <code>{admin_id}</code> удален из админов!",
                reply_markup=kb_admin_panel
            )
    except ValueError:
        await msg.answer("⚠️ Введи корректный числовой ID пользователя")
    except Exception as e:
        print(f"ERROR in admin_manage_id: {e}")
        await msg.answer("⚠️ Произошла ошибка при обработке")

async def admin_list(callback: CallbackQuery):
    try:
        # Принудительно создаем таблицу если нет
        from db import init_db
        await init_db()
        
        admins = await get_all_admins()
        if not admins:
            text = "📝 <b>Список администраторов:</b>\n\n➕ Админов пока нет"
        else:
            text = "📝 <b>Список администраторов:</b>\n\n"
            for i, admin in enumerate(admins, 1):
                username = admin['username'] or 'Без username'
                added_at = admin['added_at'][:16] if admin['added_at'] else 'Неизвестно'
                text += f"{i}. @{username} (<code>{admin['tg_id']}</code>)\n   📅 Добавлен: {added_at}\n\n"
        
        try:
            await callback.message.edit_text(text, reply_markup=kb_admin_menu, parse_mode="HTML")
        except Exception as e:
            print(f"Error editing message: {e}")
            # Если редактирование не удалось, отправляем новое сообщение
            await callback.message.answer(text, reply_markup=kb_admin_menu, parse_mode="HTML")
            
    except Exception as e:
        print(f"Error in admin_list: {e}")
        try:
            await callback.message.edit_text("⚠️ Ошибка при загрузке списка админов", reply_markup=kb_admin_menu)
        except:
            await callback.message.answer("⚠️ Ошибка при загрузке списка админов", reply_markup=kb_admin_menu)
    
    await callback.answer()
