from __future__ import annotations
import json
from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
import content_cms as cms
from config import is_admin
from psytests import ORDER, REGISTRY
router=Router()
class Admin(BaseFilter):
    async def __call__(self,event): return bool(event.from_user) and is_admin(event.from_user.id)
router.message.filter(Admin()); router.callback_query.filter(Admin())
PER_PAGE=8
class Edit(StatesGroup): value=State()
class Add(StatesGroup): category=State(); difficulty=State(); text_uz=State(); text_ru=State(); options_uz=State(); options_ru=State(); correct=State(); image=State()
def admin_menu():
    b=InlineKeyboardBuilder()
    for text,data in [("📊 Statistika","adm:stats"),("📈 Tugatish darajasi","adm:funnel"),("👥 Foydalanuvchilar","adm:users"),("🧩 Testlarni boshqarish","adm:tests"),("📝 Savollar CMS","cms:home"),("📥 Natijalarni yuklab olish","adm:export"),("📣 Xabar yuborish","adm:broadcast"),("💳 To‘lovlar","adm:pay"),("💰 Wallet / manual to‘lovlar","adm:wallet"),("👤 User / wallet boshqaruvi","admuser:home"),("🧠 IQ / premium sozlamalari","admiq:home")]: b.button(text=text,callback_data=data)
    b.adjust(2,2,1,1,1,1,1,1,1); return b.as_markup()
def admin_text(): return "🛠 <b>Admin panel</b>\n\n<b>Admin buyruqlari:</b>\n/admin — admin panel\n/cms — savollar CMS\n/walletadjust — balansni o‘zgartirish\n/adjustwallet — walletadjust alias\n/user USER_ID — foydalanuvchi boshqaruvi\n/iqprice — IQ narxini ko‘rish\n\n<b>Foydalanuvchi buyruqlari:</b> /start /natijalar /balans /shop /iq /til /haqida /yordam /bekor"
def tests_menu():
    b=InlineKeyboardBuilder()
    # IQ testi rasmli: savollari kodda (psytests/iq.py), CMS orqali tahrirlanmaydi.
    for key in ORDER:
        b.button(text=f"{REGISTRY[key].emoji} {REGISTRY[key].title['uz']}",callback_data=f"cms:list:{key}:0")
    b.button(text="⬅️ Admin panel",callback_data="adm:home"); b.adjust(1); return b.as_markup()
def list_menu(key,page,rows):
    b=InlineKeyboardBuilder(); chunk=rows[page*PER_PAGE:(page+1)*PER_PAGE]
    for q in chunk: b.button(text=f"{'🟢' if q['enabled'] else '🔴'} #{q['id']} · {q['text_uz'][:42]}",callback_data=f"cms:q:{q['id']}")
    if page>0:b.button(text="⬅️",callback_data=f"cms:list:{key}:{page-1}")
    if (page+1)*PER_PAGE<len(rows):b.button(text="➡️",callback_data=f"cms:list:{key}:{page+1}")
    b.button(text="➕ Yangi savol",callback_data=f"cms:add:{key}"); b.button(text="⬅️ Testlar",callback_data="cms:home"); b.adjust(1,2,1,1); return b.as_markup()
