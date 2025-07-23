import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 로그 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 사용자 데이터 파일
USERS_FILE = 'users.json'
RESULTS_FILE = 'results.json'
BETS_FILE = 'bets.json'

# 잔액 확인
async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    balance = users.get(user_id, 100000)  # 기본 잔액
    await update.message.reply_text(f"💰 현재 잔액: {balance}원")

# 최근 결과 15개 출력
async def last_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(RESULTS_FILE, 'r') as f:
        results = json.load(f)
    latest = results[-15:]
    await update.message.reply_text("🎲 최근 결과:\n" + "\n".join(latest))

# 배팅 명령
async def place_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("배팅금액을 입력하세요. 예: /뱅 10000")
        return

    amount = int(context.args[0])

    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    balance = users.get(user_id, 100000)

    if balance < amount:
        await update.message.reply_text("❌ 잔액이 부족합니다.")
        return

    users[user_id] = balance - amount
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

    with open(BETS_FILE, 'r') as f:
        bets = json.load(f)
    bets.append({"user_id": user_id, "bet": update.message.text, "amount": amount})
    with open(BETS_FILE, 'w') as f:
        json.dump(bets, f)

    await update.message.reply_text(f"✅ 배팅 완료: {update.message.text} ({amount}원)")

# 봇 메인 실행
async def main():
    app = ApplicationBuilder().token("8016454304:AAGseFUZMxvdp1HzeLiakKNyMy3Envgk0J4").build()

    app.add_handler(CommandHandler("내정보", my_info))
    app.add_handler(CommandHandler("바카라", last_results))
    app.add_handler(CommandHandler(["뱅", "플", "타이", "플페어", "플뱅커"], place_bet))

    print("🤖 봇 실행 중...")
    await app.run_polling()

# 실행 엔트리포인트
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
