#!/usr/bin/env python3
"""Add a READ-ONLY target-access audit to TEAMMOD27's real patch preflight.

This does not attempt a sandbox escape, alter target files, obtain privileged
tokens, or claim that an RSD connection grants patch write permission.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1]).resolve()
view=root/"ThreeOneOSFive/views/RuizenApplyPreflightView.swift"
projects=root/"ThreeOneOSFive/views/PatchProjectsView.swift"
assert view.is_file() and projects.is_file(), "Expected TEAMMOD27 Swift sources missing"

s=view.read_text(encoding="utf8")
needle="""    let onApply: () -> Void

    @Environment"""
assert s.count(needle)==1, "Preflight initializer anchor has changed"
replace="""    let onApply: () -> Void
    let patchProject: PatchProject?

    init(packageName: String?, readiness: RuizenDeviceReadiness,
         patchProject: PatchProject? = nil, onApply: @escaping () -> Void) {
        self.packageName = packageName
        self.readiness = readiness
        self.patchProject = patchProject
        self.onApply = onApply
    }

    @Environment"""
s=s.replace(needle,replace,1)
state="""    @State private var fileSandboxCheckResult = "ยังไม่ได้ทดสอบ" """
assert state.strip() in s
s=s.replace(state.strip(),state.strip() + '\n    @State private var targetCheckResult = "ยังไม่ได้ตรวจปลายทางแพตช์"',1)

needle2="""                    Text(report.explanation)
                        .font(.subheadline)"""
assert s.count(needle2)==1, "Preflight insert location changed"
ui="""                    if packageName != nil {
                        VStack(alignment: .leading, spacing: 10) {
                            Label("ตรวจสิทธิ์ปลายทางของแพตช์ (ไม่เขียนไฟล์)", systemImage: "doc.text.magnifyingglass")
                                .font(.headline).foregroundStyle(.white)
                            Text("ตรวจชื่อแอปเป้าหมาย เส้นทางในแพ็กเกจ การเข้าถึง Container และการอ่านข้อมูลพื้นฐาน ไม่แก้ไขไฟล์เกมและไม่ข้าม Sandbox")
                                .font(.caption).foregroundStyle(.secondary)
                                .fixedSize(horizontal: false, vertical: true)
                            if let patchProject {
                                Button {
                                    targetCheckResult = PatchTargetAccessAudit.inspect(patchProject)
                                } label: {
                                    Label("ตรวจปลายทางจริง (อ่านอย่างเดียว)", systemImage: "magnifyingglass")
                                        .frame(maxWidth: .infinity)
                                }
                                .buttonStyle(.bordered)
                                .tint(AppTheme.accent)
                            } else {
                                Text("แพ็กเกจนี้ไม่มีข้อมูล Manifest ให้ตรวจ ตรวจการดาวน์โหลดหรือการปลดล็อกก่อน")
                                    .font(.caption).foregroundStyle(.orange)
                            }
                            Text(targetCheckResult)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .fixedSize(horizontal: false, vertical: true)
                                .textSelection(.enabled)
                            Text("แม้การอ่านผ่าน ก็ยังไม่ใช่การยืนยันสิทธิ์เขียน ต้องมีช่องทางปลายทางที่ iOS อนุญาตก่อนลงแพตช์")
                                .font(.caption2).foregroundStyle(.orange)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                        .padding(16)
                        .background(AppTheme.surfaceRaised, in: RoundedRectangle(cornerRadius: 18))
                    }

"""
s=s.replace(needle2,ui+needle2,1)
helper="""
// Target-only metadata audit. No file mutation, AFC staging, credential access,
// sandbox-escape attempt, kernel access, or write operation is performed here.
private enum PatchTargetAccessAudit {
    static func inspect(_ project: PatchProject) -> String {
        let fm = FileManager.default
        let bundles = project.allBundleIdentifiers
        guard !bundles.isEmpty else {
            return "Manifest ไม่มี Bundle ID ของแอปปลายทาง"
        }
        if bundles.count > 8 || project.rules.count > 512 {
            return "Manifest มีเป้าหมายมากเกินขอบเขตการตรวจครั้งเดียว"
        }
        var lines: [String] = ["เป้าหมาย: \\(bundles.count) แอป • \\(project.rules.count) รายการไฟล์"]
        for bundle in bundles {
            guard (try? PatchPathValidator.canonicalBundleIdentifier(bundle)) == bundle else {
                lines.append("• Bundle ID ไม่ถูกต้อง")
                continue
            }
            guard let path = ContainerStore.resolveAppContainerPath(bundleID: bundle),
                  ContainerStore.isApplicationContainerPath(path) else {
                lines.append("• \\(bundle): ไม่พบ Container ที่เข้าถึงได้")
                continue
            }
            let root = PatchPathValidator.canonicalFileURL(
                URL(fileURLWithPath: path, isDirectory: true)
            )
            do {
                _ = try fm.attributesOfItem(atPath: root.path)
            } catch {
                lines.append("• \\(bundle): พบตำแหน่ง แต่ระบบปฏิเสธอ่านข้อมูล (\\((error as NSError).code))")
                continue
            }
            let rules = project.rules.filter { $0.bundleID == bundle }
            var existing = 0
            var readable = 0
            var invalid = 0
            for rule in rules {
                guard let target = try? PatchPathValidator.resolveTargetURL(
                    bundleID: bundle, relativePath: rule.relativePath,
                    containerRoot: root
                ) else {
                    invalid += 1
                    continue
                }
                // Metadata-only check; does not open or edit target file data.
                if fm.fileExists(atPath: target.path) {
                    existing += 1
                    if fm.isReadableFile(atPath: target.path) { readable += 1 }
                }
            }
            lines.append("• \\(bundle): อ่านข้อมูล Container ได้; พบไฟล์ \\(existing)/\\(rules.count), อ่านได้ \\(readable), เส้นทางไม่ถูกต้อง \\(invalid)")
        }
        lines.append("ผลนี้ยังไม่ยืนยันว่าสามารถเขียนไฟล์เกมได้ และไม่ได้เปิดสิทธิ์ลงแพตช์")
        return lines.joined(separator: "\\n")
    }
}
"""
assert "enum PatchTargetAccessAudit" not in s
s += helper
view.write_text(s,encoding="utf8")

s=projects.read_text(encoding="utf8")
needle3="""                    readiness: deviceReadiness,
                    onApply: { setServerPatchEnabled(true, for: item) }"""
assert s.count(needle3)==1, "Server patch sheet changed"
s=s.replace(needle3,"""                    readiness: deviceReadiness,
                    patchProject: item.project,
                    onApply: { setServerPatchEnabled(true, for: item) }""",1)
projects.write_text(s,encoding="utf8")
assert "PatchTargetAccessAudit.inspect" in view.read_text()
assert "patchProject: item.project" in projects.read_text()
print("Added read-only real target preflight; patch gate unchanged.")
