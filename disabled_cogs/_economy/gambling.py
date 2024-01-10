import random

def play_slots(bet):
    items = ["🍒", "🍋", "🍊", "🍉", "7️⃣"]
    result = random.choices(items, k=3)

    if len(set(result)) == 1:
        if result[0] == "7️⃣":
            win_amount = bet * 10
        else:
            win_amount = bet * 5
        return True, win_amount, result
    elif len(set(result)) == 2:
        win_amount = bet * 2
        return True, win_amount, result
    else:
        return False, bet, result


def play_blackjack(bet):
    def draw_card():
        return random.randint(2, 11)

    player_score = draw_card() + draw_card()
    dealer_score = draw_card() + draw_card()

    while player_score < 17:
        player_score += draw_card()

    while dealer_score < 17:
        dealer_score += draw_card()

    if player_score > 21 or (dealer_score <= 21 and dealer_score > player_score):
        return False, bet, player_score, dealer_score
    elif player_score == dealer_score:
        return 'draw', bet, player_score, dealer_score
    else:
        win_amount = bet * 2
        return True, win_amount, player_score, dealer_score

