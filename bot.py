import asyncio
import datetime
import random
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8016454304:AAGseFUZMxvdp1HzeLiakKNyMy3Envgk0J4"

users = {}
bets = {}
results = {}

CARD_VALUES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10']

def draw_card():
    return random.choice(CARD_VALUES)

def card_point(card):
    if card == 'A':
        return 1
    elif card in ['10']:
        return 0
    else:
        return int(card)

def calculate_score(cards):
    return sum([card_point(card) for card in cards]) % 10

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users.setdefault(user_id, 100000)
    await update.message.reply_text("🃏 예나찡 바카라에 오신 걸 환영합니다!\n/bet 명령어로 배팅해주세요.")

async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    balance = users.get(user_id, 0)
    await update.message.reply_text(f"💰 현재 보유금액: {balance:,}원")

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❌ 형식: /bet [플/뱅/타이] [금액]")
        return

    position_map = {"플": "Player", "뱅": "Banker", "타이": "Tie"}
    position = args[0]
    amount = int(args[1])

    if position not in position_map:
        await update.message.reply_text("❌ 배팅 포지션은 플, 뱅, 타이 중 하나여야 합니다.")
        return

    balance = users.get(user_id, 0)
    if balance < amount:
        await update.message.reply_text("⚠️ 보유금액이 부족합니다!")
        return

    users[user_id] -= amount
    bets.setdefault(user_id, []).append({"position": position_map[position], "amount": amount})

    await update.message.reply_text(
        f"🎲 배팅 완료!\n"
        f"📌 배팅 항목: {position_map[position]}\n"
        f"💵 배팅 금액: {amount:,}원\n"
        f"⏱️ {datetime.datetime.now().strftime('%m월 %d일 %H:%M:%S')}"
    )

async def game_loop(app):
    while True:
        if bets:
            await app.bot.send_message(chat_id=list(bets.keys())[0], text="🎰 게임 시작!")

            player_cards = [draw_card(), draw_card()]
            banker_cards = [draw_card(), draw_card()]
            player_score = calculate_score(player_cards)
            banker_score = calculate_score(banker_cards)

            if player_score <= 5:
                player_cards.append(draw_card())
                player_score = calculate_score(player_cards)

            if banker_score <= 5:
                banker_cards.append(draw_card())
                banker_score = calculate_score(banker_cards)

            if player_score > banker_score:
                winner = "Player"
            elif banker_score > player_score:
                winner = "Banker"
            else:
                winner = "Tie"

            for user_id, user_bets in bets.items():
                total_win = 0
                for b in user_bets:
                    if b["position"] == winner:
                        if winner == "Tie":
                            win_amount = b["amount"] * 8
                        else:
                            win_amount = b["amount"] * 2
                        users[user_id] += win_amount
                        total_win += win_amount

                await app.bot.send_message(chat_id=user_id, text=(
                    f"🎲 게임 결과!\n"
                    f"👤 플레이어 카드: {player_cards} ({player_score})\n"
                    f"🏦 뱅커 카드: {banker_cards} ({banker_score})\n"
                    f"🏆 승자: {winner}\n"
                    f"💰 적중금액: {total_win:,}원\n"
                    f"📅 {datetime.datetime.now().strftime('%m월 %d일 %H:%M:%S')}"
                ))

            bets.clear()

        await asyncio.sleep(25)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bet", bet))
    app.add_handler(CommandHandler("내정보", my_info))

    asyncio.create_task(game_loop(app))
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
