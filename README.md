# SkyLink Aviation Weather API

SkyLink Direct API menyediakan data cuaca penerbangan METAR dan TAF.

> API ini menyediakan data cuaca untuk stasiun/bandara yang memiliki laporan
> METAR atau TAF. Tidak semua bandara menerbitkan kedua jenis laporan.

## Daftar isi

- [Persiapan](#persiapan)
- [Autentikasi dan batas request](#autentikasi-dan-batas-request)
- [Endpoint METAR](#endpoint-metar)
- [Endpoint TAF](#endpoint-taf)
- [Menemukan stasiun cuaca Indonesia](#menemukan-stasiun-cuaca-indonesia)
- [Menjalankan contoh dan menyimpan JSON](#menjalankan-contoh-dan-menyimpan-json)
- [Format file hasil batch](#format-file-hasil-batch)
- [Error dan penanganannya](#error-dan-penanganannya)

## Persiapan

Gunakan Python 3.8 atau lebih baru dan pasang dependensi:

```bash
python3 -m pip install -r requirements.txt
```

Tambahkan API key SkyLink Direct ke file `.env` pada root project:

```env
SKYLINK_API_KEY=your_api_key
```

Script juga menerima `RAPIDAPI_KEY` untuk kompatibilitas, tetapi contoh di
dokumentasi ini menggunakan autentikasi SkyLink Direct.

## Autentikasi dan batas request

Semua request SkyLink Direct harus menyertakan API key di header:

```http
x-api-key: YOUR_API_KEY
```

Base URL:

```text
https://data.skylinkapi.com/v3.1
```

Batas laju bergantung pada paket. Paket Free Trial dibatasi satu request per
detik. Contoh Python menunggu minimal **1,2 detik** antara request SkyLink dan
melakukan retry dengan exponential backoff untuk `429`, `500`, `502`, dan
`504`. Request tetap dapat dihitung ke kuota bulanan, termasuk request yang
berakhir dengan error setelah terautentikasi.

## Endpoint METAR

METAR adalah observasi cuaca aktual di stasiun/bandara.

```http
GET https://data.skylinkapi.com/v3.1/weather/metar/{icao}
```

### Parameter

| Nama | Lokasi | Wajib | Tipe | Keterangan |
|---|---|---:|---|---|
| `icao` | Path | Ya | string | Kode ICAO stasiun, umumnya 4 huruf, misalnya `WIII`. |
| `parsed` | Query | Tidak | boolean | Jika `true`, tambahkan hasil parsing terstruktur pada properti `parsed`. Default `false`. |

Contoh request dengan METAR terurai:

```bash
curl --get "https://data.skylinkapi.com/v3.1/weather/metar/WIII" \
  --data-urlencode "parsed=true" \
  -H "x-api-key: YOUR_API_KEY"
```

### Contoh response

Response dasar berisi laporan mentah dan metadata stasiun:

```json
{
  "raw": "METAR WIII 090300Z 27005KT 6000 FEW020 31/24 Q1010 NOSIG",
  "icao": "WIII",
  "airport_name": "Soekarno-Hatta International Airport",
  "timestamp": "2026-10-09T03:05:00Z"
}
```

Jika memakai `parsed=true`, response juga memiliki objek `parsed`. Contoh
berikut menunjukkan bentuk datanya; nilai aktual, satuan, dan field yang
tersedia mengikuti laporan sumber:

```json
{
  "raw": "METAR WIII 090300Z 27005KT 6000 FEW020 31/24 Q1010 NOSIG",
  "icao": "WIII",
  "airport_name": "Soekarno-Hatta International Airport",
  "timestamp": "2026-10-09T03:05:00Z",
  "parsed": {
    "time": "2026-10-09T03:00:00+00:00",
    "wind": {
      "direction": 270,
      "speed": 5,
      "gust": null,
      "variable": []
    },
    "visibility": {
      "value": 6000,
      "repr": "6000"
    },
    "clouds": [
      {
        "type": "FEW",
        "base": 20,
        "repr": "FEW020"
      }
    ],
    "temperature": 31,
    "dewpoint": 24,
    "altimeter": 1010,
    "flight_rules": "MVFR",
    "wx_codes": [],
    "remarks": "NOSIG",
    "density_altitude": 2000,
    "pressure_altitude": 100,
    "relative_humidity": 0.67
  }
}
```

Field utama di `parsed`:

| Field | Keterangan |
|---|---|
| `time` | Waktu observasi pada laporan, ISO 8601. Gunakan ini untuk menentukan umur data. |
| `wind` | Arah dan kecepatan angin, gust jika ada, serta rentang arah variabel. |
| `visibility` | Nilai hasil parsing dan token laporan pada `repr`. Pertahankan `repr` untuk interpretasi sesuai satuan yang tercantum di laporan. |
| `clouds` | Lapisan awan. `base` dinyatakan dalam ratusan kaki AGL; misalnya `20` berarti 2.000 ft. |
| `temperature`, `dewpoint` | Suhu dan titik embun dalam °C. |
| `altimeter` | Nilai tekanan dari laporan. Untuk penggunaan operasional, baca bersama representasi mentah METAR. |
| `flight_rules` | Kategori penerbangan, misalnya `VFR`, `MVFR`, `IFR`, atau `LIFR`. |
| `wx_codes` | Kode fenomena cuaca beserta deskripsi jika tersedia. |
| `remarks` | Bagian remarks METAR jika ada. |
| `density_altitude`, `pressure_altitude` | Nilai perhitungan tambahan bila tersedia. |
| `relative_humidity` | Kelembapan relatif bila tersedia. |

Field yang tidak tersedia dapat bernilai `null`, kosong, atau tidak ada,
bergantung pada laporan dan hasil parsing. Simpan `raw` sebagai sumber utama
jika aplikasi perlu menginterpretasikan ulang laporan.

## Endpoint TAF

TAF adalah prakiraan cuaca untuk bandara dan area sekitarnya.

```http
GET https://data.skylinkapi.com/v3.1/weather/taf/{icao}
```

### Parameter

| Nama | Lokasi | Wajib | Tipe | Keterangan |
|---|---|---:|---|---|
| `icao` | Path | Ya | string | Kode ICAO stasiun, misalnya `WIII`. |
| `parsed` | Query | Tidak | boolean | Jika `true`, tambahkan rentang validitas dan grup prakiraan terurai. Default `false`. |

Contoh request TAF mentah (default):

```bash
curl "https://data.skylinkapi.com/v3.1/weather/taf/WIII" \
  -H "x-api-key: YOUR_API_KEY"
```

Contoh request dengan grup prakiraan terurai:

```bash
curl --get "https://data.skylinkapi.com/v3.1/weather/taf/WIII" \
  --data-urlencode "parsed=true" \
  -H "x-api-key: YOUR_API_KEY"
```

### Contoh response

Default endpoint mengembalikan laporan mentah. Ini juga bentuk TAF yang
disimpan script batch saat ini:

```json
{
  "raw": "TAF WIII 082300Z 0900/1006 27005KT 6000 FEW020",
  "icao": "WIII",
  "airport_name": "Soekarno-Hatta International Airport",
  "timestamp": "2026-10-09T03:05:00Z"
}
```

Dengan `parsed=true`, response juga menyertakan struktur seperti:

```json
{
  "raw": "TAF WIII 082300Z 0900/1006 27005KT 6000 FEW020",
  "icao": "WIII",
  "airport_name": "Soekarno-Hatta International Airport",
  "timestamp": "2026-10-09T03:05:00Z",
  "parsed": {
    "start_time": "2026-10-09T00:00:00+00:00",
    "end_time": "2026-10-10T06:00:00+00:00",
    "forecast": [
      {
        "type": "FROM",
        "start_time": "2026-10-09T00:00:00+00:00",
        "end_time": "2026-10-09T06:00:00+00:00",
        "wind": {
          "direction": 270,
          "speed": 5,
          "gust": null,
          "variable": []
        },
        "visibility": {
          "value": 6000,
          "repr": "6000"
        },
        "clouds": [
          {
            "type": "FEW",
            "base": 20,
            "repr": "FEW020"
          }
        ],
        "wx_codes": [],
        "flight_rules": "MVFR",
        "probability": null,
        "turbulence": [],
        "icing": []
      }
    ]
  }
}
```

`parsed.forecast` berisi grup prakiraan berurutan waktu. Tipe grup dapat
mencakup `FROM`, `TEMPO`, dan `BECMG`; tiap grup dapat memuat waktu, angin,
visibilitas, awan, fenomena cuaca, kategori penerbangan, probabilitas,
turbulensi, dan icing. Properti tertentu dapat `null` atau kosong.

TAF tidak selalu tersedia untuk setiap bandara. `404` pada endpoint TAF dapat
berarti stasiun tidak menerbitkan prakiraan; itu tidak selalu berarti kode
bandaranya tidak valid.

## Menemukan stasiun cuaca Indonesia

Data direktori bandara tidak sama dengan daftar stasiun yang aktif menerbitkan
cuaca. Mode batch memeriksa feed publik Aviation Weather Center (AWC) sebelum
meminta data SkyLink, supaya tidak melakukan request untuk setiap lapangan
terbang di direktori.

Discovery memakai dua endpoint AWC berikut:

```http
GET https://aviationweather.gov/api/data/metar?bbox=-11,95,6,141&format=json
GET https://aviationweather.gov/api/data/taf?bbox=-11,95,6,141&format=json
```

| Parameter | Tipe | Keterangan |
|---|---|---|
| `bbox` | string | Batas geografis Indonesia dalam urutan `lat_min,lon_min,lat_max,lon_max`. |
| `format` | string | `json`. |

Feed mengembalikan array laporan; mode batch menggunakan properti `icaoId`
untuk menemukan stasiun yang saat ini memiliki METAR atau TAF. Daftar produk
disimpan terpisah di
[indonesia_weather_stations.json](./examples/indonesia_weather_stations.json)
dan diperbarui pada setiap batch run. Feed ini hanya untuk discovery; payload
weather yang disimpan berasal dari SkyLink API.

AWC mendokumentasikan maksimum 100 request per menit. Script batch juga
menerapkan jeda 1,2 detik antara request SkyLink.

## Menjalankan contoh dan menyimpan JSON

Ambil METAR dan TAF untuk satu bandara:

```bash
python3 examples/weather_briefing.py
python3 examples/weather_briefing.py --icao WIII
```

Tanpa argumen tambahan, kode default adalah `WIII`. Hasil disimpan ke
`output/weather_WIII.json`. Script membuat folder `output/` jika belum ada.
Tentukan kode dan nama file sendiri:

```bash
python3 examples/weather_briefing.py --icao WAAA --output output/makassar.json
```

Ambil data dari stasiun Indonesia yang sedang memiliki laporan:

```bash
python3 examples/weather_briefing.py --indonesia
```

Hasil batch disimpan ke `output/weather_indonesia.json`. Batch menyimpan
progress setelah setiap stasiun. Tiap entri hanya memiliki properti `metar`
dan/atau `taf` jika feed discovery menemukan produk itu untuk stasiun tersebut.

Untuk memperbarui direktori bandara OurAirports
[indonesia_airports.json](./examples/indonesia_airports.json) (bukan daftar
stasiun laporan cuaca aktif):

```bash
python3 examples/weather_briefing.py --refresh-airport-list
```

## Format file hasil batch

Output `output/weather_indonesia.json` berupa array. Contoh berikut meringkas
field penting; response aktual menyertakan seluruh field dari endpoint:

```json
[
  {
    "icao": "WAAA",
    "metar": {
      "raw": "METAR WAAA 090230Z 23004KT 5000 HZ FEW020 32/20 Q1012 NOSIG",
      "icao": "WAAA",
      "airport_name": "Sultan Hasanuddin International Airport",
      "timestamp": "2026-10-09T02:40:20Z",
      "parsed": {
        "wind": {
          "direction": 230,
          "speed": 4,
          "gust": null,
          "variable": []
        },
        "visibility": {
          "value": 5000,
          "repr": "5000"
        },
        "clouds": [
          {
            "type": "FEW",
            "base": 20,
            "repr": "FEW020"
          }
        ],
        "temperature": 32,
        "dewpoint": 20,
        "altimeter": 1012,
        "flight_rules": "MVFR"
      }
    },
    "taf": {
      "raw": "TAF WAAA 082300Z 0900/1006 14004KT 8000 FEW020",
      "icao": "WAAA",
      "airport_name": "Sultan Hasanuddin International Airport",
      "timestamp": "2026-10-09T02:40:22Z"
    }
  }
]
```

Satu objek output mengikuti pola:

```json
{
  "icao": "CODE",
  "metar": {},
  "taf": {}
}
```

Jika hanya satu produk yang tersedia, properti produk lainnya tidak
disertakan. Jika produk terdeteksi saat discovery tetapi kemudian SkyLink
mengembalikan `404`, produk tersebut disimpan sebagai objek berisi `error`.

## Error dan penanganannya

| HTTP status | Makna umum | Tindakan |
|---:|---|---|
| `401` | API key tidak ada atau tidak valid. | Periksa konfigurasi `SKYLINK_API_KEY`; jangan retry otomatis. |
| `403` | Produk tidak termasuk dalam paket. | Periksa akses paket. |
| `404` | Stasiun atau produk cuaca tidak tersedia. | Periksa ICAO dan ketersediaan METAR/TAF; TAF sering tidak diterbitkan di bandara kecil. |
| `422` | Parameter atau format request tidak valid. | Perbaiki parameter; jangan retry request yang sama. |
| `429` | Rate limit atau kuota tercapai. | Tunggu/backoff, lalu periksa rate limit dan kuota paket. |
| `500`, `502`, `504` | Gangguan sementara di server atau sumber data. | Retry terbatas dengan exponential backoff. |

Script Python menampilkan body response jika SkyLink mengembalikan HTTP error.
Respons sukses dapat berbeda field berdasarkan ketersediaan data; client
sebaiknya menangani nilai opsional dan mempertahankan `raw`.

## Referensi

- [SkyLink v3.1 Weather API](https://skylinkapi.com/docs/v31/weather/)
- [Referensi METAR](https://skylinkapi.com/docs/v31/weather-metar/)
- [Referensi TAF](https://skylinkapi.com/docs/v31/weather-taf/)
- [SkyLink rate limits](https://skylinkapi.com/docs/rate-limits/)
- [AWC API](https://aviationweather.gov/data/api/)
