import json
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)
import random

# 기본 설정
TOKEN = "YOUR_BOT_TOKEN"  # 여기에 본인의 텔레그램 봇 토큰 입력
users_file = "users.json"
bets_file = "bets.json"
results_file = "results.json"

# 데이터 로딩/저장 함수
def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 사용자 정보 초기화
def get_user(user_id):
    users = load_json(users_file)
    if str(user_id) not in users:
        users[str(user_id)] = {"balance": 100000}
        save_json(users_file, users)
    return users[str(user_id)]

# 명령어: /내정보
async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    await update.message.reply_text(f"💰 현재 잔액: {user['balance']:,}원")

# 명령어: /바카라 (최근 결과 15개)
async def baccarat_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = load_json(results_file)
    history = results.get("history", [])[-15:]
    if not history:
        await update.message.reply_text("아직 게임 결과가 없습니다.")
    else:
        await update.message.reply_text("🎲 최근 바카라 결과:\n" + "\n".join(history))

# 배팅 처리
async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()
    user = get_user(user_id)

    commands = ["/뱅", "/플", "/타이", "/플페어", "/플뱅커"]
    for cmd in commands:
        if message.startswith(cmd):
            try:
                parts = message.split()
                if len(parts) != 2:
                    raise ValueError
                amount = int(parts[1])
                if amount <= 0:
                    raise ValueError
                if user["balance"] < amount:
                    await update.message.reply_text("❗ 잔액이 부족합니다.")
                    return
                user["balance"] -= amount
                save_json(users_file, load_json(users_file) | {str(user_id): user})

                bets = load_json(bets_file)
                if str(user_id) not in bets:
                    bets[str(user_id)] = []
                bets[str(user_id)].append({"type": cmd, "amount": amount})
                save_json(bets_file, bets)

                await update.message.reply_text(f"✅ {cmd}에 {amount:,}원 배팅 완료")
            except:
                await update.message.reply_text("❗ 올바른 형식: /뱅 10000")
            return

# 게임 결과 생성 및 배당
async def game_loop():
    while True:
        bets = load_json(bets_file)
        results = load_json(results_file)
        users = load_json(users_file)

        if bets:
            outcome = random.choice(["플", "뱅", "타이"])
            results.setdefault("history", []).append(outcome)
            results["history"] = results["history"][-50:]
            save_json(results_file, results)

            # 배당 처리
            for user_id, user_bets in bets.items():
                user = users.get(user_id, {"balance": 100000})
                for bet in user_bets:
                    if bet["type"] == f"/{outcome}":
                        win = bet["amount"] * 2
                        user["balance"] += win
                users[user_id] = user

            save_json(users_file, users)
            save_json(bets_file, {})  # 배팅 초기화

            # 유저에게 결과 전송
            for user_id in users:
                try:
                    await app.bot.send_message(chat_id=int(user_id), text=f"🎲 이번 게임 결과: {outcome}")
                except:
                    pass
        await asyncio.sleep(60)  # 1분 간격

# 메인 실행
async def main():
    global app
    app = ApplicationBuilder().token(TOKEN).build()

    # 한글 커맨드 처리 핸들러
    app.add_handler(MessageHandler(filters.Regex(r"^/내정보$"), my_info))
    app.add_handler(MessageHandler(filters.Regex(r"^/바카라$"), baccarat_history))
    app.add_handler(MessageHandler(filters.Regex(r"^/(뱅|플|타이|플페어|플뱅커) \d+$"), handle_bet))

    # 게임 루프 비동기로 실행
    asyncio.create_task(game_loop())

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
