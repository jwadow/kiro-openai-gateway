> Superseded by canonical docs: `fork-docs/FORK_CHANGELOG.md`, `fork-docs/ARCHITECTURE_AUDIT.md`, `fork-docs/SECURITY_REVIEW.md`, `fork-docs/PR_REVIEW_SUMMARY.md`.
> This file is a historical execution prompt, not a maintained project document.

Sen kıdemli bir Staff/Principal Software Engineer + Systems Architect + Reliability Engineer gibi davranacaksın.

Görev bağlamı:
- Proje: Kiro Gateway
- Kullanım şekli: OpenClaw/OpenClub üzerinden Anthropic/OpenAI benzeri modellerle, çoklu sub-agent orkestrasyonu, tool çağrıları, uzun mesaj geçmişi, Telegram benzeri kanallarda canlı akış.
- Beklenti: Yama/hacky çözüm istemiyoruz. Köklü, sürdürülebilir, endüstri standardına uygun mimari ve kod kalitesi istiyoruz.
- Öncelik: Üretimde gecikme, donma, sessizce kaybolma, 4xx/5xx hata döngüsü, büyük payload kaynaklı bozulmalar, concurrency/queue tıkanmaları.

Kesin çalışma prensipleri:
1) Sürekli sub-agent kullan. Tek ajanla ilerleme.
2) Araştırma görevlerini paralel alt görevlere böl.
3) İnternetten bol kaynak tara (benzer gateway/proxy projeleri, LLM adapter mimarileri, reliability patternleri, incident postmortem örnekleri).
4) Her iddiayı kanıtla: dosya yolu, kod referansı, log satırı, test çıktısı.
5) "Bence" yerine "kanıt + çıkarım" formatı kullan.
6) Gereksiz refactor yapma; sorun odaklı ve ölçülebilir iyileştirme yap.
7) Önce PLAN modu, sonra uygulama. Plansız kod değişikliği yapma.

====================================================
FAZ 0 — Bağlamı Doğrula
====================================================
Önce projeyi anlamadan yorum yapma.

Yapılacaklar:
- README, docs, architecture dokümanları, config dosyaları, test yapısı, gateway giriş noktaları, converter/adapter katmanları, route/streaming katmanları, auth/model resolver parçalarını oku.
- Projenin felsefesini çıkar:
  - Gateway bir "taşıma/uyumluluk katmanı" mı?
  - Nerede normalize eder, nerede dönüştürür, nerede fail-safe uygular?
  - Hangi davranışlar ürün kararı, hangileri teknik borç?

Teslim:
- 1 sayfalık "Proje Nasıl Çalışıyor" özeti.
- Kritik veri akışı diyagramı (metinle): giriş -> normalize -> guard -> upstream -> response/stream -> session/log.

====================================================
FAZ 1 — Çoklu Sub-Agent ile Endüstri Araştırması (Paralel)
====================================================
En az 10 paralel sub-agent çalıştır. Her birine farklı araştırma başlığı ver.

Örnek başlıklar:
1) LLM gateway/proxy mimari patternleri (adapter, anti-corruption layer, policy engine).
2) Payload boyutu ve context compaction best practice'leri.
3) Tool result/tool call guard stratejileri (safe truncation, transparent degradation).
4) Multi-agent orchestration queue/backpressure yönetimi.
5) Concurrency sınırları (global/per-provider/per-model) ve adil planlama.
6) Streaming hata toleransı ve yeniden deneme stratejileri.
7) Observability: log/metric/trace standardı (RED, USE, SLO, error budget).
8) Open-source benzer projelerde sık görülen anti-patternler.
9) Naming/structure refactor örnekleri (god file parçalama, bounded context).
10) Incident yönetimi: "sistem kayboldu/sessiz kaldı" senaryolarına tasarım çözümleri.

Her sub-agent çıktısı şu formatta olsun:
- Sorun sınıfı
- Endüstri standardı yaklaşım
- Uygulanabilir pattern
- Risk/Trade-off
- Kiro Gateway'e uyarlama notu
- Kaynak linkleri

Teslim:
- Konsolide "Industry Findings" raporu.

====================================================
FAZ 2 — Kod Kalitesi ve Mimari Denetim (Spagetti/Hacky Analizi)
====================================================
Projeyi satır satır eleştir ama adil ol.

İncelenecek başlıklar:
- Architecture: katman sınırları net mi? sorumluluklar ayrık mı?
- Modülerlik: god file/god function var mı?
- Data flow: dönüşümler deterministik mi, yan etkiler kontrollü mü?
- Guard yapıları: geçici yama mı, sistemik çözüm mü?
- Hata yönetimi: hata sınıfları açık mı, retry/backoff doğru mu?
- Logging: debug ve prod logları anlamlı mı, korelasyon id'leri var mı?
- Test güvencesi: kritik akışlar testli mi? edge-case testleri yeterli mi?
- Klasörleme/dosya isimlendirme/değişken isimlendirme: tutarlılık, okunabilirlik, niyet açıklığı.

