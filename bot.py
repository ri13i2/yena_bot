import asyncio
import random
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = "8016454304:AAGseFUZMxvdp1HzeLiakKNyMy3Envgk0J4"
GROUP_CHAT_ID = -1002799021115  # 실제 그룹 ID로 바꿔주세요

# 유저 잔액과 배팅 정보
balances = {}
bets = {}
game_running = False

# 카드 생성 함수
def draw_card():
    return random.choice(['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'])

def card_value(card):
    if card in ['J', 'Q', 'K', '10']:
        return 0
    elif card == 'A':
        return 1
    return int(card)

def calculate_score(cards):
    return sum([card_value(c) for c in cards]) % 10

# 명령어 핸들러
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balances[user_id] = 10000000
    await update.message.reply_text("환영합니다! 잔액이 10,000,000원으로 설정되었습니다.")

async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = balances.get(user_id, 0)
    await update.message.reply_text(f"현재 잔액은 {balance:,}원 입니다.")

async def bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_running
    user_id = update.effective_user.id
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("배팅 금액을 입력하세요. 예: /뱅 10000")
        return

    amount = int(context.args[0])
    if balances.get(user_id, 0) < amount:
        await update.message.reply_text("❌ 잔액이 부족합니다. /myinfo 로 잔액 확인")
        return

    bet_type = update.message.text.split(" ")[0][1:]  # 명령어 이름 (뱅, 플, 타이 등)
    balances[user_id] -= amount
    bets[user_id] = (bet_type, amount)
    await update.message.reply_text(f"✅ [{bet_type.upper()}] {amount:,}원 배팅 완료!")

    if not game_running:
        asyncio.create_task(game_loop(context.bot))
        game_running = True

async def game_loop(bot):
    global game_running
    await bot.send_message(chat_id=GROUP_CHAT_ID, text=f"🎰 게임이 25초 후 시작됩니다. ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    await asyncio.sleep(25)

    player_cards = [draw_card(), draw_card()]
    banker_cards = [draw_card(), draw_card()]

    await bot.send_message(chat_id=GROUP_CHAT_ID, text=f"플레이어 카드: {player_cards[0]} ?")
    await asyncio.sleep(2)
    await bot.send_message(chat_id=GROUP_CHAT_ID, text=f"뱅커 카드: {banker_cards[0]} ?")
    await asyncio.sleep(2)
    await bot.send_message(chat_id=GROUP_CHAT_ID, text=f"플레이어 두 번째 카드: {player_cards[1]}")
    await asyncio.sleep(2)
    await bot.send_message(chat_id=GROUP_CHAT_ID, text=f"뱅커 두 번째 카드: {banker_cards[1]}")

    player_score = calculate_score(player_cards)
    banker_score = calculate_score(banker_cards)

    result = "타이"
    if player_score > banker_score:
        result = "플"
    elif banker_score > player_score:
        result = "뱅"

    await bot.send_message(chat_id=GROUP_CHAT_ID, text=f"🎯 게임 결과: {result.upper()} (플: {player_score}, 뱅: {banker_score})")

    # 결과 정산
    for user_id, (bet_type, amount) in bets.items():
        if bet_type == result:
            balances[user_id] += amount * 2  # 1:1 배당
            try:
                await bot.send_message(chat_id=user_id, text=f"🎉 당첨! {amount*2:,}원 획득! 잔액: {balances[user_id]:,}원")
            except:
                pass
        else:
            try:
                await bot.send_message(chat_id=user_id, text=f"💸 실패. 잔액: {balances[user_id]:,}원")
            except:
                pass

    bets.clear()
    game_running = False

# 앱 실행
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myinfo", myinfo))
    app.add_handler(CommandHandler("뱅", bet_handler))
    app.add_handler(CommandHandler("플", bet_handler))
    app.add_handler(CommandHandler("타이", bet_handler))
    app.add_handler(CommandHandler("플페어", bet_handler))
    app.add_handler(CommandHandler("뱅페어", bet_handler))

    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
