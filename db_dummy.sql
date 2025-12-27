-- =========================
-- ROLES
-- =========================
INSERT INTO roles (role_id, role_name) VALUES
("RL0001", "Customer Service"),
("RL0002", "Supervisor"),
("RL0003", "IT Support"),
("RL0004", "Auditor"), 
("RL0005", "Branch Manager");

-- =========================
-- WORKSTATIONS
-- =========================
INSERT INTO workstations (
    workstation_id, pc_id, rpi_id, location, is_active
) VALUES
("WS0001", "PC0001", "RP0001", "CS Desk 1", 1),
("WS0002", "PC0002", "RP0002", "CS Desk 2", 0),
("WS0003", "PC0003", "RP0003", "CS Desk 3", 0),
("WS0004", "PC0004", "RP0004", "CS Desk 4", 0),
("WS0005", "PC0005", "RP0005", "CS Desk 5", 0);

-- =========================
-- SOP SERVICES
-- =========================
INSERT INTO sop_services (service_id, service_name) VALUES
("SV0001", "Penggantian Kartu ATM"),
("SV0002", "Pembukaan Rekening Tahapan"),
("SV0003", "Pendaftaran m-BCA");

-- =========================
-- USERS (FIXED)
-- =========================
INSERT INTO users (
    user_id,
    role_id,
    name,
    email,
    password,
    is_active,
    created_at,
    updated_at
) VALUES
("US0001", "RL0001", "Budi Tabuti", "buditabuti@example.com",
 "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S",
 1, "2020-12-22 13:00:00", "2020-12-22 13:00:00"),

("US0002", "RL0001", "Dedi Pratama", "dedipratama@example.com",
 "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S",
 0, "2020-12-23 14:00:00", "2020-12-23 14:00:00"),

("US0003", "RL0001", "Agus Saputra", "agussaputra@example.com",
 "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S",
 0, "2025-12-23 10:00:00", "2025-12-23 10:00:00"),

("US0004", "RL0001", "Riko Hartono", "rikohartono@example.com",
 "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S",
 0, "2020-12-30 11:00:00", "2020-12-30 11:00:00"),

("US0005", "RL0001", "Andi Wijaya", "andiwijaya@example.com",
 "$2y$10$wH8kZ9N6X4FQqYy6G3U1Ue4K5A2mJYk8Zk1zZr1Xx2y9Zp0yH6l6S",
 0, "2021-12-20 15:00:00", "2021-12-20 15:00:00");

-- =========================
-- SOP STEPS
-- =========================
INSERT INTO sop_steps (
    step_id, service_id, step_number, step_description
) VALUES
("ST0001", "SV0001", 1, "Penerimaan Dokumen: Menerima KTP asli dan kartu ATM yang rusak dari nasabah."),
("ST0002", "SV0001", 2, "Input Data Penggantian: Masuk ke menu Kartu > Penggantian Kartu."),
("ST0003", "SV0001", 3, "Data Kartu: Input nomor rekening dan nomor kartu lama."),
("ST0004", "SV0001", 4, "Verifikasi PIN Nasabah."),
("ST0005", "SV0001", 5, "Otorisasi Supervisor."),
("ST0006", "SV0001", 6, "Cetak Form Penggantian."),
("ST0007", "SV0001", 7, "Finalisasi Ganti Kartu."),
("ST0008", "SV0001", 8, "Aktivasi PIN Baru."),
("ST0009", "SV0001", 9, "Validasi Tanda Tangan."),
("ST0010", "SV0001", 10, "Edukasi Biaya."),
("ST0011", "SV0001", 11, "Pengembalian Dokumen."),

("ST0012", "SV0002", 1, "Verifikasi Niat Pembukaan Rekening."),
("ST0013", "SV0002", 2, "Edukasi Kartu."),
("ST0014", "SV0002", 3, "Konfirmasi Pilihan Kartu."),
("ST0015", "SV0002", 4, "Validasi Dokumen."),
("ST0016", "SV0002", 5, "Konfirmasi Setoran Awal."),
("ST0017", "SV0002", 6, "Pembuatan CIS."),
("ST0018", "SV0002", 7, "Input Data Kontak."),
("ST0019", "SV0002", 8, "Input Profil Nasabah."),
("ST0020", "SV0002", 9, "Pengambilan Kartu."),
("ST0021", "SV0002", 10, "Cetak Formulir."),
("ST0022", "SV0002", 11, "Aktivasi PIN."),
("ST0023", "SV0002", 12, "Setoran Tunai."),
("ST0024", "SV0002", 13, "Cetak Buku."),
("ST0025", "SV0002", 14, "Registrasi m-BCA."),
("ST0026", "SV0002", 15, "Aktivasi Finansial."),
("ST0027", "SV0002", 16, "Persetujuan Pejabat."),
("ST0028", "SV0002", 17, "Penyerahan Dokumen."),
("ST0029", "SV0002", 18, "Edukasi Pasca-Layanan."),

("ST0030", "SV0003", 1, "Input Data Kartu."),
("ST0031", "SV0003", 2, "Verifikasi Nama."),
("ST0032", "SV0003", 3, "Input Nomor HP."),
("ST0033", "SV0003", 4, "Eksekusi Registrasi."),
("ST0034", "SV0003", 5, "Otorisasi Supervisor."),
("ST0035", "SV0003", 6, "Konfirmasi Registrasi Berhasil."),
("ST0036", "SV0003", 7, "Validasi Cetak.");

-- =========================
-- SERVICE RECORD
-- =========================
INSERT INTO service_records (
    service_record_id,
    workstation_id,
    user_id,
    service_id,
    service_detected,
    confidence,
    start_time,
    end_time,
    duration,
    text,
    is_normal_flow,
    reason,
    audio_path
) VALUES (
    "SR0001",
    "WS0001",
    "US0001",
    "SV0003",
    "Pendaftaran m-BCA",
    0.73,
    "2025-12-22 13:00:00",
    "2025-12-22 13:03:15",
    195,
    "baik bu saya mulai bantu...",
    1,
    NULL,
    "local/aud/SR0001"
);

-- =========================
-- SERVICE CHECKLISTS
-- =========================
INSERT INTO service_checklists (
    checklist_id,
    service_record_id,
    step_id,
    is_checked,
    checked_at
) VALUES
("CE0001", "SR0001", "ST0030", 1, "2025-12-22 13:00:25"),
("CE0002", "SR0001", "ST0031", 1, "2025-12-22 13:00:40"),
("CE0003", "SR0001", "ST0032", 1, "2025-12-22 13:01:20"),
("CE0004", "SR0001", "ST0033", 1, "2025-12-22 13:01:30"),
("CE0005", "SR0001", "ST0034", 1, "2025-12-22 13:02:30"),
("CE0006", "SR0001", "ST0035", 1, "2025-12-22 13:02:45"),
("CE0007", "SR0001", "ST0036", 1, "2025-12-22 13:03:00");