Tespit sınıfları:
- P0: üretim riski / veri kaybı / sistem donması
- P1: performans ve güvenilirlik riski
- P2: bakım maliyeti ve okunabilirlik sorunu
- P3: stil ve isimlendirme iyileştirmesi

Her tespit için zorunlu format:
- Bulgular
- Kanıt (dosya:satır)
- Mevcut çözümün niyeti
- Neden yetersiz veya riskli
- Kökten çözüm önerisi
- Geçiş planı (kırmadan nasıl geçilir)

====================================================
FAZ 3 — Çözüm Tasarımı (Önce Plan, Sonra Uygulama)
====================================================
Önce detaylı teknik plan üret. Onay beklemeden kod yazma demiyorum; ama plansız kod yazma.

Plan içeriği:
- Hedef mimari (modül sınırları, sorumluluklar)
- Refactor adımları (küçük ve geri alınabilir adımlar)
- Backward compatibility stratejisi
- Flag/rollout stratejisi (gerekirse)
- Risk matrisi
- Ölçüm planı (hangi metrik düzelecek)

Sonra uygulama:
- Spagetti/hacky alanları refactor et
- İsimlendirme ve klasör yapısını düzenle
- Gereksiz karmaşıklığı azalt
- Kod yorumlarını sadeleştir (yalnız gerekli yerde)

Kısıt:
- "Sadece çalışsın" yaklaşımı yok.
- "Quick fix" yerine "maintainable fix".

====================================================
FAZ 4 — Test Stratejisi (Basit + Kritik)
====================================================
Refactor sonrası testleri katmanlı çalıştır:

1) Hızlı birim testler
2) Kritik entegrasyon testleri
3) Guard davranış testleri (oversize payload, tool-result yoğunluğu, uzun history)
4) Regresyon testleri (önceden patlayan case'ler)

Rapor formatı:
- Hangi test
- Neyi doğruluyor
- Sonuç
- Başarısızsa kök neden

====================================================
FAZ 5 — OpenClaw/OpenClub Canlı Stress Test (Zorlayıcı)
====================================================
Gerçekçi ve agresif test yap. "1-2 istek" yeterli değil.

Zorunlu senaryolar:
1) Çoklu sub-agent paralel araştırma (10+ görev)
2) Farklı model kombinasyonları (haiku/sonnet/opus/gpt vb.)
3) Uzun cevap üreten görevler
4) Web araştırmalı görevler + tool yoğun görevler
5) Queue baskısı + maxConcurrent sınırında davranış
6) Aralıklı kullanıcı mesajı (ana akış meşgulken yeni mesaj)
7) Oturum sürekliliği ("kaybolma", gecikme, sonra toplu dönüş)

Her senaryoda ölç:
- Başlama gecikmesi
- İlk token süresi
- Toplam tamamlanma süresi
- Hata oranı (4xx/5xx/timeout/connection)
- Yeniden deneme davranışı
- Sessiz kalma/NO_REPLY örüntüsü

====================================================
FAZ 6 — Log/Debug Forensics
====================================================
Sadece sonucu değil, log korelasyonunu da çıkar.

Yapılacaklar:
- OpenClaw session transcript + gateway log + service log korele et
- Zaman çizelgesi çıkar (hangi saniyede ne oldu)
- "Sistem kayboldu" anlarını teknik olarak ispatla
- Hata zinciri çıkar (tetikleyici -> ara belirti -> kullanıcı etkisi)

Teslim:
- Incident-style postmortem
  - Impact
  - Root cause(s)
  - Contributing factors
  - Detection gaps
  - Corrective actions
  - Preventive actions

====================================================
FAZ 7 — Nihai Çıktı Paketi
====================================================
Tek seferde aşağıdaki paketleri teslim et:

1) Executive Summary (teknik olmayan kısa özet)
2) Derin Teknik Rapor
3) Kod değişiklik listesi (dosya bazlı)
4) Test sonuçları
5) Stress test sonuçları
6) Log korelasyon ve postmortem
7) Kalan riskler + önerilen sonraki adımlar

====================================================
Kalite Kriterleri (Geçer/Geçmez)
====================================================
Bu maddeleri sağlamayan çıktıyı kabul etme:
- Kanıtsız iddia yok
- Spagetti/hacky tespiti somut örnekli
- Çözüm önerisi kökten ve sürdürülebilir
- İsimlendirme/architecture önerileri tutarlı
- Refactor sonrası testler yeşil
- Canlı stress test yapılmış ve raporlanmış
- Log forensics ile kullanıcı deneyimi teknik olarak açıklanmış

====================================================
Notlar (Kullanıcı felsefesi)
====================================================
- Kullanıcı AI-slop istemiyor.
- "Geçici yama" değil, profesyonel mühendislik yaklaşımı bekliyor.
- Proje bir gateway: güvenilir, öngörülebilir, gözlemlenebilir olmalı.
- Değişiklikler proje mantığına aykırı olmamalı; adapter katmanı doğasına uygun olmalı.

Şimdi bu planı uygula.
Önce FAZ 0 ve FAZ 1 çıktısını üret, sonra kalan fazlara geç.
