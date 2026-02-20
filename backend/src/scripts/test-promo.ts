// Test promo bonus calculation

const PROMO_CONFIG = {
  startDate: new Date('2025-12-31T00:00:00+07:00'),
  endDate: new Date('2026-01-02T00:00:00+07:00'),
  bonusPercent: 20,
};

function isPromoActive(): boolean {
  const now = new Date();
  return now >= PROMO_CONFIG.startDate && now < PROMO_CONFIG.endDate;
}

function calculateCreditsWithBonus(credits: number): number {
  if (isPromoActive()) {
    return credits * (1 + PROMO_CONFIG.bonusPercent / 100);
  }
  return credits;
}

// Test cases
console.log('=== PROMO TEST ===');
console.log('Current time:', new Date().toISOString());
console.log('Promo start:', PROMO_CONFIG.startDate.toISOString());
console.log('Promo end:', PROMO_CONFIG.endDate.toISOString());
console.log('Bonus percent:', PROMO_CONFIG.bonusPercent + '%');
console.log('');
console.log('Is promo active now?', isPromoActive());
console.log('');
console.log('=== Credit calculations ===');

const testAmounts = [20, 50, 100];
for (const amount of testAmounts) {
  const withBonus = calculateCreditsWithBonus(amount);
  const bonus = withBonus - amount;
  console.log(`$${amount} → $${withBonus} (bonus: +$${bonus})`);
}

// Test with simulated dates
console.log('');
console.log('=== Simulated date tests ===');

function testWithDate(dateStr: string, credits: number) {
  const testDate = new Date(dateStr);
  const active = testDate >= PROMO_CONFIG.startDate && testDate < PROMO_CONFIG.endDate;
  const result = active ? credits * (1 + PROMO_CONFIG.bonusPercent / 100) : credits;
  
  console.log(`${dateStr}: promo=${active}, $${credits} → $${result}`);
}

testWithDate('2025-12-30T23:59:59+07:00', 20); // Before promo
testWithDate('2025-12-31T00:00:01+07:00', 20); // Promo starts
testWithDate('2025-12-31T12:00:00+07:00', 20); // During promo
testWithDate('2026-01-01T23:59:59+07:00', 20); // Still promo
testWithDate('2026-01-02T00:00:01+07:00', 20); // After promo
