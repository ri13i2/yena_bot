import asyncio
import logging
import random
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8016454304:AAGseFUZMxvdp1HzeLiakKNyMy3Envgk0J4"
GROUP_CHAT_ID = -1002799021115  # 실제 그룹 ID로 교체

user_balances = {}
bets = {}
game_running = False

logging.basicConfig(level=logging.INFO)

# 게임 결과 계산 함수
def calculate_result(cards):
    player = cards["플레이어"]
    banker = cards["뱅커"]

    def baccarat_value(cards):
        return sum(cards) % 10

    player_total = baccarat_value(player)
    banker_total = baccarat_value(banker)

    if player_total > banker_total:
        return "플"
    elif banker_total > player_total:
        return "뱅"
    else:
        return "타이"

# 카드 생성 함수
def draw_cards():
    def draw():
        return random.randint(1, 9)
    cards = {
        "플레이어": [draw(), draw()],
        "뱅커": [draw(), draw()]
    }
    return cards

# 잔액 확인
async def 내정보(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = user_balances.get(user_id, 10000)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"💰 현재 잔액: {balance:,}원")

# 배팅 핸들러
async def bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_running
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    chat_id = update.effective_chat.id

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("사용법: /플 10000 또는 /뱅 5000 등으로 입력해주세요.")
        return

    amount = int(context.args[0])
    if amount <= 0:
        await update.message.reply_text("배팅 금액은 0보다 커야 합니다.")
        return

    balance = user_balances.get(user_id, 10000)
    if balance < amount:
        await update.message.reply_text("❗ 배팅 금액이 부족합니다.")
        return

    cmd = update.message.text.split()[0][1:]
    bets.setdefault(user_id, {"금액": 0, "선택": "", "이름": username})
    bets[user_id]["금액"] = amount
    bets[user_id]["선택"] = cmd
    user_balances[user_id] = balance - amount

    await update.message.reply_text(f"✅ {username}님 {cmd}에 {amount:,}원 배팅 완료!")

    if not game_running:
        game_running = True
        await asyncio.sleep(25)
        await run_game(context)

# 게임 실행
async def run_game(context):
    global bets, game_running

    cards = draw_cards()

    # 플레이어 카드 추가 여부
    player_total = sum(cards["플레이어"]) % 10
    if player_total <= 5:
        cards["플레이어"].append(random.randint(1, 9))

    result = calculate_result(cards)
    result_message = f"🃏 바카라 결과\n"
    result_message += f"플레이어: {cards['플레이어']}\n"
    result_message += f"뱅커: {cards['뱅커']}\n"
    result_message += f"🎯 결과: {result}\n"
    result_message += f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=result_message)

    for uid, bet in bets.items():
        if bet["선택"] == result:
            win = bet["금액"] * 2
            user_balances[uid] = user_balances.get(uid, 10000) + win

    bets.clear()
    game_running = False

# 메인 함수
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("내정보", 내정보, block=False))
    app.add_handler(CommandHandler("플", bet_handler, block=False))
    app.add_handler(CommandHandler("뱅", bet_handler, block=False))
    app.add_handler(CommandHandler("타이", bet_handler, block=False))
    app.add_handler(CommandHandler("뱅페어", bet_handler, block=False))
    app.add_handler(CommandHandler("바카라", 내정보, block=False))  # 테스트용 커맨드

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
