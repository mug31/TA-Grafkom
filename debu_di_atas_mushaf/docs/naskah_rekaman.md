# Naskah Rekaman Suara — "Debu di Atas Mushaf"

Berdasarkan `animasi_tokoh.py` (12 dialog, 24 fps, total 2016 frame = 1:24).
Timecode = waktu **mulai** dialog di video final. Durasi = target panjang rekaman
(mulut animasi dihitung dari durasi ini — kalau rekaman lebih panjang/lebih pendek,
laju buka-tutup mulut perlu disesuaikan di `bicara(...)`).

| # | Karakter | Mulai | Durasi | Teks |
|---|----------|-------|--------|------|
| 1 | Abu | 0:12.7 | ±4,2 s | udah pagi lagi, ya. Alhamdulillah, tenang kayak biasa. |
| 2 | Rami | 0:17.3 | ±4,9 s | Hari ke dua ratus sebelas, lho. Terakhir dibuka pas malam dua puluh tujuh Ramadan. |
| 3 | Piko | 0:22.5 | ±5,4 s | Iya... dulu tiap habis Subuh ada yang ngaji. Sekarang sepi, cuma detak jam. |
| 4 | Bayu | 0:29.2 | ±4,5 s | Assalamu'alaikum... boleh numpang, nggak? Di luar anginnya kencang banget. |
| 5 | Abu | 0:34.3 | ±5,5 s | Wa'alaikumussalam. Masuk aja! Di sini paling aman, nggak ada yang pernah nyentuh. |
| 6 | Bayu | 0:41.5 | ±3,0 s | Eh, ini buku apa? Kok ditaruh tinggi banget? |
| 7 | Abu | 0:44.9 | ±3,9 s | Ini Al-Qur'an. Benda paling dihormati di rumah ini, dong. |
| 8 | Bayu | 0:49.9 | ±3,0 s | Dihormati... tapi kok nggak pernah dibuka? |
| 9 | Piko | 0:56.2 | ±3,2 s | Kalau nanti dibaca lagi, kita pindah ke mana? |
| 10 | Rami | 0:59.7 | ±2,1 s | Ya pergi. Memang harusnya begitu. |
| 11 | Abu | 1:02.3 | ±5,0 s | Astaghfirullah... kita betah di sini justru karena Al-Qur'an ini ditinggalkan. |
| 12 | Abu | 1:14.7 | ±2,2 s | Alhamdulillah... akhirnya. |

---

## Per karakter

### ABU — debu tertua, tuan rumah
Suara: berat, tenang, paling tua di antara mereka. Paling banyak baris (5).

1. **0:12.7 (±4,2 s)** — "udah pagi lagi, ya. Alhamdulillah, tenang kayak biasa."
   *Setelah menguap ("Hoaam...").* Nada malas tapi damai. "Hoaam" tidak perlu direkam,
   itu animasi menguap saja.
2. **0:34.3 (±5,5 s)** — "Wa'alaikumussalam. Masuk aja! Di sini paling aman, nggak ada yang pernah nyentuh."
   *Ramah, agak bangga di bagian "paling aman".*
3. **0:44.9 (±3,9 s)** — "Ini Al-Qur'an. Benda paling dihormati di rumah ini, dong."
   *Bangga, menekankan "paling dihormati".*
4. **1:02.3 (±5,0 s)** — "Astaghfirullah... kita betah di sini justru karena Al-Qur'an ini ditinggalkan."
   *Menunduk, menyesal. Jeda panjang setelah "Astaghfirullah".*
5. **1:14.7 (±2,2 s)** — "Alhamdulillah... akhirnya."
   *Lirih, lega, hampir berbisik.*

### RAMI — pencatat hari, agak cemas
Suara: agak cepat, cempreng/khawatir, seperti orang mencatat sambil ngomel.

1. **0:17.3 (±4,9 s)** — "Hari ke dua ratus sebelas, lho. Terakhir dibuka pas malam dua puluh tujuh Ramadan."
   *Cepat (6,5 suku kata/detik), menekankan "dua ratus sebelas" dan "lho".*
2. **0:59.7 (±2,1 s)** — "Ya pergi. Memang harusnya begitu."
   *Datar, pasrah. Bukan sedih berlebihan.*

### PIKO — debu terkecil, polos
Suara: kecil, pelan, lirih. Anak-anak tapi bukan cengeng.

1. **0:22.5 (±5,4 s)** — "Iya... dulu tiap habis Subuh ada yang ngaji. Sekarang sepi, cuma detak jam."
   *Pelan, melamun, tempo turun di "sekarang sepi".*
2. **0:56.2 (±3,2 s)** — "Kalau nanti dibaca lagi, kita pindah ke mana?"
   *Lirih, tanya polos — bukan panik.*

### BAYU — debu baru, terbawa angin
Suara: cerah, energik, agak berisik/ramai. Pendatang.

1. **0:29.2 (±4,5 s)** — "Assalamu'alaikum... boleh numpang, nggak? Di luar anginnya kencang banget."
   *Sopan tapi napas masih ngos-ngosan ditiup angin.*
2. **0:41.5 (±3,0 s)** — "Eh, ini buku apa? Kok ditaruh tinggi banget?"
   *Hernan, cepat, naif.*
3. **0:49.9 (±3,0 s)** — "Dihormati... tapi kok nggak pernah dibuka?"
   *Polos, lalu hening (semua debu terdiam).*

---

## Catatan teknis
- Semua baris **1 take per baris**, tanpa musik latar. Rekam mono 48 kHz / 24-bit.
- Jeda tanda baca sudah diperhitungkan: `...` = 10 frame (±0,42 s), `. ? !` = 7 frame
  (±0,29 s), `,` = 4 frame (±0,17 s).
- Tanda `'` di "Wa'alaikumussalam", "Al-Qur'an", "Assalamu'alaikum" — ucapkan natural
  (wa-a-laikumussalam), bukan "wa koma alaikum".
- Selip 1-2 detik kosong di awal & akhir tiap file sebelum dipotong.