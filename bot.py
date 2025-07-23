import json
import asyncio
import random
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN = "8016454304:AAGseFUZMxvdp1HzeLiakKNyMy3Envgk0J4"  # 여기에 실제 봇 토큰 넣으세요

users_file = "users.json"
bets_file = "bets.json"
results_file = "results.json"

def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(user_id):
    users = load_json(users_file)
    if str(user_id) not in users:
        users[str(user_id)] = {"balance": 100000}
        save_json(users_file, users)
    return users[str(user_id)]

async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    await update.message.reply_text(f"💰 현재 잔액: {user['balance']:,}원")

async def baccarat_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = load_json(results_file)
    history = results.get("history", [])[-15:]
    await update.message.reply_text("🎲 최근 결과:\n" + "\n".join(history) if history else "아직 결과 없음")

async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text.strip()
    user = get_user(user_id)
    commands = ["/뱅", "/플", "/타이", "/플페어", "/플뱅커"]
    for cmd in commands:
        if msg.startswith(cmd):
            try:
                amount = int(msg.split()[1])
                if user["balance"] < amount:
                    await update.message.reply_text("❗ 잔액 부족")
                    return
                user["balance"] -= amount
                users = load_json(users_file)
                users[user_id] = user
                save_json(users_file, users)

                bets = load_json(bets_file)
                bets.setdefault(user_id, []).append({"type": cmd, "amount": amount})
                save_json(bets_file, bets)

                await update.message.reply_text(f"✅ {cmd}에 {amount:,}원 배팅 완료")
            except:
                await update.message.reply_text("형식: /뱅 10000")
            return

def draw_card():
    return random.randint(1, 10)

def calculate_total(cards):
    return sum(cards) % 10

async def game_loop():
    while True:
        await asyncio.sleep(25)
        bets = load_json(bets_file)
        if not bets:
            continue

        results = load_json(results_file)
        users = load_json(users_file)

        # 카드 분배
        player_cards = [draw_card()]
        banker_cards = [draw_card()]
        await broadcast(f"🃏 플레이어 첫 카드: {player_cards[0]}")
        await broadcast(f"🃏 뱅커 첫 카드: {banker_cards[0]}")

        await asyncio.sleep(3)
        player_cards.append(draw_card())
        await broadcast(f"🃏 플레이어 두번째 카드: {player_cards[1]}")
        await asyncio.sleep(3)
        banker_cards.append(draw_card())
        await broadcast(f"🃏 뱅커 두번째 카드: {banker_cards[1]}")

        player_total = calculate_total(player_cards)
        banker_total = calculate_total(banker_cards)

        await asyncio.sleep(3)
        # 플레이어 추가 카드
        if player_total <= 5:
            third = draw_card()
            player_cards.append(third)
            await broadcast(f"🃏 플레이어 추가 카드: {third}")
            player_total = calculate_total(player_cards)

        banker_total = calculate_total(banker_cards)

        await asyncio.sleep(3)
        outcome = ""
        if player_total > banker_total:
            outcome = "플"
        elif banker_total > player_total:
            outcome = "뱅"
        else:
            outcome = "타이"

        results.setdefault("history", []).append(f"플:{player_total} vs 뱅:{banker_total} → {outcome}")
        results["history"] = results["history"][-50:]
        save_json(results_file, results)

        # 결과 정산
        for user_id, user_bets in bets.items():
            user = users.get(user_id, {"balance": 100000})
            for bet in user_bets:
                if bet["type"] == f"/{outcome}":
                    user["balance"] += bet["amount"] * 2
            users[user_id] = user

        save_json(users_file, users)
        save_json(bets_file, {})

        await broadcast(f"🎲 이번 결과: {outcome} (플:{player_total} / 뱅:{banker_total})")

async def broadcast(message):
    users = load_json(users_file)
    for uid in users:
        try:
            await app.bot.send_message(chat_id=int(uid), text=message)
        except:
            pass

async def main():
    global app
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.Regex(r"^/내정보$"), my_info))
    app.add_handler(MessageHandler(filters.Regex(r"^/바카라$"), baccarat_history))
    app.add_handler(MessageHandler(filters.Regex(r"^/(뱅|플|타이|플페어|플뱅커) \d+$"), handle_bet))

    asyncio.create_task(game_loop())
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
