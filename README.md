# Lumé-
Tugas Kelompok PBP F - F02
- Naomyscha Attalie Maza
- Nisrina Fatimah
- Juma Jordan Bimo Simanjuntak
- Raqilla Al-abrar
- Ahmad Keenan Aryasatya Gamal

Deskripsi aplikasi
Lumé adalah aplikasi web yang menggabungkan pengalaman wellness dan commerce dalam satu platform. Terinspirasi dari gaya hidup sehat dan keseimbangan modern, Lumé hadir sebagai studio pilates digital yang memungkinkan pengguna untuk memesan kelas pilates dan membeli produk-produk pendukung gaya hidup sehat seperti matras, botol minum, activewear, hingga aksesoris pilates lainnya.
Aplikasi ini menerapkan sistem berbasis akun:
    - Pengguna harus login terlebih dahulu untuk dapat memanfaatkan fitur keranjang (cart), checkout, dan booking kelas.
    - Jika belum login, pengguna tetap dapat menjelajahi katalog produk dan kelas, namun ketika menekan tombol cart, add to cart atau Book Class, mereka akan diarahkan ke halaman login terlebih dahulu.

Proses registrasi dibuat sederhana, hanya memerlukan username, password, dan nomor telepon.
Saat melakukan checkout, pengguna akan diminta untuk mengisi alamat pengiriman dan memilih metode pembayaran, yang saat ini tersedia hanya:
    - Cash on Delivery (COD) dengan biaya pengiriman tetap sebesar Rp10.000 per transaksi.

Selain pembelian produk, pengguna juga dapat melakukan pemesanan kelas pilates, yang terbagi menjadi dua jenis:
    - Weekly Class: jadwal latihan rutin setiap minggu.
    - Daily Class: jadwal harian yang bisa langsung dipilih dan dibayar di lokasi (cash on delivery on-site).

Dengan pendekatan ini, Lumé tidak hanya berfungsi sebagai platform jual-beli produk kesehatan, tetapi juga sebagai ekosistem gaya hidup sehat yang terintegrasi—menghubungkan pengguna dengan aktivitas fisik, peralatan pendukung, dan komunitas mindful yang seimbang.

Daftar modul yang akan diimplementasikan
User & Admin : 
- Login, register, dan profile management (melihat dan mengedit profil, melihat riwayat transaksi/booking).
- Admin memiliki akses ke dashboard yang menampilkan statistik seperti total user, total pendapatan, total pesanan, dan total booking.

Catalog : 
- Menampilkan daftar produk beserta detail, kategori, harga, dan spesifikasi.
- Mendukung fitur pencarian dan filter kategori.

Cart : 
- Menampung produk yang dipilih pengguna untuk dibeli.
- Setelah checkout, produk dihapus dari cart dan stok otomatis berkurang.

Checkout : 
- Mengelola kalkulasi akhir total harga, ongkos kirim, dan metode pembayaran.
- Meminta input alamat pengguna dan menghasilkan ID transaksi yang akan tercatat di profil.

Booking : 
- Mengelola kelas pilates (daily dan weekly), termasuk jadwal, kapasitas, dan instruktur.
- Pengguna dapat memesan kelas dan melakukan pembayaran langsung di tempat.


Sumber initial dataset kategori utama produk
Data awal dikumpulkan dari beberapa situs e-commerce dan brand kesehatan ternama, antara lain:
stanley.com, corkcicle.com, hydroflask.com, owala.com, lululemon.com, alo.com, gymshark.com, vuori.com, underarmour.com, nike.com, betterme.com, dan adidas.com.


Variabel yang digunakan dalam dataset meliputi:
- brand : merek produk
- product_name : nama produk yang ditampilkan ke pengguna
- category : kategori produk (mat, botol, activewear, dsb.)
- variant : perbedaan versi produk dalam satu kategori
- key_specs : fitur utama atau spesifikasi singkat
- image_url : URL gambar utama produk
- marketplace : situs asal data
- price : harga produk


Role atau peran pengguna beserta deskripsinya
User(Pengguna)
- Dapat melihat detail produk dan kelas tanpa login.
- Setelah login, dapat:
    - Menambahkan produk ke keranjang
    - Melakukan checkout dan pembayaran COD
    - Melihat riwayat transaksi dan booking di halaman profil
    - Memesan kelas pilates (weekly atau daily)

Admin 
- Dapat melakukan CRUD pada produk (tambah, edit, hapus)
- Dapat melakukan CRUD pada kelas pilates (tambah, edit, hapus jadwal)
- Memiliki akses ke Admin Dashboard untuk melihat:
    - Total pengguna, pendapatan, pesanan, dan booking
    - Mengatur status pesanan (paid, shipped, picked up)

Link PWS : https://juma-jordan-lume.pbp.cs.ui.ac.id/
Link figma : https://www.figma.com/design/osIH3CEyPlh5W9PMRyY8Hz/Lum%C3%A9?node-id=0-1&t=QfRKmdLKiJh1yp1W-1 
