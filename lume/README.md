# Lumé-
Tugas Kelompok PBP F - F02
- Naomyscha Attalie Maza
- Nisrina Fatimah
- Juma Jordan Bimo Simanjuntak
- Raqilla Al-abrar
- Ahmad Keenan Aryasatya Gamal

Deskripsi aplikasi
Lumé adalah sebuah aplikasi berbasis web yang menggabungkan pengalaman wellness dan commerce dalam satu platform. Terinspirasi dari gaya hidup sehat dan keseimbangan modern, Lumé dirancang sebagai studio pilates digital tempat pengguna dapat memesan kelas pilates dan membeli produk-produk pendukung gaya hidup sehat, seperti matras, botol minum, activewear, dan aksesoris pilates lainnya.
Aplikasi ini memiliki sistem yang fleksibel—pengguna tidak diwajibkan untuk login. Tanpa login pun, pengguna dapat langsung menjelajahi produk, menambahkannya ke keranjang, dan melakukan pembelian. Saat checkout, pengguna hanya perlu mengisi data dasar seperti nama dan nomor telepon, lalu memilih metode pengambilan:
- Ambil di studio: pengguna akan mendapatkan kode unik (pickup ID) untuk ditunjukkan saat pengambilan.
- Kirim ke alamat: sistem otomatis menampilkan estimasi ongkir, dan pengguna diminta mengisi nama, nomor telepon, serta alamat pengiriman.

Namun, pengguna yang membuat akun (login) akan mendapatkan pengalaman yang lebih personal:
- Akses ke keranjang yang tersimpan secara permanen, sehingga mereka bisa melanjutkan belanja kapan pun.
- Diskon membership 15% untuk transaksi pertama.
- Fitur penyimpanan alamat dan kontak otomatis, seperti platform e-commerce besar pada umumnya.

(Rencana pengembangan ke depan) Pemesan kelas pilates langsung dari studio, termasuk pilihan jadwal, instruktur, dan notifikasi pengingat.
Dengan pendekatan ini, Lumé tidak hanya berfungsi sebagai tempat jual beli produk kesehatan, tetapi juga menjadi ekosistem gaya hidup sehat yang terintegrasi, mendukung pengguna dalam membangun rutinitas mindful dan seimbang. Ke depannya, Lumé dapat berkembang menjadi platform komunitas pilates yang menawarkan jadwal kelas, tracking progress, hingga fitur loyalty bagi pelanggan tetap.

Daftar modul yang akan diimplementasikan
- Catalog : Menampung data produk fisik (kategori, brand, produk, gambar). Menyediakan listing, detail, dan API filter/sort.
- Cart : Menampung produk-produk yang disimpan jika ingin dibeli.
- Checkout : Mengelola kalkulasi akhir (subtotal, diskon, ongkir).
- Booking : Kelas pilates terpisah dari katalog, erdapat tipe kelas dan jadwal yang berbeda. Flow booking berdiri sendiri dan akan dihubungkan ke checkout.
- User: Auth (login/register), alamat, lalu expose data profil/alamat untuk prefilling checkout.
- Admin: Panel staff untuk CRUD produk dan memproses pesanan.

Sumber initial dataset kategori utama produk
Dataset didapatkan dari hasil scraping data dari www.merrithew.com dengan search pilates, https://www.pilates.com, align-pilates.com, staminaproducts.com, gratzpilates.com, decathlon.co.uk, decathlon.ca, decathlon.my, walmart.com, gaiam.com, dan ebay.com. Dataset yang digunakan berisikan beberapa variabel:
- brand: merk atau manufaktur resmi produk
- product_name: nama produk yang tampil ke user
- category: kategori produk (midal mat, pilates ring, reformer, accessoty) untuk filter dan navigasi
- variant: varian atau atribut pembeda dalam satu produk
- key_specs: ringkasan fitur atau atribut
- decription: kalau ingin markup terstruktur
- source_url: URL halaman sumber tempat data diambil
- image_url: URL gambar atau halaman yang menampilkan gambar utama produk
- marketplace: tipe situs asal data

Role atau peran pengguna beserta deskripsinya
Pengunjung (Guest User)
- Dapat menjelajahi produk tanpa loginDapat menambahkan produk ke keranjang sementara (tidak tersimpan)
- Dapat melakukan pembelian dengan mengisi data nama & kontak saat checkout
- Bisa memilih pengambilan produk di studio atau pengiriman ke alamat

Pengguna Terdaftar (Member)
- Login untuk mengakses keranjang pribadi yang tersimpan
- Mendapat diskon 15% membership pada  transaksi pertama
- Dapat menyimpan data pribadi (nama, nomor telepon, alamat)
- (Future) Bisa memesan kelas pilates langsung melalui akun

Admin (Studio Owner / Staff)
- Mengelola produk (CRUD product)
- Melihat dan memproses pesanan
- Mengatur status pesanan (paid, shipped, picked up)
- (Future) Mengatur jadwal kelas dan instruktur

Link PWS : https://juma-jordan-lume.pbp.cs.ui.ac.id/
Link figma : https://www.figma.com/files/team/1510143807974722636/project/465240058/Lum%C3%A9?fuid=1510143805779277091 
