import asyncio
import random
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

TOKEN = "8016454304:AAGseFUZMxvdp1HzeLiakKNyMy3Envgk0J4"  # 실제 봇 토큰으로 교체
GROUP_CHAT_ID = -1002799021115  # 실제 그룹 ID로 교체

user_balances = {}
current_bets = {}
game_running = False
game_task = None


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def 내정보(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = user_balances.get(user_id, 100000)
    user_balances[user_id] = balance
    await update.message.reply_text(f"💰 내 정보입니다\n현재 잔액: {balance:,}원")


async def 바카라(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("최근 게임 결과 15개는 아직 저장되지 않았습니다.")


async def 배팅처리(update: Update, context: ContextTypes.DEFAULT_TYPE, side: str):
    user_id = update.effective_user.id
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("❌ 배팅 금액을 숫자로 정확히 입력해주세요.")
        return

    amount = int(context.args[0])
    balance = user_balances.get(user_id, 100000)

    if balance < amount:
        await update.message.reply_text("❌ 잔액이 부족합니다.")
        return

    user_balances[user_id] = balance - amount
    current_bets.setdefault(side, []).append((user_id, amount))
    await update.message.reply_text(f"✅ {side.upper()}에 {amount:,}원 배팅 완료되었습니다.")

    global game_running, game_task
    if not game_running:
        game_task = asyncio.create_task(게임시작())


async def 뱅(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await 배팅처리(update, context, "banker")


async def 플(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await 배팅처리(update, context, "player")


async def 타이(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await 배팅처리(update, context, "tie")


async def 플페어(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await 배팅처리(update, context, "ppair")


async def 플뱅커(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await 배팅처리(update, context, "bpair")


async def 게임시작():
    global game_running, current_bets
    game_running = True

    await asyncio.sleep(25)

    deck = [random.randint(1, 10) for _ in range(6)]
    p1, b1, p2, b2, p3 = deck[0], deck[1], deck[2], deck[3], deck[4]

    player_total = p1 + p2
    banker_total = b1 + b2

    result_message = [f"🕓 {get_timestamp()} 기준 게임 결과"]
    result_message.append(f"🃏 플레이어 카드: {p1}, {p2}")
    result_message.append(f"🃏 뱅커 카드: {b1}, {b2}")

    if player_total <= 5:
        player_total += p3
        result_message.append(f"➕ 플레이어 추가 카드: {p3}")

    result = "tie"
    if player_total % 10 > banker_total % 10:
        result = "player"
    elif player_total % 10 < banker_total % 10:
        result = "banker"

    result_message.append(f"🏆 최종 결과: {result.upper()} 승리")

    await context_bot().send_message(GROUP_CHAT_ID, "\n".join(result_message))

    # 정산
    for user_id, amount in current_bets.get(result, []):
        prize = amount * 2
        user_balances[user_id] = user_balances.get(user_id, 0) + prize

    current_bets.clear()
    game_running = False


def context_bot():
    return ApplicationBuilder().token(TOKEN).build().bot


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("내정보", 내정보))
    app.add_handler(CommandHandler("바카라", 바카라))
    app.add_handler(CommandHandler("뱅", 뱅))
    app.add_handler(CommandHandler("플", 플))
    app.add_handler(CommandHandler("타이", 타이))
    app.add_handler(CommandHandler("플페어", 플페어))
    app.add_handler(CommandHandler("플뱅커", 플뱅커))

    print("✅ 바카라 봇 실행 중")
    await app.run_polling()


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
