import asyncio
import random
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)

user_balances = {}
bets = {}
GROUP_CHAT_ID = -1002799021115  # 실제 그룹 ID로 바꿔주세요
cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10']

# /내정보 명령 처리
async def 내정보(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = user_balances.get(user_id, 100000)
    await update.message.reply_text(f'💰 현재 잔액: {balance}원')

# /바카라 명령 처리
async def 바카라(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "history" not in context.bot_data:
        await update.message.reply_text("📭 아직 게임 기록이 없습니다.")
    else:
        history = context.bot_data["history"][-15:]
        text = "\n".join(history)
        await update.message.reply_text(f"🎲 최근 게임 결과:\n{text}")

# 배팅 공통 처리
async def bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name
    command = update.message.text.split()[0].replace("/", "")
    args = context.args

    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text("⚠️ 사용법: /명령어 금액 (예: /뱅 10000)")
        return

    amount = int(args[0])
    balance = user_balances.get(user_id, 100000)

    if amount > balance:
        await update.message.reply_text("❌ 잔액이 부족합니다.")
        return

    user_balances[user_id] = balance - amount
    bets[user_id] = {"type": command, "amount": amount, "name": user_name}

    await update.message.reply_text(f"✅ {command.upper()}에 {amount}원 배팅 완료!")

    if not context.bot_data.get("game_running"):
        context.bot_data["game_running"] = True
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"🎰 누군가 배팅을 했습니다. 25초 후 게임이 시작됩니다.\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await asyncio.sleep(25)
        await run_game(context)

# 게임 실행
async def run_game(context: ContextTypes.DEFAULT_TYPE):
    player_cards = [random.choice(cards), random.choice(cards)]
    banker_cards = [random.choice(cards), random.choice(cards)]

    player_sum = sum(min(int(card), 10) if card != 'A' else 1 for card in player_cards) % 10
    banker_sum = sum(min(int(card), 10) if card != 'A' else 1 for card in banker_cards) % 10

    if player_sum <= 5:
        player_cards.append(random.choice(cards))
        player_sum = sum(min(int(card), 10) if card != 'A' else 1 for card in player_cards) % 10

    if banker_sum <= 5:
        banker_cards.append(random.choice(cards))
        banker_sum = sum(min(int(card), 10) if card != 'A' else 1 for card in banker_cards) % 10

    result = ""
    if player_sum > banker_sum:
        result = "플레이어"
    elif banker_sum > player_sum:
        result = "뱅커"
    else:
        result = "타이"

    msg = f"🃏 카드 결과\n"
    msg += f"플레이어: {player_cards} ({player_sum})\n"
    msg += f"뱅커: {banker_cards} ({banker_sum})\n"
    msg += f"🎯 결과: {result} 승리"

    winners = []
    for user_id, bet in bets.items():
        bet_type = bet["type"]
        amount = bet["amount"]
        name = bet["name"]

        if (bet_type == "플" and result == "플레이어") or \
           (bet_type == "뱅" and result == "뱅커") or \
           (bet_type == "타이" and result == "타이"):
            user_balances[user_id] += amount * 2
            winners.append(f"{name}님 ({bet_type}) +{amount}원 적중")

    if not winners:
        msg += "\n❌ 이번 게임에서는 적중자가 없습니다."
    else:
        msg += "\n💸 적중자:\n" + "\n".join(winners)

    context.bot_data.setdefault("history", []).append(result)
    context.bot_data["game_running"] = False
    bets.clear()

    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)

# 한글 명령어는 필터로 처리
def 명령필터(명령):
    return MessageHandler(filters.TEXT & filters.Regex(f"^/{명령}$"), globals()[명령])

# 봇 실행
async def main():
    app = ApplicationBuilder().token("8016454304:AAGseFUZMxvdp1HzeLiakKNyMy3Envgk0J4").build()

    app.add_handler(명령필터("내정보"))
    app.add_handler(명령필터("바카라"))
    app.add_handler(CommandHandler("뱅", bet_handler))
    app.add_handler(CommandHandler("플", bet_handler))
    app.add_handler(CommandHandler("타이", bet_handler))
    app.add_handler(CommandHandler("뱅페어", bet_handler))

    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