@router.message(Command("admin"))
async def admin(message:Message,state:FSMContext): await state.clear(); await message.answer(admin_text(),reply_markup=admin_menu())
@router.callback_query(F.data=="adm:home")
async def home(c:CallbackQuery,state:FSMContext): await state.clear(); await c.answer(); await c.message.edit_text(admin_text(),reply_markup=admin_menu())
@router.message(Command("cms"))
async def cms_cmd(message:Message): await cms.init(); await message.answer("📝 <b>Savollar CMS</b>\n\nTestni tanlang:",reply_markup=tests_menu())
@router.callback_query(F.data=="cms:home")
async def cms_home(c:CallbackQuery): await c.answer(); await c.message.edit_text("📝 <b>Savollar CMS</b>\n\nTestni tanlang:",reply_markup=tests_menu())
@router.callback_query(F.data.startswith("cms:list:"))
async def cms_list(c:CallbackQuery):
    _,_,key,p=c.data.split(":"); p=int(p); rows=await cms.rows(key); pages=max(1,(len(rows)+PER_PAGE-1)//PER_PAGE); p=min(p,pages-1); title=REGISTRY[key].title['uz'] if key in REGISTRY else 'Premium IQ testi'; await c.answer(); await c.message.edit_text(f"📝 <b>{title}</b>\nSavollar: <b>{len(rows)}</b> · sahifa {p+1}/{pages}\n\n🟢 faol · 🔴 o‘chirilgan",reply_markup=list_menu(key,p,rows))
@router.callback_query(F.data.startswith("cms:q:"))
async def question(c:CallbackQuery):
    q=await cms.get(int(c.data.rsplit(":",1)[1])); await c.answer()
    if not q:return
    uz=json.loads(q['options_uz']) if q['options_uz'] else []; ru=json.loads(q['options_ru']) if q['options_ru'] else []
    text=(f"📝 <b>#{q['id']}</b> · {q['test_key']}\nHolat: {'🟢 faol' if q['enabled'] else '🔴 o‘chirilgan'}\nKategoriya: <b>{q['category']}</b> · qiyinlik: <b>{q['difficulty']}</b>\n\n🇺🇿 {q['text_uz']}\n🇷🇺 {q['text_ru']}\n\n🇺🇿 {uz}\n🇷🇺 {ru}\n🎯 To‘g‘ri javob: <b>{q['correct_index'] if q['correct_index'] is not None else '—'}</b>\n🖼 {q['image_url'] or '—'}")
    b=InlineKeyboardBuilder()
    for label,field in [("✏️ UZ savol","text_uz"),("✏️ RU savol","text_ru"),("🔢 UZ variantlar","options_uz"),("🔢 RU variantlar","options_ru"),("🎯 To‘g‘ri javob","correct_index"),("🏷 Kategoriya","category"),("📈 Qiyinlik","difficulty"),("🖼 Rasm URL","image_url")]: b.button(text=label,callback_data=f"cms:edit:{q['id']}:{field}")
    b.button(text="🔄 Faollik",callback_data=f"cms:toggle:{q['id']}"); b.button(text="🗑 O‘chirish",callback_data=f"cms:delete:{q['id']}"); b.button(text="⬅️ Ro‘yxat",callback_data=f"cms:list:{q['test_key']}:0"); b.adjust(2,2,2,2,2,1,1); await c.message.edit_text(text,reply_markup=b.as_markup())
@router.callback_query(F.data.startswith("cms:toggle:"))
async def toggle(c:CallbackQuery):
    q=await cms.get(int(c.data.rsplit(":",1)[1]));
    if q: await cms.update(q['id'],enabled=0 if q['enabled'] else 1); await cms.apply_all(); c.data=f"cms:q:{q['id']}"; await question(c)
@router.callback_query(F.data.startswith("cms:delete:"))
async def delete(c:CallbackQuery):
    q=await cms.get(int(c.data.rsplit(":",1)[1])); ok=await cms.delete(q['id']) if q else False
    if ok: await cms.apply_all()
    await c.answer("🗑 O‘chirildi" if ok else "Topilmadi"); await c.message.edit_text("📝 <b>Savol o‘chirildi.</b>\n\nTestni tanlang:",reply_markup=tests_menu())
@router.callback_query(F.data.startswith("cms:edit:"))
async def edit_start(c:CallbackQuery,state:FSMContext):
    _,_,qid,field=c.data.split(":"); await state.update_data(question_id=int(qid),field=field); await state.set_state(Edit.value); await c.answer(); await c.message.edit_text({"text_uz":"🇺🇿 Yangi savol matni:","text_ru":"🇷🇺 Новый текст вопроса:","options_uz":"🇺🇿 5 variantni | bilan ajrating:","options_ru":"🇷🇺 5 вариантов через |:","correct_index":"🎯 To‘g‘ri javob indeksi 0–4:","category":"🏷 Kategoriya kodi:","difficulty":"📈 Qiyinlik 1–5:","image_url":"🖼 Rasm URL (o‘chirish uchun -):"}[field]+"\n\nBekor: /bekor")
@router.message(Edit.value,Command("bekor"))
async def edit_cancel(m:Message,state:FSMContext): await state.clear(); await m.answer("❌ Bekor qilindi.",reply_markup=tests_menu())
@router.message(Edit.value)
async def edit_value(m:Message,state:FSMContext):
    d=await state.get_data(); f=d['field']; raw=(m.text or '').strip()
    if f in ('correct_index','difficulty'):
        if not raw.isdigit(): return await m.answer('❌ Faqat raqam yuboring.')
        v=int(raw); ok=(0<=v<=4) if f=='correct_index' else (1<=v<=5)
        if not ok:return await m.answer('❌ Noto‘g‘ri oraliq.')
    elif f.startswith('options_'):
        v=[x.strip() for x in raw.split('|') if x.strip()]
        if len(v)!=5:return await m.answer('❌ Aynan 5 ta variant kerak.')
    else:v=None if f=='image_url' and raw=='-' else raw
    await cms.update(d['question_id'],**{f:v}); await cms.apply_all(); await state.clear(); await m.answer('✅ Saqlandi va testga qo‘llandi.',reply_markup=tests_menu())
@router.callback_query(F.data.startswith("cms:add:"))
async def add_start(c:CallbackQuery,state:FSMContext): await state.clear(); await state.update_data(test_key=c.data.rsplit(':',1)[1]); await state.set_state(Add.category); await c.answer(); await c.message.edit_text('➕ <b>Yangi savol</b>\n\nKategoriya/scale kodini yuboring.\nBig Five: E/A/C/S/O · RIASEC: R/I/A/S/E/C')
@router.message(Add.category)
async def add_cat(m:Message,state:FSMContext): await state.update_data(category=(m.text or '').strip()); await state.set_state(Add.difficulty); await m.answer('Qiyinlik 1–5:')
@router.message(Add.difficulty)
async def add_diff(m:Message,state:FSMContext):
    raw=(m.text or '').strip()
    if not raw.isdigit() or not 1<=int(raw)<=5:return await m.answer('❌ 1–5 yuboring.')
    await state.update_data(difficulty=int(raw)); await state.set_state(Add.text_uz); await m.answer('🇺🇿 Savol matni:')
@router.message(Add.text_uz)
async def add_uz(m:Message,state:FSMContext): await state.update_data(text_uz=(m.text or '').strip()); await state.set_state(Add.text_ru); await m.answer('🇷🇺 Текст вопроса:')
@router.message(Add.text_ru)
async def add_ru(m:Message,state:FSMContext): await state.update_data(text_ru=(m.text or '').strip()); await state.set_state(Add.options_uz); await m.answer('🇺🇿 5 variantni | bilan ajrating:')
@router.message(Add.options_uz)
async def add_ou(m:Message,state:FSMContext):
    v=[x.strip() for x in (m.text or '').split('|') if x.strip()]
    if len(v)!=5:return await m.answer('❌ Aynan 5 ta variant kerak.')
    await state.update_data(options_uz=v); await state.set_state(Add.options_ru); await m.answer('🇷🇺 5 вариантов через |:')
@router.message(Add.options_ru)
async def add_or(m:Message,state:FSMContext):
    v=[x.strip() for x in (m.text or '').split('|') if x.strip()]
    if len(v)!=5:return await m.answer('❌ Нужно ровно 5 вариантов.')
    await state.update_data(options_ru=v); await state.set_state(Add.correct); await m.answer('🎯 To‘g‘ri javob indeksi 0–4:')
@router.message(Add.correct)
async def add_correct(m:Message,state:FSMContext):
    raw=(m.text or '').strip()
    if not raw.isdigit() or int(raw) not in range(5):return await m.answer('❌ 0–4 yuboring.')
    await state.update_data(correct_index=int(raw)); await state.set_state(Add.image); await m.answer('🖼 Rasm URL yoki -:')
@router.message(Add.image)
async def add_image(m:Message,state:FSMContext):
    d=await state.get_data(); d['image_url']=None if (m.text or '').strip()=='-' else (m.text or '').strip(); await cms.create(d); await state.clear(); await cms.apply_all(); await m.answer('✅ Yangi savol qo‘shildi va testga qo‘llandi.',reply_markup=tests_menu())
