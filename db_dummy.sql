INSERT INTO roles
VALUES 
("RL0001", "Customer Service"),
("RL0002", "Supervisor"),
("RL0003", "IT Support"),
("RL0004", "Auditor"),
("RL0005", "Branch Manager");

INSERT INTO workstations
VALUES
("WS0001", "PC0001", "RP0001", "CS Desk 1", 1),
("WS0002", "PC0002", "RP0002", "CS Desk 2", 0),
("WS0003", "PC0003", "RP0003", "CS Desk 3", 0),
("WS0004", "PC0004", "RP0004", "CS Desk 4", 0),
("WS0005", "PC0005", "RP0005", "CS Desk 5", 0);

INSERT INTO sop_services
VALUES
("SV0001", "Penggantian Kartu ATM"),
("SV0002", "Pembukaan Rekening Tahapan"),
("SV0003", "Pendaftaran m-BCA");

INSERT INTO users
VALUES
("US0001", "RL0001", "Budi Tabuti", "buditabuti@example.com", "2020-12-22 13:00:00", "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S", NULL, 1, "2020-12-22 13:00:00", "2020-12-22 13:00:00"),
("US0002", "RL0001", "Dedi Pratama", "dedipratama@example.com", "2020-12-23 14:00:00", "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S", NULL, 0, "2020-12-23 14:00:00", "2020-12-23 14:00:00"),
("US0003", "RL0001", "Agus Saputra", "agussaputra@example.com", "2020-12-25 10:00:00", "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S", NULL, 0, "2025-12-23 10:00:00", "2025-12-23 10:00:00"),
("US0004", "RL0001", "Riko Hartono", "rikohartono@example.com", "2020-12-30 11:00:00", "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S", NULL, 0, "2020-12-30 11:00:00", "2020-12-30 11:00:00"),
("US0005", "RL0001", "Andi Wijaya", "andiwijaya@example.com", "2021-12-20 15:00:00", "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S", NULL, 0, "2021-12-20 15:00:00", "2021-12-20 15:00:00");

