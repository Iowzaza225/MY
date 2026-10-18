#!/usr/bin/env python3
"""Keep iOS 27 device-connectivity display truthful across navigation.

Reads only TEAMMOD27's reconstructed Swift source. The model is NOT a
cross-app file authorization gate: canApply remains unchanged and false
for iOS 27. Returning to the package list triggers an actual native RSD
recheck; it never promotes cached connectivity into patch permissions.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1]).resolve()
readiness=root/"ThreeOneOSFive/helpers/RuizenDeviceReadiness.swift"
projects=root/"ThreeOneOSFive/views/PatchProjectsView.swift"
assert readiness.is_file() and projects.is_file()

s=readiness.read_text(encoding="utf8")
needle="    func refresh() {\n"
assert s.count(needle)==1, "Readiness refresh() anchor moved"
method="""    // A transient connection result is only valid when actually probed. Do not
    // erase a just-completed result simply because a sheet was dismissed.
    // Every app foreground transition forces a new native check so a stopped
    // VPN cannot be mistaken for an active tunnel.
    func refreshOrRecheck(force: Bool = false) {
        guard !isChecking && !isPairing else { return }
        let baseline = Self.detect()
        guard baseline.isModernIOS, pairingFilePresent else {
            refresh()
            return
        }
        // UI navigation alone can reuse a very recent in-process result,
        // never a persisted or across-launch result.
        if !force && report.tunnel == .verified && report.rsd == .verified
            && Date().timeIntervalSince(checkedAt) < 10 {
            return
        }
        runNativeProbe()
    }

"""
s=s.replace(needle,method+needle,1)
readiness.write_text(s,encoding="utf8")

s=projects.read_text(encoding="utf8")
appearance="            .onAppear {\n                deviceReadiness.refresh()"
assert s.count(appearance)==1, "PatchProjectsView onAppear changed"
s=s.replace(appearance,"            .onAppear {\n                deviceReadiness.refreshOrRecheck()",1)
activated="                if phase == .active {\n                    deviceReadiness.refresh()"
assert s.count(activated)==1, "Scene phase refresh changed"
s=s.replace(activated,"                if phase == .active {\n                    deviceReadiness.refreshOrRecheck(force: true)",1)

anchor="""        let isActive = activeProjectIDs.contains(item.id)
        let isWorking = workingProjectIDs.contains(item.id)

        VStack(alignment: .leading, spacing: 13) {"""
assert s.count(anchor)==1, "Patch package list anchor moved"
new="""        let isActive = activeProjectIDs.contains(item.id)
        let isWorking = workingProjectIDs.contains(item.id)
        let connectionVerified = deviceReadiness.report.isModernIOS
            && deviceReadiness.report.tunnel == .verified
            && deviceReadiness.report.rsd == .verified

        VStack(alignment: .leading, spacing: 13) {"""
s=s.replace(anchor,new,1)
original="""                HTVStatusPill(
                    title: isWorking ? "กำลังทำงาน" : (isActive ? "ใช้งานอยู่" : (deviceReadiness.report.canApply ? "รอตรวจสิทธิ์" : "รอเชื่อมต่อ")),
                    systemImage: isWorking ? "clock.fill" : (isActive ? "checkmark.circle.fill" : (deviceReadiness.report.canApply ? "info.circle.fill" : "exclamationmark.triangle.fill")),
                    tint: isWorking ? .orange : (isActive ? .green : (deviceReadiness.report.canApply ? AppTheme.accent : .orange))
                )"""
assert s.count(original)==1, "Patch readiness status pill changed"
replacement="""                HTVStatusPill(
                    title: isWorking ? "กำลังทำงาน" :
                        (isActive ? "ใช้งานอยู่" :
                            (deviceReadiness.isChecking ? "กำลังตรวจ" :
                                (connectionVerified ? "RSD เชื่อมต่อ" :
                                    (deviceReadiness.report.canApply ? "รอตรวจสิทธิ์" : "รอเชื่อมต่อ")))),
                    systemImage: isWorking ? "clock.fill" :
                        (isActive ? "checkmark.circle.fill" :
                            (deviceReadiness.isChecking ? "clock.fill" :
                                (connectionVerified ? "checkmark.circle.fill" : "exclamationmark.triangle.fill"))),
                    tint: isWorking ? .orange :
                        (isActive ? .green :
                            (deviceReadiness.isChecking ? AppTheme.accent :
                                (connectionVerified ? .green : .orange)))
                )"""
s=s.replace(original,replacement,1)
label="""            if !remote.description.isEmpty {
                Text(remote.description)"""
assert s.count(label)==1, "Package description block changed"
additional="""            if connectionVerified {
                Text("Tunnel/RSD เชื่อมต่อแล้ว แต่ยังไม่ได้ยืนยันสิทธิ์เขียนไฟล์ของแอปเป้าหมาย")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

"""
s=s.replace(label,additional+label,1)
button="""                        patchActionPill(title: "เปิดใช้", systemImage: "bolt.fill", tint: AppTheme.accent)"""
assert s.count(button)==1, "Package action label changed"
s=s.replace(button,'''                        patchActionPill(
                            title: deviceReadiness.report.isModernIOS ? "ตรวจสิทธิ์" : "เปิดใช้",
                            systemImage: deviceReadiness.report.isModernIOS ? "checkmark.shield" : "bolt.fill",
                            tint: AppTheme.accent
                        )''',1)
projects.write_text(s,encoding="utf8")
assert "deviceReadiness.refreshOrRecheck()" in s
assert "deviceReadiness.refreshOrRecheck(force: true)" in s
assert "let connectionVerified =" in s
assert "var canApply: Bool { !isModernIOS && legacyEligible }" in readiness.read_text()
print("Connection presentation repaired; file patch authorization gate unchanged.")
