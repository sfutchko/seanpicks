#!/usr/bin/env python3
"""Test professional betting edges"""

from app.services.professional_edges import ProfessionalEdgeCalculator, calculate_true_probability

calc = ProfessionalEdgeCalculator()

print('🎯 PROFESSIONAL BETTING EDGES DEMONSTRATION')
print('=' * 50)

# 1. No-Vig Line (True Probability)
print('\n1️⃣ NO-VIG PROBABILITY (Remove the juice):')
print('   DraftKings: Patriots -150, Jets +130')
true_probs = calculate_true_probability(-150, 130)
print(f'   TRUE ODDS: Patriots {true_probs["home_true_prob"]}% ({true_probs["home_no_vig_line"]})')
print(f'             Jets {true_probs["away_true_prob"]}% ({true_probs["away_no_vig_line"]})')
print('   ✅ This is the "fair" line without bookie profit')

# 2. Expected Value
print('\n2️⃣ EXPECTED VALUE CALCULATION:')
our_prob = 0.58  # We think Patriots have 58% chance
ev = calc.calculate_expected_value(our_prob, -150, 100)
print(f'   Our Model: 58% Patriots win probability')
print(f'   Line: -150 (implied 60%)')
print(f'   EV: ${ev["expected_value"]} per $100 bet ({ev["ev_percentage"]}%)')
print(f'   Edge: {ev["edge"]}%')
if ev['is_positive_ev']:
    print('   ✅ POSITIVE EV - BET IT!')
else:
    print('   ❌ Negative EV - PASS')

# 3. Kelly Criterion Sizing
print('\n3️⃣ KELLY CRITERION BET SIZING:')
kelly = calc.kelly_criterion(0.58, -150)
print(f'   Optimal bet size: {kelly*100:.1f}% of bankroll')
print(f'   On $1000 bankroll: ${kelly*1000:.0f}')
print('   (Using 1/4 Kelly for safety)')

# 4. Closing Line Value
print('\n4️⃣ CLOSING LINE VALUE TRACKING:')
clv = calc.track_closing_line_value(-150, -165, did_bet_win=True)
print(f'   Our bet: -150')
print(f'   Closing: -165')
print(f'   Beat CLV: {clv["beat_closing"]} ({clv["clv_points"]} points)')
print('   ✅ Line moved our way - sharp indicator!')

# 5. Check different scenarios
print('\n5️⃣ MORE CLV EXAMPLES:')
scenarios = [
    (-110, -115, "Small CLV win"),
    (+150, +140, "Lost CLV on dog"),
    (-200, -180, "Big CLV win on favorite"),
    (+100, -110, "Line flipped - bad CLV")
]

for pick, close, desc in scenarios:
    result = calc.track_closing_line_value(pick, close)
    symbol = "✅" if result["beat_closing"] else "❌"
    print(f'   {symbol} {desc}: {pick} → {close}')

print(f'\n   Career CLV: {clv.get("career_clv_percentage", 0)}%')
print(f'   Grade: {clv.get("clv_grade", "N/A")}')

# 6. Middle Opportunities
print('\n6️⃣ MIDDLE & SCALP OPPORTUNITIES:')
print('   Example: Patriots -2.5 at DK, Jets +3.5 at FD')
print('   If Patriots win by exactly 3, BOTH bets win!')
print('   This is called a "middle" - risk-free profit zone')

# 7. Arbitrage Example
print('\n7️⃣ ARBITRAGE (RISK-FREE PROFIT):')
print('   Rare but exists during line moves:')
print('   Team A: +110 at Book1')
print('   Team B: +105 at Book2')
prob_a = 100/210  # +110 
prob_b = 100/205  # +105
total = prob_a + prob_b
if total < 1:
    profit = (1 - total) * 100
    print(f'   Combined probability: {total:.3f} < 1.0')
    print(f'   Guaranteed profit: {profit:.2f}%')

print('\n' + '=' * 50)
print('💰 WHAT SEPARATES PROS FROM AMATEURS:')
print()
print('PROS TRACK:')
print('  ✅ CLV% - Beat closing line 52%+ of time')
print('  ✅ EV - Only bet positive expected value')  
print('  ✅ ROI by situation, book, bet type')
print('  ✅ Actual vs Expected variance')
print()
print('PROS USE:')
print('  ✅ No-vig lines for true probability')
print('  ✅ Kelly Criterion for bet sizing')
print('  ✅ Multiple books (10-15 accounts)')
print('  ✅ Automated betting for speed')
print()
print('PROS EXPLOIT:')
print('  ✅ Player props (less efficient)')
print('  ✅ Derivative markets (1H, 1Q, TT)')
print('  ✅ Live betting algorithms')
print('  ✅ Weather/injury news first')
print()
print('THE TRUTH:')
print('  📊 Volume > Big Edges')
print('  📊 2% edge on 1000 bets > 10% edge on 50 bets')
print('  📊 Closing line is all that matters long-term')
print('  📊 Variance is huge - need 10,000+ bet sample')

print('\n' + '=' * 50)
print('🎲 CURRENT MISSING FROM OUR APP:')
print('  1. CLV tracking (easy to add)')
print('  2. True betting % data ($99/mo)')
print('  3. Player props module')
print('  4. More books for line shopping')
print('  5. Backtesting engine')
print('  6. Live win probability model')
print('  7. Injury impact quantification')