INSERT INTO sop_steps
VALUES
("ST0001", "SV0001", 1, "Penerimaan Dokumen: Menerima KTP asli dan kartu ATM yang rusak dari nasabah."),
("ST0002", "SV0001", 2, "Input Data Penggantian: Masuk ke menu Kartu > Penggantian Kartu."),
("ST0003", "SV0001", 3, "Data Kartu: Input nomor rekening dan nomor kartu lama. Pilih jenis dan tipe lartu baru. Kemudian, pilih alasan rusak. Dan Input nomor kartu baru (diambil dari stok kartu)."),
("ST0004", "SV0001", 4, "Verifikasi PIN Nasabah: Pilih sarana verifikasi PIN, lalu minta nasabah memasukkan PIN lama pada PINPad."),
("ST0005", "SV0001", 5, "Otorisasi: Meminta override dari Pejabat/Supervisor."),
("ST0006", "SV0001", 6, "Cetak Form: Klik [Cetak] untuk mencetak Form Penggantian Kartu ATM."),
("ST0007", "SV0001", 7, "Finalisasi Ganti Kartu: Klik [GANTI] dan cetak validasi pada Form Belakang Atas."),
("ST0008", "SV0001", 8, "Aktivasi PIN Baru: Masuk ke menu Kartu > Aktivasi PIN dan cetak validasi pada Form Belakang Bawah."),
("ST0009", "SV0001", 9, "Validasi Tanda Tangan: Meminta tanda tangan nasabah pada form dan melakukan verifikasi kecocokan tanda tangan (Tancok)."),
("ST0010", "SV0001", 10, "Edukasi Biaya: Menginformasikan kepada nasabah bahwa biaya penggantian kartu akan didebet otomatis dari saldo rekening."),
("ST0011", "SV0001", 11, "Pengembalian: Menyerahkan kembali KTP dan kartu lama (yang sudah digunting/rusak) kepada nasabah."),
("ST0012", "SV0002", 1, "Verifikasi Niat: Menanyakan tujuan pembukaan rekening (Transaksi)."),
("ST0013", "SV0002", 2, "Edukasi Kartu: Menjelaskan perbedaan Paspor Mastercard vs GPN."),
("ST0014", "SV0002", 3, "Pilihan Kartu: Mengonfirmasi pilihan kartu."),
("ST0015", "SV0002", 4, "Validasi Dokumen: Meminta KTP asli (SIM tidak diperbolehkan)."),
("ST0016", "SV0002", 5, "Setoran Awal: Mengonfirmasi setoran awal sebesar Rp 500.000."),
("ST0017", "SV0002", 6, "Pembuatan CIS: Mengisi data identitas (Nama, Alamat, RT/RW, hingga Kode Pos)."),
("ST0018", "SV0002", 7, "Data Kontak: Menginput Nomor HP 1, HP 2, dan Alamat E-mail (Wajib)."),
("ST0019", "SV0002", 8, "Profil Nasabah: Mengisi data pekerjaan, Penghasilan, dan Nama Gadis Ibu Kandung."),
("ST0020", "SV0002", 9, "Pengambilan Kartu: Mengambil kartu dari box dan input nomor kartu ke sistem."),
("ST0021", "SV0002", 10, "Pencetakan Form: Mencetak formulir pembukaan rekening dan meminta tanda tangan nasabah."),
("ST0022", "SV0002", 11, "Aktivasi PIN: Meminta nasabah input PIN dua kali pada PINPad."),
("ST0023", "SV0002", 12, "Setoran Tunai: Memproses setoran awal Rp 500.000 dan validasi bukti setoran."),
("ST0024", "SV0002", 13, "Cetak Buku: Mencetak Kepala Buku dan baris saldo pertama."),
("ST0025", "SV0002", 14, "Registrasi m-BCA: Mendaftarkan nomor HP dan nomor kartu ATM ke sistem."),
("ST0026", "SV0002", 15, "Aktivasi Finansial m-BCA: Melakukan aktivasi fitur finansial via PINPad/EDC."),
("ST0027", "SV0002", 16, "Persetujuan Pejabat: Meminta tanda tangan pejabat pada form dan buku."),
("ST0028", "SV0002", 17, "Penyerahan Dokumen: Menyerahkan Buku Tabungan, Kartu ATM, dan KTP. "),
("ST0029", "SV0002", 18, "Edukasi Pasca-Layanan: Menginfokan kartu baru bisa digunakan hari ini."),
("ST0030", "SV0003", 1, "Input Data Kartu: Masuk ke menu m-BCA > Registrasi m-BCA dan ketik nomor kartu ATM yang baru diaktivasi."),
("ST0031", "SV0003", 2, "Verifikasi Nama: Klik [Cari] dan pastikan nama nasabah yang muncul sudah sesuai."),
("ST0032", "SV0003", 3, "Input Nomor HP: Memasukkan nomor handphone aktif nasabah (pastikan diawali kode negara jika sistem meminta)."),
("ST0033", "SV0003", 4, "Eksekusi Registrasi: Klik [Registrasi] untuk mendaftarkan layanan."),
("ST0034", "SV0003", 5, "Otorisasi (Override): Meminta override atau persetujuan dari Pejabat/Supervisor."),
("ST0035", "SV0003", 6, 'Konfirmasi Berhasil: Memastikan muncul notifikasi "Registrasi m-BCA berhasil dilakukan".'),
("ST0036", "SV0003", 7, "Validasi Cetak: Klik [OK] dan cetak validasi pada Form Pemrek Halaman Belakang (Samping Kanan Atas).");

INSERT INTO service_records
VALUES
("SR0001", "WS0001", "US0001", "Pendaftaran m-BCA", 0.73, "2025-12-22 13:00:00", "2025-12-22 13:03:15", 195, "baik bu saya mulai bantu untuk proses pendaftaran mbca boleh dibantu ibu untuk nomor handphonenya berapa baik terima kasih ibu saya lanjut ya untuk proses selanjutnya baik ibu untuk proses pendaftaran mbcanya sudah selesai", 1, NULL, "local/aud/SR0001");

INSERT INTO service_checklists
VALUES
("CE0001", "SR0001", "ST0030", 1, "2025-12-22 13:00:25"),
("CE0002", "SR0001", "ST0031", 1, "2025-12-22 13:00:40"),
("CE0003", "SR0001", "ST0032", 1, "2025-12-22 13:01:20"),
("CE0004", "SR0001", "ST0033", 1, "2025-12-22 13:01:30"),
("CE0005", "SR0001", "ST0034", 1, "2025-12-22 13:02:30"),
("CE0006", "SR0001", "ST0035", 1, "2025-12-22 13:02:45"),
("CE0007", "SR0001", "ST0036", 1, "2025-12-22 13:03:00");