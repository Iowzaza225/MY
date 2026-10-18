#!/usr/bin/env python3
"""Stage TEAMMOD27's strictly sandbox-scoped file diagnostics and catalog UI.

Runs AFTER ci/brand_teammod27.py, on generated build sources only.
The diagnostic never calls AFC, never touches pairing credentials and never
accesses another app's sandbox. It uses a throwaway per-run folder in the
current app's Application Support; the entire folder is removed on return.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
views = root / "ThreeOneOSFive" / "views"
preflight = views / "RuizenApplyPreflightView.swift"
home = views / "RepositoryHomeView.swift"
assert preflight.is_file() and home.is_file(), "Expected view files are missing"

preflight_source = preflight.read_text(encoding="utf-8")
state_marker = "    @State private var pairingImportError: String?"
assert preflight_source.count(state_marker) == 1
preflight_source = preflight_source.replace(
    state_marker,
    state_marker + '\n    @State private var fileSandboxCheckResult = "ยังไม่ได้ทดสอบ"',
    1
)

preflight_marker = """                    Text(report.explanation)
                        .font(.subheadline)"""
assert preflight_source.count(preflight_marker) == 1, "Preflight diagnostic insertion point changed"
preflight_widget = """                    VStack(alignment: .leading, spacing: 10) {
                        HStack(spacing: 8) {
                            Image(systemName: "checkmark.shield")
                                .foregroundStyle(AppTheme.accent)
                            Text("ทดสอบสิทธิ์ไฟล์ของ TEAMMOD27")
                                .font(.headline).foregroundStyle(.white)
                        }
                        Text("ทดสอบสร้าง อ่าน สำรอง แก้ไข และคืนค่าไฟล์ชั่วคราว เฉพาะใน Application Support ของแอปนี้เท่านั้น ไม่ยุ่งกับไฟล์เกมหรือ Pairing")
                            .font(.caption).foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                        Button {
                            fileSandboxCheckResult = TeammodSandboxFileCheck.run()
                        } label: {
                            Label("ทดสอบอ่าน–เขียน–สำรอง–คืนค่า", systemImage: "doc.badge.gearshape")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.bordered)
                        .tint(AppTheme.accent)
                        Text(fileSandboxCheckResult)
                            .font(.caption)
                            .foregroundStyle(fileSandboxCheckResult.hasPrefix("ผ่าน") ? Color.green : Color.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                            .textSelection(.enabled)
                    }
                    .padding(16)
                    .background(AppTheme.surfaceRaised, in: RoundedRectangle(cornerRadius: 18))

"""
preflight_source = preflight_source.replace(preflight_marker, preflight_widget + preflight_marker, 1)

helper = """
// Tests ONLY the current app's writable container. No AFC, no privileged paths,
// no pairing-file reads, and no network or third-party app data access.
private enum TeammodSandboxFileCheck {
    static func run() -> String {
        let manager = FileManager.default
        guard let support = manager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first else {
            return "ไม่ผ่าน: ไม่พบพื้นที่ Application Support ของแอป"
        }
        let unique = support
            .appendingPathComponent("TEAMMOD27-SandboxChecks", isDirectory: true)
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        do {
            try manager.createDirectory(at: unique, withIntermediateDirectories: true)
            defer { try? manager.removeItem(at: unique) }

            let original = unique.appendingPathComponent("sample.txt")
            let backup = unique.appendingPathComponent("sample.backup")
            let expected = Data("TEAMMOD27 safe file check".utf8)
            let changed = Data("TEAMMOD27 replaced test content".utf8)

            try expected.write(to: original, options: .atomic)
            guard try Data(contentsOf: original) == expected else {
                return "ไม่ผ่าน: อ่านข้อมูลหลังเขียนไม่ตรงกัน"
            }
            try manager.copyItem(at: original, to: backup)
            guard try Data(contentsOf: backup) == expected else {
                return "ไม่ผ่าน: ไฟล์สำรองไม่ตรงกับต้นฉบับ"
            }
            try changed.write(to: original, options: .atomic)
            guard try Data(contentsOf: original) == changed else {
                return "ไม่ผ่าน: ทดสอบแก้ไขไฟล์ไม่สำเร็จ"
            }
            try manager.removeItem(at: original)
            try manager.copyItem(at: backup, to: original)
            guard try Data(contentsOf: original) == expected else {
                return "ไม่ผ่าน: คืนค่าไฟล์จากสำรองไม่สำเร็จ"
            }
            return "ผ่านครบ 5 ขั้นตอน: สร้าง ✓ อ่าน ✓ สำรอง ✓ แก้ไข ✓ คืนค่า ✓ (พื้นที่แอปเท่านั้น)"
        } catch {
            return "ไม่ผ่าน: " + error.localizedDescription
        }
    }
}
"""
assert "enum TeammodSandboxFileCheck" not in preflight_source
preflight_source += helper
preflight.write_text(preflight_source, encoding="utf-8")

home_source = home.read_text(encoding="utf-8")
# Show the difference between 'empty catalog' and 'network/license failure'.
# Existing pull-to-refresh is preserved and a discoverable retry button added.
home_marker = """            .htvCard(padding: 14)
        }
    }

    private func overviewMetric("""
assert home_source.count(home_marker) == 1, "Overview structure changed"
home_widget = """            .htvCard(padding: 14)
            if totalPatchCount == 0 && !serverCatalog.isLoading {
                VStack(alignment: .leading, spacing: 10) {
                    Label("สถานะรายการไฟล์จาก HIGHT API", systemImage: "server.rack")
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(AppTheme.accent)
                    if let message = serverCatalog.errorMessage {
                        Text("ไม่สามารถโหลดแคตตาล็อก: " + message)
                            .font(.caption).foregroundStyle(.orange)
                    } else {
                        Text("เซิร์ฟเวอร์ตอบกลับ แต่ยังไม่มีไฟล์ที่เปิดใช้งานในแคตตาล็อก ตรวจรายการไฟล์และเกมที่กำหนดในแผง HIGHT API")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Text("License App ID: teammod27 • รายการไฟล์ 0 ยังไม่ใช่ปัญหา Tunnel")
                        .font(.caption2).foregroundStyle(.secondary)
                    Button {
                        Task { await refreshServer() }
                    } label: {
                        Label("รีเฟรชรายการไฟล์", systemImage: "arrow.clockwise")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                    .tint(AppTheme.accent)
                }
                .htvCard()
            }
        }
    }

    private func overviewMetric("""
home_source = home_source.replace(home_marker, home_widget, 1)
home.write_text(home_source, encoding="utf-8")

assert "TeammodSandboxFileCheck.run()" in preflight.read_text()
assert "License App ID: teammod27" in home.read_text()
print("Staged sandbox-only five-step file test and authenticated catalog status UI.")
