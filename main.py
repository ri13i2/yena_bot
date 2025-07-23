import json
import random
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = '8016454304:AAGseFUZMxvdp1HzeLiakKNyMy3Envgk0J4'  # ← 여기에 텔레그램 봇 토큰 입력

USERS_FILE = 'users.json'
BETS_FILE = 'bets.json'
RESULTS_FILE = 'results.json'

game_running = False

# ---------------- JSON 유틸 ---------------- #
def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)

# ---------------- 사용자 초기화 ---------------- #
async def 시작(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_json(USERS_FILE)
    if user_id not in users:
        users[user_id] = {'balance': 10000}
        save_json(USERS_FILE, users)
        await update.message.reply_text("🎲 시작되었습니다! 잔액: 10,000원")
    else:
        await update.message.reply_text("이미 시작하셨습니다. /내정보로 확인해보세요.")

# ---------------- 잔액 확인 ---------------- #
async def 내정보(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_json(USERS_FILE)
    bal = users.get(user_id, {}).get('balance', 0)
    await update.message.reply_text(f"💰 현재 잔액: {bal}원")

# ---------------- 결과 출력 ---------------- #
async def 바카라(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = load_json(RESULTS_FILE).get("history", [])
    if not results:
        await update.message.reply_text("아직 게임 결과가 없습니다.")
    else:
        result_str = "\n".join([f"{i+1}. {r}" for i, r in enumerate(results[-15:][::-1])])
        await update.message.reply_text(f"🎰 최근 게임 결과:\n{result_str}")

# ---------------- 배팅 커맨드 공통 ---------------- #
async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_running

    user_id = str(update.effective_user.id)
    cmd = update.message.text.split()
    if len(cmd) != 2:
        await update.message.reply_text("사용법: /명령어 금액 (예: /뱅 1000)")
        return

    bet_type = update.message.text.split()[0][1:]  # /뱅 → 뱅
    try:
        amount = int(cmd[1])
    except:
        await update.message.reply_text("금액은 숫자여야 합니다.")
        return

    if bet_type not in ['뱅', '플', '타이', '플페어', '플뱅커']:
        await update.message.reply_text("잘못된 배팅 명령어입니다.")
        return

    users = load_json(USERS_FILE)
    if user_id not in users:
        await update.message.reply_text("먼저 /시작 으로 가입해주세요.")
        return

    if users[user_id]['balance'] < amount:
        await update.message.reply_text("💸 잔액이 부족합니다.")
        return

    users[user_id]['balance'] -= amount
    save_json(USERS_FILE, users)

    bets = load_json(BETS_FILE)
    if bet_type not in bets:
        bets[bet_type] = {}
    bets[bet_type][user_id] = bets[bet_type].get(user_id, 0) + amount
    save_json(BETS_FILE, bets)

    await update.message.reply_text(f"✅ {bet_type.upper()}에 {amount}원 배팅 완료")

    if not game_running:
        asyncio.create_task(run_game())

# ---------------- 게임 실행 ---------------- #
async def run_game():
    global game_running
    game_running = True
    await asyncio.sleep(30)  # 30초 대기 후 게임 실행

    bets = load_json(BETS_FILE)
    users = load_json(USERS_FILE)
    results = load_json(RESULTS_FILE)

    # 랜덤 결과 생성
    main_result = random.choices(['뱅', '플', '타이'], weights=[45, 45, 10])[0]
    banker_pair = random.choice([True, False])
    player_pair = random.choice([True, False])

    result_msg = f"🎲 게임 결과\n▶️ 메인: {main_result.upper()}"
    if banker_pair: result_msg += "\n💠 뱅커페어"
    if player_pair: result_msg += "\n💠 플레이어페어"

    # 유저별 정산
    payout_rate = {'뱅': 0.95, '플': 1, '타이': 8, '플페어': 11, '플뱅커': 11}
    messages = {}

    for bet_type in bets:
        for user_id, amount in bets[bet_type].items():
            win = False
            if bet_type == main_result:
                win = True
            elif bet_type == '플페어' and player_pair:
                win = True
            elif bet_type == '플뱅커' and banker_pair:
                win = True

            if win:
                reward = int(amount * payout_rate[bet_type])
                users[user_id]['balance'] += reward + amount
                txt = f"✅ {bet_type.upper()} 적중! +{reward}원"
            else:
                txt = f"❌ {bet_type.upper()} 실패..."

            if user_id not in messages:
                messages[user_id] = []
            messages[user_id].append(txt)

    # 결과 저장
    results.setdefault("history", []).append(main_result.upper())
    results["history"] = results["history"][-15:]
    save_json(RESULTS_FILE, results)
    save_json(USERS_FILE, users)
    save_json(BETS_FILE, {})  # 배팅 초기화

    # 메시지 전송
    app = ApplicationBuilder().token(TOKEN).build()
    for user_id, msgs in messages.items():
        try:
            await app.bot.send_message(chat_id=int(user_id), text=f"{result_msg}\n\n" + "\n".join(msgs))
        except:
            pass

    game_running = False

# ---------------- 봇 실행 ---------------- #
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("시작", 시작))
app.add_handler(CommandHandler("내정보", 내정보))
app.add_handler(CommandHandler("바카라", 바카라))
app.add_handler(CommandHandler("뱅", handle_bet))
app.add_handler(CommandHandler("플", handle_bet))
app.add_handler(CommandHandler("타이", handle_bet))
app.add_handler(CommandHandler("플페어", handle_bet))
app.add_handler(CommandHandler("플뱅커", handle_bet))

app.run_polling()
